import unittest
import colorsys
import contextlib
import io

from lightbar import fade, screen_color, options


def pixels(*colors):
    return bytes(channel for r, g, b in colors for channel in (b, g, r, 255))


class ColorTests(unittest.TestCase):
    def test_black_scene_turns_off(self):
        self.assertEqual(screen_color(pixels((0, 0, 0)), 1, 1), (0, 0, 0))

    def test_red_majority_with_black_letterbox_stays_red(self):
        data = pixels((0, 0, 0), (255, 0, 0), (255, 0, 0))
        self.assertEqual(screen_color(data, 3, 1, 1), (255, 0, 0))

    def test_small_white_element_on_black_does_not_produce_full_white(self):
        data = pixels(*([(0, 0, 0)] * 31 + [(255, 255, 255)]))
        self.assertEqual(screen_color(data, 32, 1, 1), (0, 0, 0))

    def test_black_majority_beats_small_colored_element(self):
        data = pixels(*([(0, 0, 0)] * 31 + [(255, 0, 0)]))
        self.assertEqual(screen_color(data, 32, 1, 1), (0, 0, 0))

    def test_gray_majority_beats_bright_white_and_colored_ui(self):
        data = pixels(*([(64, 64, 64)] * 24 + [(255, 255, 255)] * 4 + [(255, 0, 0)] * 4))
        self.assertEqual(screen_color(data, 32, 1, 1), (64, 64, 64))

    def test_white_majority_is_still_white(self):
        data = pixels(*([(255, 255, 255)] * 24 + [(0, 0, 0)] * 8))
        self.assertEqual(screen_color(data, 32, 1, 1), (255, 255, 255))

    def test_dim_color_majority_beats_small_bright_color(self):
        data = pixels(*([(80, 0, 0)] * 24 + [(0, 255, 0)] * 8))
        self.assertEqual(screen_color(data, 32, 1, 1), (80, 0, 0))

    def test_near_black_scene_turns_off(self):
        self.assertEqual(screen_color(pixels((5, 5, 5)), 1, 1, 1), (0, 0, 0))

    def test_dominant_hue_does_not_average_complementary_colors(self):
        data = pixels((255, 0, 0), (255, 0, 0), (0, 255, 255))
        self.assertEqual(screen_color(data, 3, 1, 1), (255, 0, 0))

    def test_neutral_scene_and_brightness(self):
        self.assertEqual(screen_color(pixels((200, 200, 200)), 1, 1, 0.5), (100, 100, 100))

    def test_saturation_boost_keeps_hue_and_value(self):
        result = screen_color(pixels((200, 100, 100)), 1, 1, 1, 1.2)
        self.assertEqual(result, (200, 80, 80))
        hue, saturation, value = colorsys.rgb_to_hsv(*result)
        self.assertEqual((hue, value), (0, 200))
        self.assertAlmostEqual(saturation, 0.6)

    def test_saturation_zero_desaturates_and_boost_clamps(self):
        data = pixels((200, 100, 100))
        self.assertEqual(screen_color(data, 1, 1, 1, 0), (200, 200, 200))
        self.assertEqual(screen_color(data, 1, 1, 1, 3), (200, 0, 0))

    def test_saturation_preserves_black_and_neutral_grays(self):
        for color in ((0, 0, 0), (64, 64, 64), (255, 255, 255)):
            with self.subTest(color=color):
                self.assertEqual(screen_color(pixels(color), 1, 1, 1, 3), color)

    def test_boost_does_not_change_dominant_group(self):
        data = pixels(*([(64, 64, 64)] * 24 + [(200, 100, 100)] * 8))
        self.assertEqual(screen_color(data, 32, 1, 1, 3), (64, 64, 64))

    def test_saturation_cli_validation(self):
        self.assertEqual(options([]).saturation, 1.2)
        self.assertEqual(options(['--saturation', '1.2']).saturation, 1.2)
        for value in ('-1', '3.1', 'nan', 'inf'):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    options(['--saturation', value])
                self.assertEqual(error.exception.code, 2)

    def test_fade_independent_of_frame_rate(self):
        target = (255, 80, 20)
        whole = fade((0, 0, 0), target, 0.1, 180)
        half = fade((0, 0, 0), target, 0.05, 180)
        split = fade(half, target, 0.05, 180)
        for a, b in zip(whole, split):
            self.assertAlmostEqual(a, b)

    def test_zero_fade_applies_immediately(self):
        self.assertEqual(fade((0, 0, 0), (10, 20, 30), 0.01, 0), (10, 20, 30))


if __name__ == '__main__':
    unittest.main()
