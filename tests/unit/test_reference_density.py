# coding=utf-8
"""
Created on 16.3.2023
Updated on 13.4.2023

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2022 Joonas Koponen and Tuomas Pitkänen, 2023 Sami Voutilainen

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
__author__ = "Joonas Koponen \n Tuomas Pitkänen \n Sami Voutilainen"
__version__ = "2.0"

import unittest
import tests.mock_objects as mo

from modules.element import Element
from modules.layer import Layer
from modules.reference_density import ReferenceDensity


class TestUpdatingReferenceDensity(unittest.TestCase):

    def test_dynamic_reference_density(self):

        target_no_layers = mo.Target(layers=[])
        no_layers = ReferenceDensity(target_no_layers.layers)
        self.assertEqual(no_layers.get_value(), 0.0)

        target_one_layer_under_limit = mo.Target(layers=[
            Layer("Si", [Element.from_string("Si 1.0")], 1.0, 2.3290)
        ])

        one_layer_under_limit = ReferenceDensity(
            target_one_layer_under_limit.layers)

        self.assertAlmostEqual(one_layer_under_limit.get_value(),
                         4.993970863902691e+22)

        target_one_layer_over_limit = mo.Target(layers=[
            Layer("Si", [Element.from_string("Si 1.0")], 10.0, 2.3290)
        ])

        one_layer_over_limit = ReferenceDensity(
            target_one_layer_over_limit.layers)

        self.assertEqual(one_layer_over_limit.get_value(),
                         4.993970863902691e+22)

        target_two_layers_over_limit = mo.Target(layers=[
            Layer("Au", [Element.from_string("Au 1.0")], 11.0, 19.32),
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290)
        ])

        two_layers_over_limit = ReferenceDensity(
            target_two_layers_over_limit.layers)

        self.assertEqual(two_layers_over_limit.get_value(),
                         5.906980546244748e+22)

        target_two_layers_under_limit = mo.Target(layers=[
            Layer("Au", [Element.from_string("Au 1.0")], 1.0, 19.32),
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290)
        ])

        two_layers_under_limit = ReferenceDensity(
            target_two_layers_under_limit.layers)

        self.assertEqual(two_layers_under_limit.get_value(),
                         5.085271832136897e+22)

        target_two_in_same_layer_under_limit = mo.Target(layers=[
            Layer("SiN", [Element.from_string("Si 0.43"),
                          Element.from_string("N 0.57")], 1.0, 3.17),
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290)
        ])

        two_elements_in_same_layer_under_limit = ReferenceDensity(
            target_two_in_same_layer_under_limit.layers)

        self.assertEqual(5.446206442383031e+22, two_elements_in_same_layer_under_limit.get_value())

        target_two_in_same_layer_over_limit = mo.Target(layers=[
            Layer("SiN", [Element.from_string("Si 0.43"),
                          Element.from_string("N 0.57")], 11.0, 3.17),
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290)
        ])

        two_elements_in_same_layer_over_limit = ReferenceDensity(
            target_two_in_same_layer_over_limit.layers)

        self.assertEqual(9.51632664870609e+22, two_elements_in_same_layer_over_limit.get_value())

        target_two_layers_under_limit_reversed = mo.Target(layers=[
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290),
            Layer("Au", [Element.from_string("Au 1.0")], 1.0, 19.32)
        ])

        two_layers_under_limit_reversed = ReferenceDensity(
            target_two_layers_under_limit_reversed.layers)

        self.assertEqual(4.993970863902691e+22,
            two_layers_under_limit_reversed.get_value())

        target_two_layers_over_limit_reversed = mo.Target(layers=[
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290),
            Layer("Au", [Element.from_string("Au 1.0")], 11.0, 19.32)
        ])

        two_layers_over_limit_reversed = ReferenceDensity(
            target_two_layers_over_limit_reversed.layers)

        self.assertEqual(4.993970863902691e+22, two_layers_over_limit_reversed.get_value())

    def test_update_layers(self):

        target_two_in_same_layer_under_limit = mo.Target(layers=[
            Layer("SiN", [Element.from_string("Si 0.43"),
                          Element.from_string("N 0.57")], 1.0, 3.17),
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290)
        ])

        two_elements_in_same_layer_under_limit = ReferenceDensity(
            target_two_in_same_layer_under_limit.layers)

        two_elements_in_same_layer_under_limit_duplicate = ReferenceDensity(
            target_two_in_same_layer_under_limit.layers)

        self.assertEqual(
            two_elements_in_same_layer_under_limit.get_value(),
            two_elements_in_same_layer_under_limit_duplicate.get_value()
        )

        new_target_two_in_same_layer_under_limit = mo.Target(layers=[
            Layer("SiN", [Element.from_string("Si 0.5"),
                          Element.from_string("N 0.5")], 1.0, 3.17),
            Layer("Si", [Element.from_string("Si 1.0")], 100.0, 2.3290)
        ])

        two_elements_in_same_layer_under_limit.update_layers(
            new_target_two_in_same_layer_under_limit.layers
        )

        self.assertNotEqual(
            two_elements_in_same_layer_under_limit.get_value(),
            two_elements_in_same_layer_under_limit_duplicate.get_value()
        )

        two_elements_in_same_layer_under_limit_duplicate.update_layers(
            new_target_two_in_same_layer_under_limit.layers
        )

        self.assertEqual(
            two_elements_in_same_layer_under_limit.get_value(),
            two_elements_in_same_layer_under_limit_duplicate.get_value()
        )

    def test_manual_density(self):

        target_one_layer_under_limit = mo.Target(layers=[
            Layer("Si", [Element.from_string("Si 1.0")], 1.0, 2.3290)
        ])

        initially_true_use_user_value = ReferenceDensity(
            target_one_layer_under_limit.layers, 5.0e+20, True)

        initially_false_use_user_value = ReferenceDensity(
            target_one_layer_under_limit.layers, 5.0e+20, False)

        self.assertEqual(initially_true_use_user_value.get_value(),
                         5.0e+20)

        self.assertAlmostEqual(initially_false_use_user_value.get_value(),
                         4.99397e+22, delta=1.0e19)

        self.assertEqual(initially_true_use_user_value.manual_density,
                         initially_false_use_user_value.manual_density)

        self.assertNotEqual(initially_true_use_user_value.get_value(),
                            initially_false_use_user_value.get_value()
                            )

        initially_true_use_user_value.use_user_value = False

        self.assertAlmostEqual(initially_true_use_user_value.get_value(),
                         4.99397e+22, delta=1.0e19)


