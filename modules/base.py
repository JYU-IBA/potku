# coding=utf-8
"""
Created on 15.04.2020

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

import collections

simulations = collections.namedtuple(
    "Simulations",
    ("running_simulations", "finished_simulations",
     "running_optimizations", "finished_optimizations"),
)


class ElementSimulationContainer:
    __slots__ = ()

    def get_active_simulations(self) -> simulations:
        return simulations(
            self.get_running_simulations(),
            self.get_finished_simulations(),
            self.get_running_optimizations(),
            self.get_finished_optimizations()
        )

    def get_running_simulations(self):
        raise NotImplementedError

    def get_finished_simulations(self):
        raise NotImplementedError

    def get_running_optimizations(self):
        raise NotImplementedError

    def get_finished_optimizations(self):
        raise NotImplementedError
