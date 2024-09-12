"""

Unit test suite for tier list maker program.

Make sure PYTHONPATH is configured correctly with root directory:

$ pwd
$ export PYTHONPATH="${PYTHONPATH}:/root/path"
^ Copy path from pwd command

"""

import json
import os
import unittest
import time

from PIL import Image

from helper import RESTAURANT_NAMES
from tierlist import make_tierlist

LOGOS_PATH = "logos"


class TestMakeTierList(unittest.TestCase):
    def test_make_tierlist_performance(self):
        cutoff = 3
        start = time.time()
        make_tierlist()
        end = time.time()
        if end - start > cutoff:
            self.fail(f"Failed the performance test with cutoff {cutoff} seconds")

    def test_make_tierlist_raises_exception(self):
        try:
            make_tierlist(with_year_tag=True, with_year_first_visited_tag=True)
            self.fail("The function make_tierlist with both boolean set to True should raise ValueError")
        except ValueError:
            pass

    def test_make_tierlist_consistency(self):
        try:
            # All invocations of make_tierlist with same (unchanged) tier_dict.json file should
            # create exactly same Image objects
            t1, t2 = make_tierlist(), make_tierlist()
            assert t1 == t2
            # TODO: uncomment after optimizing make_tierlist
            # t1, t2 = make_tierlist(with_year_tag=True), make_tierlist(with_year_tag=True)
            # assert t1 == t2
            # t1, t2 = make_tierlist(with_year_first_visited_tag=True), make_tierlist(with_year_first_visited_tag=True)
            # assert t1 == t2
        except AssertionError:
            print(t1)
            print(t2)
            self.fail('All invocations of make_tierlist with unchanged tier_dict.json should not change resulting tier list')


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
                self.fail()

    def test_logo_extension_equals_jpg(self):
        for name in self.list_of_logo_names:
            try:
                assert name.endswith(".jpg")
            except AssertionError:
                print(name)
                self.fail()


class TestTierDictJson(unittest.TestCase):
    def setUp(self):
        self.f = open('tier_dict.json')
        self.d = dict(json.load(self.f))
        self.tiers = list(self.d.keys())
        self.restaurant_names = RESTAURANT_NAMES

    def test_tier_dict_json_has_unique_names(self):
        try:
            # Set removes duplicate elements if there exists one
            restaurant_names_set = set(self.restaurant_names)
            assert len(self.restaurant_names) == len(restaurant_names_set)
        except AssertionError:
            print(self.restaurant_names, restaurant_names_set)
            print(len(self.restaurant_names), len(restaurant_names_set))
            self.fail()

    def test_tier_dict_name_matches_logo_filename(self):
        try:
            for t in self.tiers:
                tier_restaurant_names = list(self.d[t].keys())
                for name in tier_restaurant_names:
                    assert self.d[t][name]["path_to_logo_image"] == f"{LOGOS_PATH}/{name}.jpg"
        except AssertionError:
            print(self.d[t][name]["path_to_logo_image"])
            print(f"{LOGOS_PATH}/{name}.jpg")
            self.fail()

    def test_year_first_visited_not_greater_than_year_reassessed(self):
        try:
            for t in self.tiers:
                tier_restaurant_names = list(self.d[t].keys())
                for name in tier_restaurant_names:
                    assert self.d[t][name]["year_first_visited"] <= self.d[t][name]["year"]
        except AssertionError:
            print(self.d[t][name]["year_first_visited"])
            print(self.d[t][name]["year"])
            self.fail()

    def tearDown(self):
        self.f.close()


if __name__ == '__main__':
    unittest.main()
