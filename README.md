# The Divergence Engine

An interactive research printer by Max Park and Jude Pullen. An AI-enabled research tool which -rather than, as often can happen- returning a definitive answer or another flood of text in reply,  it offers tasty breadcrumbs, scattered clues and disparate ideas that invite people to make recipe ideas and discoveries of their own - and tempt them towards questioning how online knowledge is shaped, and how much more tasty it can become from using well-sourced ingredients, and a little bit of elbow-grease. 

## Start with the Jetson build

The core Divergence Engine build is **`diveng.py`**, tested for the Jetson Orin
Nano Super. It combines internet research with on-device Granite models for
local USB-PDF indexing, retrieval and QR-page questions.

There is also an optional, lower-cost web-assisted route for a 64-bit Raspberry
Pi 4B or Pi 5 with 8 GB RAM. It is useful when local Granite document retrieval
is not required; it is not a reduced Jetson build.

| | Jetson Orin Nano — core local-AI build | Raspberry Pi 4B / 5 — optional web-assisted build |
| --- | --- | --- |
| Start here | [`docs/setup-jetson.md`](docs/setup-jetson.md) | [`docs/setup-pi.md`](docs/setup-pi.md) |
| Run | `python3 diveng.py` | `python3 unblocker_pi.py` |
| Research and image search | Internet + Mistral/Brave | Internet + Mistral |
| USB PDF path | Local Granite indexing and retrieval | OpenNotebook, configured with your chosen provider |
| QR page | Local Granite questions across active documents and web material | Receipt page and source links |
| Local Ollama models | Required | Not required |
| Recommended computer | Jetson Orin Nano Super, 8 GB shared RAM | Pi 4B or Pi 5, 64-bit OS, 8 GB RAM |

## First run

1. Clone the repository and enter it.

   ```bash
   git clone https://github.com/Max-Park-Design/The-Divergence-Engine.git
   cd The-Divergence-Engine
   ```

2. Follow the [Jetson setup guide](docs/setup-jetson.md). Use the Pi guide only
   when you deliberately want the web-assisted alternative.

3. Run its harmless pre-flight check before connecting or mounting hardware.

   ```bash
   python3 scripts/check_setup.py --build pi
   # or
   python3 scripts/check_setup.py --build jetson
   ```

4. Launch the matching file only after the check has found your core files and
   credentials.

The controller expects the project Arduino, a serial thermal printer and the
three OLED assets. It is not a software-only demo at present.

## What is in this repository?

| Path | Purpose |
| --- | --- |
| `diveng.py` | Primary Jetson controller with local Granite USB retrieval and local QR questions |
| `unblocker_pi.py` | Optional Raspberry Pi 4B / 5 web-assisted controller; no Ollama/Granite requirement |
| `scripts/check_setup.py` | Read-only check for files, credentials and optional local services |
| `requirements-pi.txt` | Python packages for the Pi edition |
| `requirements-jetson.txt` | Python packages for the Jetson edition |
| `firmware/Unblocker/Unblocker.ino` | Arduino firmware |
| `oled_graphics/` | Animation frames for the three rotary dials |
| `docs/choose-your-build.md` | Plain-language comparison of the two builds |
| `docs/hardware.md` | Physical components and connection notes |
| `deploy/` | Systemd examples — edit the user and path before installing |

## Keep keys and documents private

Never commit a real API key or a USB PDF. `.gitignore` excludes `.env`,
`MISTRAL_API_KEY.txt`, `BRAVE_SEARCH_API_KEY.txt`, generated receipts and USB
copies. Use the supplied `*.example` files as templates only.

## Documentation

- [Choose your build](docs/choose-your-build.md)
- [Set up the Raspberry Pi edition](docs/setup-pi.md)
- [Set up the Jetson edition](docs/setup-jetson.md)
- [Hardware notes](docs/hardware.md)
- [Architecture and maintenance notes](docs/architecture.md)

## Status

This is an artist-led hardware project, not a general-purpose package. The
Jetson edition is the core installation build. The Raspberry Pi edition is an
optional web/OpenNotebook alternative for a 64-bit Pi 4B or Pi 5 with 8 GB
RAM. Test your own serial ports, printer and services before a public event.

