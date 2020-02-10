# coding=utf-8
"""
Created on 10.2.2020

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

file_paths.py module is intended for providing functions that
return or validate various file paths used by Potku. File I/O
should be performed in other modules.
"""
__author__ = "Juhani Sundell"
__version__ = ""  # TODO


def get_erd_file_name(recoil_element, seed, optim_mode=None,
                      get_espe_param=False):
    """Returns the name of a file that corresponds to given
    recoil element, seed, optimization mode and get_espe_param.

    Args:
        recoil_element: recoil element
        seed: seed of the simulation
        optim_mode: either None, 'recoil' or 'fluence'
        get_espe_param: boolean that determines if the file is going
                        to be used as a parameter for get_espe

    Return:
        .erd file name
    """
    # TODO check for path traversal (maybe with a decorator)
    espe_str = ".*" if get_espe_param else ""

    if optim_mode is None:
        return f"{recoil_element.prefix}-{recoil_element.name}." \
               f"{seed}{espe_str}.erd"
    if optim_mode == "fluence":
        return f"{recoil_element.prefix}-optfl.{seed}{espe_str}.erd"
    if optim_mode == "recoil":
        return f"{recoil_element.prefix}-opt.{seed}{espe_str}.erd"

    raise ValueError(f"Unknown optimization mode '{optim_mode}'")