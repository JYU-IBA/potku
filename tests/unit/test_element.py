# coding=utf-8
"""
Created on 14.02.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 TODO

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = ""  # TODO
__version__ = ""  # TODO

import unittest
import random

import tests.mock_objects as mo
import modules.masses as masses

from modules.element import Element


class TestElement(unittest.TestCase):
    def test_from_string(self):
        self.assertRaises(ValueError,
                          lambda: Element.from_string(""))

        self.assertRaises(ValueError,
                          lambda: Element.from_string("4"))

        self.assertRaises(ValueError,
                          lambda: Element.from_string("2 2"))

        e = Element.from_string("He")

        self.assertEqual("He", e.symbol)
        self.assertIsNone(e.isotope)
        self.assertEqual(0, e.amount)

        e = Element.from_string("4He")

        self.assertEqual("He", e.symbol)
        self.assertEqual(4, e.isotope)

        e = Element.from_string("3H 2")

        self.assertEqual("H", e.symbol)
        self.assertEqual(3, e.isotope)
        self.assertEqual(2, e.amount)

    def test_lt(self):
        elems = [
            Element.from_string("H"),
            Element.from_string("He"),
            Element.from_string("C"),
            Element.from_string("C 2"),
            Element.from_string("4C"),
            Element.from_string("5C"),
            Element.from_string("15Si"),
            Element.from_string("Mn"),
            Element.from_string("Mn 2"),
            Element.from_string("16Mn"),
            Element.from_string("243Bk"),
            Element.from_string("250Cf")
        ]

        orig_elems = list(elems)
        random.shuffle(elems)
        self.assertEqual(orig_elems, sorted(elems))

    def test_eq(self):
        self.assertEqual(Element.from_string("He"),
                         Element.from_string("He"))

        self.assertEqual(Element.from_string("4He"),
                         Element.from_string("4He"))

        self.assertEqual(Element.from_string("4He 2"),
                         Element.from_string("4He 2.00"))

        self.assertEqual(Element("He", 4, 2),
                         Element("He", 4, 2.00))

        self.assertEqual(Element("He", 4, 0),
                         Element("He", 4))

        self.assertEqual(Element("He"),
                         Element("He", None))

        self.assertNotEqual(Element.from_string("4He 2"),
                            Element.from_string("4He 1"))

        self.assertNotEqual(Element.from_string("3He"),
                            Element.from_string("4He"))

        self.assertNotEqual(Element.from_string("He"),
                            Element.from_string("4He"))

        self.assertNotEqual(Element.from_string("He"),
                            Element.from_string("H"))

        self.assertNotEqual(Element.from_string("H"), "H")

    def test_equals_prop_based(self):
        n = 1000
        for _ in range(n):
            elem1 = mo.get_element(randomize=True)
            elem1_str = str(elem1)
            elem2 = Element.from_string(elem1_str)
            self.assertIsNot(elem1, elem2)
            self.assertEqual(elem1, elem2)

    def test_get_isotopes(self):
        self.assert_isotopes_match("H", (1, 2), include_st_mass=False)
        self.assert_isotopes_match("H", (None, 1, 2), include_st_mass=True)
        self.assertEqual([], Element.get_isotopes("U", include_st_mass=True,
                                                  filter_unlikely=True))

    def assert_isotopes_match(self, symbol, isotopes, include_st_mass):
        isos = Element.get_isotopes(symbol, include_st_mass=include_st_mass)

        self.assertEqual(len(isotopes), len(isos))

        if include_st_mass and isos:
            self.assertIsNone(isos[0]["abundance"])

        for n, iso in zip(isotopes, isos):
            self.assertEqual(
                ["element", "abundance", "mass"],
                list(iso.keys())
            )
            self.assertEqual(Element("H", n), iso["element"])

    def test_most_common_isotope(self):
        self.assertEqual(4, Element("He").get_most_common_isotope())
        self.assertIsNone(Element("U").get_most_common_isotope())

        # get_most_common_isotope just simply returns the number value of
        # masses.get_most_common_isotope
        for _ in range(100):
            e = mo.get_element(randomize=True)

            mi = masses.get_most_common_isotope(e.symbol)

            if mi is None:
                self.assertEqual(mi, e.get_most_common_isotope())
            else:
                self.assertEqual(
                    masses.get_most_common_isotope(e.symbol)[masses.NUMBER_KEY],
                    e.get_most_common_isotope())


if __name__ == '__main__':
    unittest.main()
