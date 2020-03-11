# coding=utf-8
"""
Created on 08.03.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = ""  # TODO
__version__ = ""  # TODO

import unittest
import random

from modules.nsgaii import pick_final_solutions


class TestPickFinalSolutions(unittest.TestCase):
    """Tests for the pick_final_solutions function that returns solutions
    from the final pareto front to be presented to the user.

    For simplicity's sake the objective values and solutions have the same
    values.
    """

    def test_pick_final_solutions(self):
        """Tests picking solutions from a pareto front"""
        # Create some objective values and shuffle them.
        obj_vals = [
            (3, 0), (2, 2), (0, 3), (2.5, 1.5), (2.9, 0.1), (0.1, 2.9)
        ]
        random.shuffle(obj_vals)
        sols = list(obj_vals)
        # Also take copies of both lists to ensure that they are not modified
        # during the function
        c_obj = list(obj_vals)
        c_sol = list(sols)

        self.assertEqual(((0, 3), (3, 0)),
                         pick_final_solutions(obj_vals, sols, count=2))

        self.assertEqual(((0, 3), (2, 2), (3, 0)),
                         pick_final_solutions(obj_vals, sols, count=3))

        self.assertEqual(c_obj, obj_vals)
        self.assertEqual(c_sol, sols)

    def test_nonpareto_front(self):
        """Tests picking solutions from a non-pareto front."""
        # Currently the function makes no assumptions about pareto optimality,
        # which makes the function slower. If the assumption is made, this
        # test may fail.
        obj_vals = [(1, 2), (0, 0), (2, 1)]
        sols = list(obj_vals)

        self.assertEqual(((0, 0), (0, 0)),
                         pick_final_solutions(obj_vals, sols, count=2))

        self.assertEqual(((0, 0), (2, 1), (0, 0)),
                         pick_final_solutions(obj_vals, sols, count=3))

    def test_single_pareto_solution(self):
        """Tests picking solutions from a front containing single solution.
        """
        obj_vals = [(0, 0)]
        sols = list(obj_vals)

        self.assertEqual(((0, 0), (0, 0)),
                         pick_final_solutions(obj_vals, sols, count=2))

        self.assertEqual(((0, 0), (0, 0), (0, 0)),
                         pick_final_solutions(obj_vals, sols, count=3))

    def test_bad_inputs(self):
        self.assertRaises(IndexError,
                          lambda: pick_final_solutions([], [], count=2))
        self.assertRaises(IndexError,
                          lambda: pick_final_solutions([], [], count=3))
        self.assertRaises(ValueError,
                          lambda: pick_final_solutions([], [], count=0))
        self.assertRaises(ValueError,
                          lambda: pick_final_solutions([], [], count=4))


if __name__ == '__main__':
    unittest.main()