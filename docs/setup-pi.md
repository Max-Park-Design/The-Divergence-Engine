# Set up the Raspberry Pi edition

This is the lower-cost, web-assisted build. It is designed for a **64-bit
Raspberry Pi 5**. Use 8 GB RAM where possible; 4 GB may work with a light
OpenNotebook configuration, but it is not the recommended event setup.

It runs the Arduino, OLEDs, USB monitor, thermal printer, QR page and cloud
research. It does not install or use local Granite models.

## You need

- Raspberry Pi 5, 64-bit Raspberry Pi OS, wired power supply and internet.
- The project Arduino, its uploaded firmware and the physical controls.
- A serial thermal printer.
- A Mistral API key.
- Docker and an OpenNotebook instance running locally on port `5055`.

OpenNotebook provides the source store used by this build. Its official image
is available for Linux ARM64. Follow the [OpenNotebook Docker setup]
(https://www.open-notebook.ai/get-started), configure a cloud provider in its
UI and create one empty notebook before launching the controller.

## 1. Get the code and Python packages

```bash
git clone https://github.com/Max-Park-Design/The-Divergence-Engine.git
cd The-Divergence-Engine
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-pi.txt
```

## 2. Add your Mistral key

```bash
cp .env.pi.example .env
nano .env
```

Replace `replace_with_your_key` with your key. The `.env` file is private and
must never be committed. Load it into the current shell just before running:

```bash
set -a
. ./.env
set +a
```

## 3. Start OpenNotebook

Start your OpenNotebook Docker setup and visit its UI. Create a notebook, then
check that its API is reachable at `http://localhost:5055`. If it runs on a
different machine or port, add this line to `.env`:

```bash
UNBLOCKER_OPEN_NOTEBOOK_API=http://YOUR_HOST:5055
```

## 4. Check before first launch

```bash
python3 scripts/check_setup.py --build pi
```

`CHECK` beside a serial port or a local service is normal if that item is not
connected yet. A missing key or project file must be fixed first.

## 5. Run it

```bash
python3 unblocker_pi.py
```

The script will report the detected Arduino and printer paths. If yours differ,
put the correct values in `.env` before loading it:

```bash
UNBLOCKER_ARDUINO_PORT=/dev/ttyACM0
UNBLOCKER_PRINTER_PORT=/dev/ttyUSB0
```

Use `ls /dev/ttyACM* /dev/ttyUSB*` after connecting hardware to discover the
available paths.

## Run automatically on boot

Copy [`deploy/unblocker-pi.service`](../deploy/unblocker-pi.service) to
`/etc/systemd/system/`, replace every `YOUR_USER` placeholder, then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now unblocker-pi.service
sudo systemctl status unblocker-pi.service --no-pager
```

Do not install the service until the manual launch works.

