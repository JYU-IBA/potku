# coding=utf-8
"""
TODO
"""

import unittest

from modules import general_functions as gf
from modules.element import Element


class TestGeneralFunctions(unittest.TestCase):
    def test_match_strs_to_elements(self):
        strs = ["Si", "10C", "C", "12"]
        elements = [
            Element.from_string("Si"),
            Element.from_string("10C"),
            Element.from_string("12C")
        ]
        matches = gf.match_strs_to_elements(strs, elements)

        self.assertEqual(
            ("Si", Element.from_string("Si")),
            next(matches))
        self.assertEqual(
            ("10C", Element.from_string("10C")),
            next(matches))
        self.assertEqual(
            ("C", Element.from_string("12C")),
            next(matches))
        self.assertEqual(
            ("12", None),
            next(matches))

    def test_match_elements_to_strs(self):
        # TODO
        pass

    def test_find_match_in_dicts(self):
        dicts = [{
            1: 2,
            3: 4,
            5: 6
        }, {
            1: 11,      # these values wont be found because
            3: 12,      # the dict has the same keys as the
            5: 13       # first dict
        }, {
            7: 8,
            9: None
        }]

        self.assertEqual((1, 2),
                         gf.find_match_in_dicts(1, dicts))
        self.assertEqual((2, None),
                         gf.find_match_in_dicts(2, dicts))
        self.assertEqual((3, 4),
                         gf.find_match_in_dicts(3, dicts))
        self.assertEqual((5, 6),
                         gf.find_match_in_dicts(5, dicts))
        self.assertEqual((7, 8),
                         gf.find_match_in_dicts(7, dicts))
        self.assertEqual((9, None),
                         gf.find_match_in_dicts(9, dicts))


if __name__ == "__main__":
    unittest.main()
