import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from lightbar import controller_names, main


class ControllerTests(unittest.TestCase):
    def test_discovery_without_module_name_forindex(self):
        pad = SimpleNamespace(name='PS4 Controller', quit=Mock())
        api = SimpleNamespace(
            get_count=lambda: 2,
            is_controller=lambda index: index == 1,
            Controller=Mock(return_value=pad),
        )
        self.assertEqual(controller_names(api), {1: 'PS4 Controller'})
        api.Controller.assert_called_once_with(1)
        pad.quit.assert_called_once_with()

    def test_no_controllers(self):
        api = SimpleNamespace(get_count=lambda: 0)
        self.assertEqual(controller_names(api), {})

    def test_stable_scene_restores_externally_overwritten_led(self):
        state = {'led': None, 'frames': 0}

        def set_led(rgb):
            state['led'] = rgb
            return True

        pad = SimpleNamespace(name='PS4 Controller', quit=Mock(),
                              attached=lambda: True, set_led=set_led)
        controller = SimpleNamespace(init=Mock(), get_count=lambda: 1,
                                     is_controller=lambda index: True,
                                     Controller=lambda index: pad)
        pygame = SimpleNamespace(display=SimpleNamespace(init=Mock()),
                                 event=SimpleNamespace(pump=Mock(), clear=Mock()),
                                 quit=Mock())
        capture = Mock()
        capture.__enter__ = Mock(return_value=capture)
        capture.__exit__ = Mock(return_value=False)
        capture.monitors = [{}, {}]
        capture.grab.return_value = SimpleNamespace(bgra=bytes((0, 0, 255, 255)), width=1, height=1)

        def between_frames(seconds):
            self.assertEqual(state['led'], (255, 0, 0))
            state['frames'] += 1
            if state['frames'] == 2:
                raise KeyboardInterrupt
            # Simulate another app resetting the LED while the screen stays red.
            state['led'] = (0, 0, 255)

        modules = {'pygame': pygame, 'pygame._sdl2': SimpleNamespace(controller=controller),
                   'mss': SimpleNamespace(mss=lambda: capture)}
        with patch.dict('sys.modules', modules), patch('lightbar.time.sleep', side_effect=between_frames):
            self.assertEqual(main(['--brightness', '1', '--fade-ms', '0']), 0)
        self.assertEqual(state['frames'], 2)
