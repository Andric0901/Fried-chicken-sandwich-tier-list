import unittest
import os
import json
from PIL import Image


LOGOS_PATH = "logos"


class TestLogos(unittest.TestCase):
    def setUp(self):
        self.list_of_logo_names = os.listdir(LOGOS_PATH)

    def test_logo_ratio_is_one_to_one(self):
        for name in self.list_of_logo_names:
            logo_dir = LOGOS_PATH + "/" + name
            image = Image.open(logo_dir)
            width, height = image.size
            try:
                assert width == height
                image.close()
            except AssertionError:
                print(width, height, logo_dir)

    def test_logo_extension_equals_jpg(self):
        for name in self.list_of_logo_names:
            try:
                assert name.endswith(".jpg")
            except AssertionError:
                print(name)


class TestTierDictJson(unittest.TestCase):
    def setUp(self):
        self.f = open('tier_dict.json')
        self.d = dict(json.load(self.f))
        self.tiers = list(self.d.keys())

    def test_tier_dict_json_has_unique_names(self):
        try:
            for t in self.tiers:
                # Set removes duplicate elements if there exists one
                restaurant_names_list, restaurant_names_set = list(self.d[t].keys()), set(self.d[t].keys())
                assert len(restaurant_names_list) == len(restaurant_names_set)
        except AssertionError:
            print(restaurant_names_list, restaurant_names_set)
            print(len(restaurant_names_list), len(restaurant_names_set))

    # def test_tier_dict_name_matches_logo_filename(self):
    #     ...

    def tearDown(self):
        self.f.close()



if __name__ == '__main__':
    unittest.main()
