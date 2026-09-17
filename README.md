# The Divergence Engine

An interactive installation by Max Park and Jude Pullen. Physical controls steer
country selection, topic selection, source policy and the conceptual distance
between a researched sentence and its accompanying image. The Jetson coordinates
the hardware, research services, receipt printer and local web archive.

## Repository layout

| Path | Purpose |
| --- | --- |
| `unblocker.py` | Runtime controller, hardware state and research pipeline |
| `demo_store.py` | Recorded-output validation, selection and archiving |
| `add_demo.py` | Import a saved result into the local demo library |
| `firmware/Unblocker/Unblocker.ino` | Arduino firmware |
| `oled_graphics/` | Runtime animation frames: softpower, overton and delta |
| `soft_power_index.csv` | Country-selection data |
| `hrcalc.py`, `max30102.py` | Existing pulse-sensor support modules |
| `deploy/unblocker.service` | Systemd service example |
| `docs/architecture.md` | Runtime organisation and maintenance notes |

## Runtime

The installation uses Linux, Python, an Arduino serial connection, a serial
thermal printer and a local OpenNotebook API at `http://localhost:5055`.
Mistral and source/image retrieval require internet access.

Use the Python environment already configured on the Jetson. The dependency
inventory is in `requirements.txt`; it is not a tested installation lockfile.
Do not upgrade packages on the working installation merely to publish this repo.

Set `MISTRAL_API_KEY` in the process environment. For systemd, place the value in
`/home/george/Unblocker/.env`, readable only by its owner, and use the supplied
service example's `EnvironmentFile` setting. `.env` is excluded from Git.
Python does not load this file automatically.

For a manual launch from the project directory:

```bash
set -a
. ./.env
set +a
python3 unblocker.py
```

The service example retains the installation path `/home/george/Unblocker`.
Review that path before using it on another machine. Preparing a source checkout
does not install or restart the service.

## Local files

Recorded demos, inserted USB documents, state and generated outputs are local
data and are not distributed here. Demo functionality is included. Import your
own saved outputs with `python3 add_demo.py --help` and validate them with
`python3 demo_store.py demos`. Demo replay requires a valid local demo library.

Run the controller from its project directory. Some paths are relative to that
directory and others to the source file. Keep `oled_graphics/`,
`soft_power_index.csv` and the Python runtime files in their documented locations.

QR source pages are served by the Jetson; their accessibility depends on the
server and network remaining available.
