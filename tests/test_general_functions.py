# coding=utf-8
"""
TODO
"""

import unittest

from modules import general_functions as gf
from modules.element import Element


class TestMatchingFunctions(unittest.TestCase):
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
        strs = ["Si", "10C", "C", "12"]
        elements = [
            Element.from_string("Si"),
            Element.from_string("10C"),
            Element.from_string("12C"),
            Element.from_string("Br")
        ]
        matches = gf.match_elements_to_strs(elements, strs)
        self.assertEqual(next(matches),
                         (Element.from_string("Si"), "Si"))
        self.assertEqual(next(matches),
                         (Element.from_string("10C"), "10C"))
        self.assertEqual(next(matches),
                         (Element.from_string("12C"), "C"))
        self.assertEqual(next(matches),
                         (Element.from_string("Br"), None))

        # Matches has been exhausted and this will produce an
        # exception
        self.assertRaises(StopIteration, lambda: next(matches))

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

        self.assertEqual(gf.find_match_in_dicts(1, dicts), 2)
        self.assertIsNone(gf.find_match_in_dicts(2, dicts))
        self.assertEqual(gf.find_match_in_dicts(3, dicts), 4)
        self.assertEqual(gf.find_match_in_dicts(5, dicts), 6)
        self.assertEqual(gf.find_match_in_dicts(7, dicts), 8)
        self.assertIsNone(gf.find_match_in_dicts(9, dicts))

        # Testing with empty lists and dicts
        self.assertIsNone(gf.find_match_in_dicts(1, []))
        self.assertIsNone(gf.find_match_in_dicts(None, [{}]))

        # Testing invalid values
        self.assertRaises(
            TypeError, lambda: gf.find_match_in_dicts(1, [[1]]))
        self.assertRaises(
            TypeError, lambda: gf.find_match_in_dicts(1, [set(1, 2)]))
        self.assertRaises(
            TypeError, lambda: gf.find_match_in_dicts([], [{[]: []}]))


if __name__ == "__main__":
    unittest.main()
