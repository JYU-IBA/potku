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
        self.assertIsNone(e.amount)

        e = Element.from_string("4He")

        self.assertEqual("He", e.symbol)
        self.assertEqual(4, e.isotope)
        self.assertIsNone(e.amount)

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

        self.assertNotEqual(Element.from_string("4He 2"),
                            Element.from_string("4He 1"))

        self.assertNotEqual(Element.from_string("3He"),
                            Element.from_string("4He"))

        self.assertNotEqual(Element.from_string("He"),
                            Element.from_string("4He"))

        self.assertNotEqual(Element.from_string("He"),
                            Element.from_string("H"))

        self.assertNotEqual(Element.from_string("H"), "H")


if __name__ == '__main__':
    unittest.main()
