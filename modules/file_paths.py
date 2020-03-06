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

from pathlib import Path


def get_erd_file_name(recoil_element, seed, optim_mode=None):
    """Returns the name of a file that corresponds to given
    recoil element, seed and optimization mode.

    Args:
        recoil_element: recoil element
        seed: seed of the simulation
        optim_mode: either None, 'recoil' or 'fluence'

    Return:
        .erd file name
    """
    if optim_mode is None:
        return f"{recoil_element.prefix}-{recoil_element.name}." \
               f"{seed}.erd"
    if optim_mode == "fluence":
        return f"{recoil_element.prefix}-optfl.{seed}.erd"
    if optim_mode == "recoil":
        return f"{recoil_element.prefix}-opt.{seed}.erd"

    raise ValueError(f"Unknown optimization mode '{optim_mode}'")


def get_seed(erd_file):
    """Returns seed value from given .erd file path.

    Does not check if the 'erd_file' parameter is a valid
    file name or path.

    Args:
        erd_file: name or path to an .erd file.

    Returns:
        seed as an integer or None if seed value could not be
        parsed.
    """
    try:
        return int(erd_file.rsplit('.', 2)[1])
    except (ValueError, IndexError):
        # int could not be parsed or the splitted string did not contain
        # two parts
        return None


def validate_erd_file_names(erd_files, recoil_element):
    """Checks if the iterable of .erd files contains valid file names
    for the given recoil element.

    Invalid erd files are filtered out of the output.

    Args:
        erd_files: iterable of .erd file names or paths
        recoil_element: recoil element to which files are matched

    Yield:
        tuple containing a valid erd file name or path and its seed value
    """
    for erd_file_path in erd_files:
        # TODO on a Unix-like system this will allow file names like
        #  '4He-default.\.101.erd' to be valid but on Win this is not the
        #  case. Not sure how to specify what the correct behaviour should
        #  be
        erd_file = Path(erd_file_path).name
        seed = get_seed(erd_file)
        if seed is None:
            continue

        if is_erd_file(recoil_element, erd_file):
            yield erd_file_path, seed


def is_erd_file(recoil_element, file_name):
    """Checks if the file is a valid ERD file name for the given
    recoil element.
    """
    return file_name.startswith(recoil_element.get_full_name()) and \
        file_name.endswith(".erd")


def recoil_filter(prefix):
    """Returns a filter function that accepts recoil element file names
    that begin with the given prefix and end in either 'rec' or 'sct'.
    """
    # Last line ensures that e.g. C and Cu are handled separately
    return lambda file: file.startswith(prefix) and \
        (file.endswith(".rec") or file.endswith(".sct")) and \
        not file[file.index(prefix) + len(prefix)].isalpha()


# TODO document what the prefix actually is in the following functions
def is_recoil_file(prefix, file_name):
    """Checks whether a file name is a recoil name for the given prefix.
    """
    return recoil_filter(prefix)(file_name)


def get_recoil_file_path(recoil_element, directory):
    return Path(directory,
                f"{recoil_element.get_full_name()}.{recoil_element.type}")


def is_optfl_result(prefix, file_name):
    """Checks whether a file name is a optfl result for the given prefix.
    """
    return file_name.startswith(prefix) and \
        file_name.endswith("-optfl.result") and \
        not file_name[file_name.index(prefix) + len(prefix)].isalpha()


def is_optfirst(prefix, file_name):
    """Checks whether a file name is a optfirst file for the given prefix.
    """
    return f"{prefix}-optfirst.rec" == file_name


def is_optlast(prefix, file_name):
    """Checks whether a file name is a optlast file for the given prefix.
    """
    return f"{prefix}-optlast.rec" == file_name
