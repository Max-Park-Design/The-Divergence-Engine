# Choose your build

## Raspberry Pi 5 — web-assisted edition

Choose this if cost matters most and the installation will have a reliable
internet connection. It runs the physical controller, receipt printer, QR page,
Mistral research and OpenNotebook source flow. It does **not** need Ollama or
the Granite models.

- Target: 64-bit Raspberry Pi 5; 8 GB RAM recommended.
- Entry point: `unblocker_pi.py`.
- Models: Mistral and the provider configured in OpenNotebook.
- USB documents: handled through OpenNotebook.
- Best for: demonstrations with public web research and a lower hardware cost.

## Jetson Orin Nano — local-AI edition

Choose this if the installation needs on-device Granite retrieval for USB PDFs
and local questions on the QR page. It keeps the full web-research route too.

- Target: Jetson Orin Nano Super, 8 GB shared RAM.
- Entry point: `unblocker_jetson.py`.
- Models: Ollama with a Granite chat model and `granite-embedding:30m`.
- USB documents: indexed locally; active material can be retrieved locally for
  the QR page.
- Best for: local-document experiments and installations where that local path
  is a core part of the work.

## Comparison

| Capability | Pi 5 web-assisted | Jetson local-AI |
| --- | --- | --- |
| Arduino, OLEDs, dials and crank | Yes | Yes |
| Thermal printer and QR receipt | Yes | Yes |
| Mistral web research | Yes | Yes |
| Wikimedia image route | Yes | Yes |
| OpenNotebook source store | Yes | Yes |
| Ollama | No | Yes |
| Granite embedding and retrieval | No | Yes |
| Questions over active USB PDFs | Not in the current Pi build | Local Granite retrieval |
| Normal web run without internet | No | No |

## Important distinction

The Jetson's local model path is a feature, not a prerequisite for the whole
installation. A Pi is a valid, lower-cost build when cloud-assisted research is
appropriate. A Pi is not currently a supported replacement for the Jetson's
local Granite performance.

Next: [set up the Pi](setup-pi.md) or [set up the Jetson](setup-jetson.md).

