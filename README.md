# PS4 Lightbar Screen Sync

Your screen's colors, in your hands.

A small experiment that turns a PS4 DualShock 4 light bar into an ambient accent for games, movies, and anything else on your computer's screen. Pick a dominant screen color, fade into it gently, repeat.

## The idea

Warm sunsets glow orange. Underwater scenes glow blue. Dark scenes fade out. This should feel subtle and atmospheric, with restrained brightness and no flashing effects. The light bar is a single RGB light, so it represents one scene color at a time. How immersive it feels depends on controller position, room lighting, and light bar visibility; it is not room-scale lighting.

## First prototype

- Installable `ds4sync` CLI, two dependencies, no browser shell, server, accounts, or telemetry.
- Dominant color from a grid of up to 576 sampled pixels. Every pixel gets an equal vote across hue and neutral brightness groups, including black and gray. Only the winning group is averaged, keeping small bright menus from overriding a larger dark image.
- Time-based smoothing, adjustable brightness, 15 updates/second by default.
- Reasserts stable LED colors on each update, subject to SDL's write rate limit, to recover from external color overrides. Other apps can still cause brief flashes; this does not give exclusive control of the light bar.
- SDL handles controller transport; USB is the recommended first hardware test. Bluetooth still needs validation.
- Preview mode prints RGB hex colors without touching a controller.
- Captured frames stay in memory. Nothing records or uploads them.

This is an initial, unbenchmarked prototype. The color pipeline has automated tests; real controller output, Bluetooth behavior, and OS-specific capture permissions still need hardware testing. Sampling is sparse, but the current capture backend still grabs the whole selected monitor each frame. Low CPU and memory usage are goals, not measured claims.

## Install

Requires Python 3.9+ and [pipx](https://pipx.pypa.io/). On macOS, install pipx with `brew install pipx` if needed.

```sh
pipx install git+https://github.com/DhanwanthParameswar/ps4-lightbar-screen-sync.git
pipx ensurepath
```

Open a new terminal after `ensurepath`. The command works from any directory without activating a virtual environment. Python remains the implementation language; pipx manages its isolated environment.

## Run

Pair your DualShock 4 with **this computer** over Bluetooth, or connect over USB. Bluetooth still needs hardware validation; USB is a useful fallback.

```sh
ds4sync
```

Other options:

```sh
ds4sync --list
ds4sync --controller 0 --brightness 0.5 --fade-ms 220 --fps 15
ds4sync --preview
ds4sync --help
ds4sync --version
```

Update or uninstall:

```sh
pipx upgrade ps4-lightbar-screen-sync
pipx uninstall ps4-lightbar-screen-sync
```

Use `--monitor 2` for another monitor. `--help` lists all options. Ctrl+C stops the app and makes a best-effort attempt to turn the light bar off; the prior LED color is not restored. A disconnected controller requires restarting the script.

## Compatibility and limits

- **Computer use:** this reads a computer display and controls a controller connected to it. It does not run on a stock PS4 or capture a console's HDMI output. A console setup would need a capture device and separate controller-control investigation.
- **macOS:** allow Screen Recording for the terminal or host app in System Settings → Privacy & Security, then restart it if necessary.
- **Windows / Linux:** capture and controller access need testing. Linux MSS capture generally needs X11; Wayland may require a different capture backend. Device permissions can also affect controller access.
- **Other apps:** Steam Input, DS4Windows, and games may write their own LED colors and compete with Lightbar. Test with those LED controls disabled or those apps closed.
- **Protected content:** DRM video or exclusive fullscreen capture may be black or unavailable.
- **Controller discovery:** automatic selection uses SDL device names as a heuristic. Use `--list` and an explicit index if it picks the wrong controller. Only genuine DS4 hardware is the initial target; clones may behave differently.
- **Footprint:** Python and pygame are useful for proving the effect quickly. A native implementation is the next step if this needs a tiny standalone download.

## Next milestones

1. Validate on a real DS4 over USB, then Bluetooth; measure CPU, RAM, and end-to-end latency.
2. Tune sampling and fade behavior against actual games, including scene cuts and letterboxed movies.
3. Replace full-screen captures with a downsampled native capture path.
4. Package a small tray/menu-bar app with one start/stop switch and brightness control.

## Develop

Install from a checkout:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ds4sync --help
```

On Windows activate with `.venv\Scripts\activate` instead.

The color tests need only the Python standard library:

```sh
python3 -m unittest discover -s tests -v
```

## Technical references

- [SDL's PS4 HID backend](https://github.com/libsdl-org/SDL/blob/SDL2/src/joystick/hidapi/SDL_hidapi_ps4.c)
- [pygame-ce controller LED API](https://pyga.me/docs/ref/sdl2_controller.html#pygame._sdl2.controller.Controller.set_led)
- [MSS screen capture](https://python-mss.readthedocs.io/stable/)

Independent experiment, unaffiliated with Sony or PlayStation.
