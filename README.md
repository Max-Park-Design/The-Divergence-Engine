# The Divergence Engine

An interactive research printer by Max Park and Jude Pullen. Its dials steer a
country, a subject and the distance between a researched fact and its image.
An Arduino reads the controls; Python gathers material, prints a receipt and
creates a QR page for further reading.

## Choose your build

**You do not need a Jetson to build The Divergence Engine.** A Raspberry Pi 5
can run the physical, web-connected edition at a much lower cost. Choose the
Jetson only when you need local Granite models for USB-document retrieval and
local QR-page questions.

| | Raspberry Pi 5 — web-assisted | Jetson Orin Nano — local-AI |
| --- | --- | --- |
| Start here | [`docs/setup-pi.md`](docs/setup-pi.md) | [`docs/setup-jetson.md`](docs/setup-jetson.md) |
| Run | `python3 unblocker_pi.py` | `python3 unblocker_jetson.py` |
| Research and image search | Internet + Mistral | Internet + Mistral/Brave |
| USB PDF path | OpenNotebook, configured with your chosen provider | Local Granite indexing and retrieval |
| QR page | Receipt page and source links | Local Granite questions across active documents and web material |
| Local Ollama models | Not required | Required |
| Recommended computer | Pi 5, 64-bit OS, 8 GB RAM | Jetson Orin Nano Super, 8 GB shared RAM |

The Pi route is not a slower Jetson route: it is deliberately web-assisted. It
does not provide the Jetson edition's fast local Granite document workflow.
Both builds still need an internet connection for normal web research and image
retrieval.

## First run

1. Clone the repository and enter it.

   ```bash
   git clone https://github.com/Max-Park-Design/The-Divergence-Engine.git
   cd The-Divergence-Engine
   ```

2. Choose **one** build above and follow its setup guide from start to finish.

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
| `unblocker_pi.py` | Raspberry Pi 5, web-assisted controller; no Ollama/Granite requirement |
| `unblocker_jetson.py` | Jetson controller with local Granite USB retrieval and local QR questions |
| `unblocker.py` | Preserved original controller; kept for reference and existing installations |
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
Jetson edition is the installation build. The Raspberry Pi edition uses the
preserved web/OpenNotebook path and is intended for a 64-bit Raspberry Pi 5;
test your own serial ports, printer and OpenNotebook configuration before a
public event.

