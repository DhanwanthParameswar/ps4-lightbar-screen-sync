"""Screen color → DualShock 4 light bar. Run with --help for options."""

import argparse
import colorsys
import math
import os
import sys
import time


def screen_color(bgra, width, height, brightness=0.65):
    """Sample a 32×18 grid; select a dominant hue instead of averaging to gray."""
    bins = [[0, 0, 0, 0] for _ in range(12)]
    total = [0, 0, 0]
    count = 0
    for gy in range(min(18, height)):
        y = min(height - 1, int((gy + 0.5) * height / min(18, height)))
        for gx in range(min(32, width)):
            x = min(width - 1, int((gx + 0.5) * width / min(32, width)))
            offset = (y * width + x) * 4
            b, g, r = bgra[offset:offset + 3]
            hue, saturation, value = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            # Ignore letterbox bars while retaining a truly black scene as black.
            if value < 0.04:
                continue
            count += 1
            for i, channel in enumerate((r, g, b)):
                total[i] += channel
            if saturation > 0.2:
                bucket = bins[min(11, int(hue * 12))]
                weight = saturation * value
                bucket[0] += weight
                for i, channel in enumerate((r, g, b), 1):
                    bucket[i] += channel * weight
    if not count:
        return (0, 0, 0)
    dominant = max(bins, key=lambda bucket: bucket[0])
    if dominant[0] >= count * 0.1:
        rgb = [channel / dominant[0] for channel in dominant[1:]]
    else:
        rgb = [channel / count for channel in total]
    return tuple(round(channel * brightness) for channel in rgb)


def fade(previous, target, elapsed, fade_ms):
    """Time-based smoothing behaves consistently at different frame rates."""
    amount = 1 if fade_ms == 0 else 1 - math.exp(-elapsed * 1000 / fade_ms)
    return tuple(a + (b - a) * amount for a, b in zip(previous, target))


def options(argv=None):
    parser = argparse.ArgumentParser(prog='ds4sync', description=__doc__)
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.1')
    parser.add_argument('--preview', action='store_true', help='print colors without opening a controller')
    parser.add_argument('--list', action='store_true', help='list controller indexes and exit')
    parser.add_argument('--controller', type=int, help='explicit SDL controller index; defaults to a PS4 controller')
    parser.add_argument('--monitor', type=int, default=1, help='MSS monitor index (default: 1)')
    parser.add_argument('--fps', type=int, default=15, help='updates per second, 1–60 (default: 15)')
    parser.add_argument('--brightness', type=float, default=0.65, help='brightness, 0–1 (default: 0.65)')
    parser.add_argument('--fade-ms', type=float, default=180, help='fade time constant, 0–2000 (default: 180)')
    args = parser.parse_args(argv)
    if not 1 <= args.fps <= 60:
        parser.error('--fps must be between 1 and 60')
    if not 0 <= args.brightness <= 1:
        parser.error('--brightness must be between 0 and 1')
    if not 0 <= args.fade_ms <= 2000:
        parser.error('--fade-ms must be between 0 and 2000')
    return args


def controller_names(controller):
    """Read names from opened devices, including pygame-ce before 2.5.9."""
    names = {}
    for index in range(controller.get_count()):
        if not controller.is_controller(index):
            continue
        device = controller.Controller(index)
        try:
            names[index] = device.name or ''
        finally:
            device.quit()
    return names


def main(argv=None):
    args = options(argv)
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
    os.environ.setdefault('SDL_JOYSTICK_HIDAPI_PS4', '1')
    os.environ.setdefault('SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS', '1')
    pygame = None
    pad = None
    try:
        if not args.preview or args.list:
            import pygame
            from pygame._sdl2 import controller

            pygame.display.init()
            controller.init()
            available = controller_names(controller)
            if args.list:
                for i in available:
                    print(f'{i}: {available[i]}')
                if not available:
                    print('No SDL controllers found. Connect a DualShock 4 and try again.')
                return 0
            index = args.controller
            if index is None:
                index = next((i for i in available if any(
                    name in available[i].lower()
                    for name in ('ps4', 'dualshock', 'dual shock', 'wireless controller')
                )), None)
            if index not in available:
                raise RuntimeError('No PS4 controller selected. Connect it, then use --list or --controller INDEX.')
            pad = controller.Controller(index)
            if not pad.set_led((0, 0, 0)):
                raise RuntimeError('SDL could not control this light bar. Try USB and close other LED-control apps.')
        import mss

        with mss.mss() as capture:
            if not 1 <= args.monitor < len(capture.monitors):
                raise RuntimeError(f'Choose --monitor between 1 and {len(capture.monitors) - 1}.')
            region = capture.monitors[args.monitor]
            current = (0.0, 0.0, 0.0)
            last_sent = None
            last = time.monotonic()
            print('Lightbar running. Ctrl+C to stop. Screen frames stay in memory.')
            while True:
                started = time.monotonic()
                if pygame:
                    pygame.event.pump()
                    pygame.event.clear()
                    if not pad.attached():
                        raise RuntimeError('Controller disconnected. Reconnect it and restart Lightbar.')
                frame = capture.grab(region)
                target = screen_color(frame.bgra, frame.width, frame.height, args.brightness)
                now = time.monotonic()
                current = fade(current, target, now - last, args.fade_ms)
                last = now
                rgb = tuple(round(channel) for channel in current)
                if rgb != last_sent:
                    if pad and not pad.set_led(rgb):
                        raise RuntimeError('Light bar update failed. Try reconnecting the controller over USB.')
                    if args.preview:
                        print('#%02x%02x%02x' % rgb, flush=True)
                    last_sent = rgb
                time.sleep(max(0, 1 / args.fps - (time.monotonic() - started)))
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(f'Lightbar: {error}', file=sys.stderr)
        return 1
    finally:
        if pad:
            try:
                pad.set_led((0, 0, 0))
                pad.quit()
            except Exception:
                pass
        if pygame:
            pygame.quit()


if __name__ == '__main__':
    sys.exit(main())
