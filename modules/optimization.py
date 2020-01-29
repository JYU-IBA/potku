# coding=utf-8
"""
Created on 29.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Heta Rekilä

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

Optimization module contains functions used in NSGA2 algorithm
"""

__author__ = "Heta Rekilä \n Juhani Sundell"
__version__ = "2.0"

import numpy as np


def dominates(a, b):
    """
    Check if solution a dominates solution b. Minimization. This is related
    to the NSGA-II optimization function (modules/nsgaii.py).

    Args:
        a: Solution (objective values) a.
        b: Solution (objective values) b.

    Return:
        Whether a dominates b.
    """
    is_better = False
    for ai, bi in zip(a, b):
        if ai > bi:
            return False
        if ai < bi:
            is_better = True
    return is_better


def tournament_allow_doubles(t, p, fit):
    """
    Tournament selection that allows one individual to be in the mating pool
    several times.

    Args:
        t: Number of solutions to be compared, size of tournament.
        p: Number of solutions to be selected as parents in the mating pool.
        fit: Fitness vectors.

    Return:
        Index of selected solutions.
    """
    n = len(fit)
    pool = []
    for i in range(p):
        candidates = []
        # Find k different candidates for tournament
        j = 0
        while j in range(t):
            candidate = np.random.randint(n)
            if candidate not in candidates:
                candidates.append(candidate)
                j += 1
        min_front = min([fit[i, 0] for i in candidates])
        min_candidates = [i for i in candidates if fit[i, 0] == min_front]
        number_of_mins = len(min_candidates)
        if number_of_mins > 1:  # If multiple candidates from the same front
            # Find the candidate with smallest crowding distance
            max_dist = max([fit[i, 1] for i in min_candidates])
            max_cands = [i for i in min_candidates if fit[i, 1] == max_dist]
            pool.append(max_cands[0])
        else:
            pool.append(min_candidates[0])

    return np.array(pool)