#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "gitpython",
#   "python-dotenv",
#   "getch",
# ]
# ///

# https://treyhunner.com/2024/12/lazy-self-installing-python-scripts-with-uv/

import subprocess,argparse,pathlib,git,logging
self_script = pathlib.Path(__file__)
self_script_name = self_script.stem

logger = logging.getLogger(self_script_name)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)

parser = argparse.ArgumentParser(
        prog=self_script_name,
        description="build it")

parser.add_argument('action', choices=['build', 'ps', 'up', 'down', 'logs', 'shell-ts', 'shell-bridge', 'readkey'], default='ps')
log_level_names_mapping = logging.getLevelNamesMapping()
# lowercase map
log_level_names_mapping = {k.lower():v for (k,v) in log_level_names_mapping.items()}

parser.add_argument('--log', choices=log_level_names_mapping.keys(), default='info', required=False)
args = parser.parse_args()

if 'log' in args:
    logger.setLevel(log_level_names_mapping[args.log])

def sudo_run(cmd: list[str]):
    logger.debug('Running command: %s', cmd)
    import subprocess
    args = ['sudo', '-S'] + cmd
    subprocess.run(args)

def ensure_submodules():
    # create repo at this scope so that the subprocess exits without throwing when the script exits
    repo = git.Repo(self_script.parent)
    for sm in repo.submodules:
        sm.update(recursive=True, init=True)

def ensure_dotenv_config():
    import dotenv
    config_spec = {
        'ts.env': {
            'TS_AUTHKEY': {
                'description': 'Provide a Tailscale oauth key\n - get from https://login.tailscale.com/admin/settings/oauth\n - Select "Auth Keys: Write"\n - Set a tag\nCopy the client secret and paste here\n(If you want the machine to persist on ts, append &ephemeral=false to the secret)',
                'password': True
            }
        }
    }
    for dotenv_filename in config_spec:
        need_config = config_spec[dotenv_filename]
        dotenv_path = self_script.parent / dotenv_filename
        logger.debug('checking %s at %s', dotenv_filename, dotenv_path)

        def get_set_keys():
            k = []
            if dotenv_path.exists():
                have_map = dotenv.dotenv_values(dotenv_path)
                for key in have_map:
                    logger.debug('dotenv %s contains required key %s', dotenv_path, key)
                    k.append(key)
            return k

        have_keys = get_set_keys()
        missing_keys = [x for x in need_config.keys() if x not in have_keys]
        logger.debug('missing keys: %s', missing_keys)

        if len(missing_keys) == 0:
            return

        for key in missing_keys:
            password = False
            prompt = f'[{dotenv_filename}] Need a value for {key}: '
            if 'description' in need_config[key]:
                prompt = f'[{dotenv_filename}] Need a value for {key}\n{need_config[key]["description"]}\n: '
            if 'password' in need_config[key]:
                password = need_config[key]['password']

            provided_value = None
            if password:
                from getpass import getpass
                provided_value = getpass(prompt)
            else:
                provided_value = input(prompt)

            if not provided_value or provided_value == '':
                raise Exception(f'Required env var {key} not provided')
            dotenv.set_key(dotenv_path=dotenv_path, key_to_set=key, value_to_set=provided_value)

        # check a second time
        have_keys = get_set_keys()
        missing_keys = [x for x in need_config.keys() if x not in have_keys]
        logger.debug('missing keys: %s', missing_keys)
        if len(missing_keys) > 0:
            raise Exception(f'Still missing some keys from {dotenv_path} after interactively prompting: {missing_keys}')


logger.debug('Parsed args: %s', args)

if args.action == 'build':
    ensure_submodules()
    sudo_run(['docker-compose', 'build'])
    ensure_dotenv_config()

if args.action == 'ps':
    sudo_run(['docker-compose', 'ps'])

if args.action == 'up':
    ensure_dotenv_config()
    sudo_run(['docker-compose', 'up', '-d'])
    sudo_run(['docker-compose', 'ps'])

if args.action == 'down':
    sudo_run(['docker-compose', 'down'])

if args.action == 'logs':
    sudo_run(['docker-compose', 'logs'])

if args.action == 'shell-ts':
    sudo_run(['docker-compose', 'exec' ''])

if args.action == 'readkey':
    from getch import getche
    prompt_txt = 'u: up, d: down, p: ps, t: logs(ts), b: logs (bridge), B: interactive init bridge, j: journal, V: root shell in volume, q: quit'
    print(prompt_txt)
    k = getche()
    while True:
        if k == 'u':
            sudo_run(['docker-compose', 'up', '-d'])
        elif k == 'd':
            sudo_run(['docker-compose', 'down'])
        elif k == 'p':
            sudo_run(['docker-compose', 'ps'])
        elif k == 't':
            sudo_run(['docker-compose', 'logs', 'ts-pbridge'])
        elif k == 'b':
            sudo_run(['docker-compose', 'logs', 'pbridge'])
        elif k == 'B':
            print('launching protonmail bridge interactive shell.')
            print('docs: https://proton.me/support/bridge-cli-guide')
            print('on first run, type `login` command.')
            print('`info` command will show username & password used for clients')
            input('press enter to continue')
            sudo_run(['docker-compose', 'run', 'pbridge', 'init'])
        elif k == 'j':
            sudo_run(['journalctl', '-e'])
        elif k == 'V':
            sudo_run(['bash', '-c', 'cd /var/lib/docker/volumes/ts-proton-bridge_ts-pbridge-data/_data;$SHELL'])
        elif k == 'q':
            break
        else:
            pass
        print(prompt_txt)
        k = getche()

