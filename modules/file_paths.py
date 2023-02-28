# coding=utf-8
"""
Created on 10.2.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell

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
__author__ = "Juhani Sundell"
__version__ = "2.0"

from pathlib import Path
from typing import Union
from typing import Optional
from typing import Iterable
from typing import Tuple
from typing import Callable
from typing import Iterator

from .enums import OptimizationType
from .enums import SimulationType
from . import general_functions as gf


def get_erd_file_name(recoil_element: "RecoilElement", seed: Union[int, str],
                      optim_mode: Optional[OptimizationType] = None) -> str:
    """Returns the name of a file that corresponds to given
    recoil element, seed and optimization mode.

    Args:
        recoil_element: recoil element
        seed: seed of the simulation (or '*' when used to glob multiple files)
        optim_mode: either None, 'recoil' or 'fluence'

    Return:
        .erd file name
    """
    if optim_mode is None:
        return f"{recoil_element.get_full_name()}." \
               f"{seed}.erd"
    if optim_mode is OptimizationType.FLUENCE:
        return f"{recoil_element.prefix}-optfl.{seed}.erd"
    if optim_mode is OptimizationType.RECOIL:
        return f"{recoil_element.prefix}-opt.{seed}.erd"

    raise ValueError(f"Unknown optimization mode '{optim_mode}'")


def get_seed(erd_file: Path) -> Optional[int]:
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
        return int(erd_file.name.rsplit('.', 2)[1])
    except (ValueError, IndexError):
        # int could not be parsed or the splitted string did not contain
        # two parts
        return None


def validate_erd_file_names(erd_files: Iterable[Union[Path, str]],
                            recoil_element: "RecoilElement") -> \
                            Iterator[Tuple[Path, int]]:
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
        erd_file = Path(erd_file_path)
        seed = get_seed(erd_file)
        if seed is None:
            continue

        if is_erd_file(recoil_element, erd_file):
            yield erd_file, seed


def is_erd_file(recoil_element: "RecoilElement", file: Path) -> bool:
    """Checks if the file is a valid ERD file name for the given
    recoil element.
    """
    return file.name.startswith(recoil_element.get_full_name()) and \
        file.suffix == ".erd"


def recoil_filter(prefix: str) -> Callable:
    """Returns a filter function that accepts recoil element file names
    that begin with the given prefix and end in either 'rec' or 'sct'.
    """
    exts = {".rec", ".sct"}
    # Last line ensures that e.g. C and Cu are handled separately
    return lambda file: file.name.startswith(prefix) and \
        file.suffix in exts and \
        not file.name[file.name.index(prefix) + len(prefix)].isalpha()


# TODO document what the prefix actually is in the following functions
def is_recoil_file(prefix: str, file: Path) -> bool:
    """Checks whether a file name is a recoil name for the given prefix.
    """
    return recoil_filter(prefix)(file)


def get_recoil_file_path(recoil_element: "RecoilElement", directory: Path) \
        -> Path:
    return Path(directory,
                f"{recoil_element.get_full_name()}.rec")


def is_optfl_result(prefix: str, file: Path) -> bool:
    """Checks whether a file name is a optfl result for the given prefix.
    """
    return file.name.startswith(prefix) and \
        file.name.endswith("-optfl.result") and \
        not file.name[file.name.index(prefix) + len(prefix)].isalpha()


def is_optfirst(prefix: str, file: Path) -> bool:
    """Checks whether a file name is a optfirst file for the given prefix.
    """
    return f"{prefix}-optfirst.rec" == file.name


def is_optmed(prefix: str, file: Path) -> bool:
    """Checks whether a file name is a optmed file for the given prefix.
    """
    return f"{prefix}-optmed.rec" == file.name


def is_optlast(prefix: str, file: Path) -> bool:
    """Checks whether a file name is a optlast file for the given prefix.
    """
    return f"{prefix}-optlast.rec" == file.name


def find_available_file_path(file_paths: Iterable[Path]) -> Path:
    """Iterates over the given file paths and returns the first one
    that does not exist. Raises ValueError if all of the file paths
    already exist.

    Args:
        file_paths: iterable of Path objects.

    Return:
        first file path that does not already exist.
    """
    try:
        return gf.find_next(file_paths, lambda fp: not fp.exists())
    except ValueError:
        raise ValueError("No available file name found")
