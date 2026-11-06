# Set up the Jetson edition

This is the full local-document build, tested on a Jetson Orin Nano Super with
8 GB shared RAM. It uses local Granite models through Ollama to index USB PDFs,
retrieve passages and answer QR-page questions locally.

It also uses Mistral and Brave for normal web research, plus OpenNotebook for
the existing source workflow.

## You need

- Jetson Orin Nano Super with the project Arduino and serial thermal printer.
- Ollama running and reachable from the controller.
- A Granite chat model and `granite-embedding:30m` in Ollama.
- An OpenNotebook instance on port `5055`.
- Mistral and Brave Search API keys.

## 1. Get the code and packages

```bash
git clone https://github.com/Max-Park-Design/The-Divergence-Engine.git
cd The-Divergence-Engine
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-jetson.txt
```

If you already have a working Jetson environment, preserve its installed
versions rather than upgrading it only to match this repository.

## 2. Configure local models

The installation uses these model names by default:

```text
granite-engine:latest
granite-embedding:30m
```

`granite-engine:latest` is an installation-specific name. The repository does
not contain model weights. You may point the script at another compatible
Ollama chat model by copying `.env.jetson.example` to `.env` and setting:

```bash
UNBLOCKER_OLLAMA_API=http://YOUR_OLLAMA_HOST:11434
UNBLOCKER_CHAT_MODEL=YOUR_CHAT_MODEL
UNBLOCKER_EMBED_MODEL=granite-embedding:30m
```

Load `.env` before launching if you use overrides:

```bash
set -a
. ./.env
set +a
```

## 3. Add web-service keys

Create these two files beside `unblocker_jetson.py` using the provided example
files as a guide:

```text
MISTRAL_API_KEY.txt
BRAVE_SEARCH_API_KEY.txt
```

Each file must contain one key only. Both are ignored by Git. Do not add them
to a commit, screenshot or QR page.

## 4. Start OpenNotebook

Start the existing OpenNotebook setup and create an empty notebook. The script
expects its API at `http://localhost:5055`; use the same connection arrangement
as the installation if Ollama lives outside its Docker container.

## 5. Check and run

```bash
python3 scripts/check_setup.py --build jetson
python3 unblocker_jetson.py
```

The check does not send a research request or print anything. It only verifies
the local files, keys and reachable services.

## Run automatically on boot

Copy [`deploy/unblocker-jetson.service`](../deploy/unblocker-jetson.service)
to `/etc/systemd/system/`, replace every `YOUR_USER` placeholder, then enable
it after the manual launch works:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now unblocker-jetson.service
sudo systemctl status unblocker-jetson.service --no-pager
```

