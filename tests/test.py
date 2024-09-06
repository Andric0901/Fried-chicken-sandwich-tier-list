import unittest
import os
from PIL import Image


LOGOS_PATH = "logos"


class TestLogosRatio(unittest.TestCase):
    def test_logo_ratio_one_to_one(self):
        list_of_logo_names = os.listdir(LOGOS_PATH)
        for name in list_of_logo_names:
            logo_dir = LOGOS_PATH + "/" + name
            image = Image.open(logo_dir)
            width, height = image.size
            try:
                assert width == height
                image.close()
            except AssertionError:
                print(width, height, logo_dir)


class TestLogosExtension(unittest.TestCase):
    def test_logo_extension_equals_jpg(self):
        list_of_logo_names = os.listdir(LOGOS_PATH)
        for name in list_of_logo_names:
            try:
                assert name.endswith(".jpg")
            except AssertionError:
                print(name)


if __name__ == '__main__':
    unittest.main()
