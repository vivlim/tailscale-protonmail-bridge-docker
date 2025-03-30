# tailscale-protonmail-bridge-docker

## what is this?

this is a combination of:
- [protonmail-bridge-docker](https://github.com/shenxn/protonmail-bridge-docker), a docker container for running [protonmail bridge](https://proton.me/mail/bridge) headlessly in a container
- [tailscale container](https://hub.docker.com/r/tailscale/tailscale), a docker container for running tailscale in a docker container

the combination of these allows you to expose protonmail bridge to devices on your tailnet from a specific hostname, available via [tailscale's magicdns](https://tailscale.com/kb/1081/magicdns). the hostname is configured in docker-compose.yaml

### why would you want to use this?

unless you run protonmail bridge, the only email clients that you can use with protonmail are their official ones. that makes staying on top of multiple email accounts on different providers a pain.

also, setting up protonmail bridge on multiple machines is annoying and uses resources on those machines, i'd rather centralize that. (it's especially resource-intensive on an arm64 windows device. no thanks)

## do.py
this repo is also an exploration into using a python script to ease common actions (e.g. `sudo docker-compose up -d` & `sudo docker-compose down -d`). it uses the [uv python package manager](https://github.com/astral-sh/uv) to download [dependencies declared in its metadata](https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies), you must have that installed to use `do.py`.

