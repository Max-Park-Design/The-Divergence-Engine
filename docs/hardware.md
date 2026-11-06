# Hardware notes

Both editions use the same physical installation. The computer choice changes
the research and document path, not the Arduino-controlled interface.

| Component | Role | Notes |
| --- | --- | --- |
| Arduino | Reads the rotary dials, USB sliders, crank, switches and pulse input; drives LEDs and OLEDs | Upload `firmware/Unblocker/Unblocker.ino` |
| Rotary dials | Select country policy, topic policy and image distance | Their animation frames live in `oled_graphics/` |
| USB sliders | Bring inserted PDF sources into a run | Five physical slots are mapped in the controller |
| Thermal printer | Prints the receipt and QR code | Normally appears as `/dev/ttyUSB0` |
| Three OLEDs | Show the rotary-dial states | Keep the three graphics folders together |
| Jetson or Raspberry Pi 4B / 5 | Runs the Python controller | The Jetson is the core build; choose the route in [choose-your-build.md](choose-your-build.md) |

## Serial connections

By default the Python controller searches for:

```text
Arduino: /dev/ttyACM0
Printer: /dev/ttyUSB0
```

On a different setup, set `UNBLOCKER_ARDUINO_PORT` and
`UNBLOCKER_PRINTER_PORT` in the appropriate `.env` file. Confirm paths with:

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

The USB slot mapping is installation-specific. If your physical hub changes,
update `USB_PORT_MAP` in the build file and test insertion/removal before an
event.

## Before an event

1. Run the pre-flight check for the chosen build.
2. Test the Arduino and printer manually.
3. Insert one PDF per USB drive and verify the slot mapping.
4. Test the QR page from another device on the same network.
5. Keep API keys and USB content out of Git.

