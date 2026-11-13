import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from lightbar import controller_names


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
