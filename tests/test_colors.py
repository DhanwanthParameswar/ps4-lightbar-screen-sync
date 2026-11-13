import unittest

from lightbar import fade, screen_color


def pixels(*colors):
    return bytes(channel for r, g, b in colors for channel in (b, g, r, 255))


class ColorTests(unittest.TestCase):
    def test_black_scene_turns_off(self):
        self.assertEqual(screen_color(pixels((0, 0, 0)), 1, 1), (0, 0, 0))

    def test_letterbox_does_not_dilute_red(self):
        self.assertEqual(screen_color(pixels((0, 0, 0), (255, 0, 0)), 2, 1, 1), (255, 0, 0))

    def test_small_white_element_on_black_does_not_produce_full_white(self):
        data = pixels(*([(0, 0, 0)] * 31 + [(255, 255, 255)]))
        self.assertEqual(screen_color(data, 32, 1, 1), (16, 16, 16))

    def test_small_color_on_black_is_dimmed_without_changing_hue(self):
        data = pixels(*([(0, 0, 0)] * 31 + [(255, 0, 0)]))
        self.assertEqual(screen_color(data, 32, 1, 1), (16, 0, 0))

    def test_near_black_scene_turns_off(self):
        self.assertEqual(screen_color(pixels((5, 5, 5)), 1, 1, 1), (0, 0, 0))

    def test_dominant_hue_does_not_average_complementary_colors(self):
        data = pixels((255, 0, 0), (255, 0, 0), (0, 255, 255))
        self.assertEqual(screen_color(data, 3, 1, 1), (255, 0, 0))

    def test_neutral_scene_and_brightness(self):
        self.assertEqual(screen_color(pixels((200, 200, 200)), 1, 1, 0.5), (100, 100, 100))

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
