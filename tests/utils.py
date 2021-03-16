# coding=utf-8
"""
Created on 19.1.2020

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

utils.py contains various utility functions to be used in tests
"""

__author__ = "Juhani Sundell"
__version__ = "2.0"

import os
import hashlib
import unittest
import platform
import warnings
import itertools
import functools
import modules.general_functions as gf

from pathlib import Path
from string import Template
from typing import (
    Dict,
    Any,
    Callable,
    Optional,
)


def get_sample_data_dir() -> Path:
    """Returns the absolute path to the sample data directory.
    """
    return gf.get_root_dir() / "sample_data"


def get_resource_dir() -> Path:
    """Returns the resource directory's absolute path.
    """
    return gf.get_root_dir() / "tests" / "resource"


def change_wd_to_root(func):
    """Helper wrapper function that changes the working directory to the root
    directory of Potku for the duration of the wrapped function. After the
    function has run, working directory is changed back so other tests are
    not affected.

    This decorator was originally used to test code that read a file
    using a relative path. Now the file path has been made absolute, so this
    function is no longer needed for its original purpose. However, there may
    be other uses for this.
    """
    # Get old working directory and path to this file. Then traverse to
    # parent directory (i.e. the root)
    old_wd = Path.cwd()
    root = gf.get_root_dir()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Change the dir, run the func and change back in the finally
        # block
        os.chdir(root)
        try:
            func(*args, **kwargs)
        finally:
            os.chdir(old_wd)

    # Return the wrapper function
    return wrapper


def get_md5_for_files(file_paths):
    """Calculates MD5 hash for the combined content of all given
    files."""
    hasher = hashlib.md5()
    for file_path in file_paths:
        with open(file_path, "rb") as file:
            buf = file.read()
            hasher.update(buf)

    return hasher.hexdigest()


def check_md5_for_files(file_paths, checksum):
    """Checks that the combined contents of all files match the
    given checksum.

    Args:
        file_paths: absolute paths to file
        checksum: hexadecimal string representation of the expected
            checksum

    Return:
        tuple where first element is a boolean value that tells if
        the given files match the checksum, and second element is a
        message that tells further details about the check.
    """
    try:
        actual_checksum = get_md5_for_files(file_paths)
        if actual_checksum == checksum:
            return True, "files match the given checksum"

        return False, "files do not match the given checksum"
    except Exception as e:
        return False, e


def verify_files(file_paths, checksum, msg=None):
    """Decorator function that can be used to verify files before
    running a test.
    """
    b, reason = check_md5_for_files(file_paths, checksum)
    if b:
        return lambda func: func
    if msg is not None:
        return unittest.skip(f"{msg}: {reason}.")
    return unittest.skip(reason)


WINDOWS = "Windows"
LINUX = "Linux"
MAC = "Darwin"


class PlatformSwitcher:
    """Context manager that switches the value returned by platform.system().

    Usage:
    with PlatformSwitcher('name of the os'):
        # os specific code here
    """
    platforms = frozenset([WINDOWS, LINUX, MAC])

    def __init__(self, system):
        if system not in self.platforms:
            raise ValueError(f"PlatformSwitcher was given an unsupported os "
                             f"{system}")
        self.system = system
        self.old_platsys = platform.system

    def __enter__(self):
        """Upon entering the context manager platform.system is overridden
        to return a value given in initialization."""
        platform.system = lambda: self.system

    def __exit__(self, exc_type, exc_val, exc_tb):
        """When exiting, platform.system is restored."""
        platform.system = self.old_platsys


class ListdirSwitcher:
    """Context manager that changes the output of os.listdir to a given list
    of strings.
    """
    def __init__(self, file_names):
        self.file_names = file_names
        self.old_listdir = os.listdir

    def __enter__(self):
        os.listdir = lambda _: self.file_names

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.listdir = self.old_listdir


def get_template_file_contents(template_file, **kwargs):
    """Reads a template file and substitutes in the values provided as
    keyword arguments.
    """
    with open(template_file) as file:
        temp = Template(file.read())

    return temp.substitute(kwargs)


def only_succeed_on(*systems: str) -> Callable:
    """Expect the decorated test to fail on given systems:
    """
    systems = set(systems)
    if platform.system() not in systems:
        return unittest.expectedFailure
    return lambda func: func


def only_run_on(*systems: str, reason: Optional[str] = None) -> Callable:
    """Only runs the test function on given systems.
    """
    systems = set(systems)
    if platform.system() not in systems:
        if reason is None:
            reason = f"This test is only for {', '.join(systems)}"
        return unittest.skip(reason)
    return lambda func: func


def run_without_warnings(func):
    """Runs the given function and returns its return value while ignoring
    warnings.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return func()


def assert_has_slots(obj: Any):
    """Asserts that the given object has a __slots__ declaration. If not,
    raises AssertionError.
    """
    if not hasattr(obj, "__slots__"):
        raise AssertionError("Object does not have __slots__.")
    for i in range(1000):
        attr = f"xyz{i}"
        if not hasattr(obj, attr) and attr not in getattr(obj, "__slots__"):
            try:
                setattr(obj, attr, "foo")
                raise AssertionError(
                    "__slots__ declaration not working as intended, perhaps "
                    "due to inheritance.")
            except AttributeError:
                return


def assert_folder_structure_equal(expected_structure: Dict, directory: Path):
    """Tests if the given directory contains the expected folder structure.

    Args:
        expected_structure: folder structure defined as dictionary. Keys are
            fjles and folders, values are dictionaries (if the key is a folder)
            or NoneTypes.
        directory: path to a directory whose structure is being tested.
    """
    if not isinstance(expected_structure, dict):
        raise ValueError(f"Expected folder structure should be defined as "
                         f"dictionary, {type(expected_structure)} given")
    fnames = set(f.name for f in os.scandir(directory))
    keys = set(expected_structure.keys())
    if keys != fnames:
        raise AssertionError(
            f"Contents of the directory {directory} did not match expected "
            f"values. Expected:\n{sorted(keys)}\nGot:\n{sorted(fnames)}")
    for k, v in expected_structure.items():
        p = directory / k
        if isinstance(v, dict):
            assert_folder_structure_equal(v, p)
        elif v is None:
            if not p.is_file():
                raise AssertionError(
                    f"Expected {p} to be a file but it was not."
                )
        else:
            raise ValueError(
                f"Value should either be 'None' or a dictionary. {type(v)} "
                f"given.")


def assert_all_same(*args):
    """Asserts that all given arguments are the same object. Raises
    AssertionError if that is not the case.
    """
    if not all(x is y for x, y in itertools.combinations(args, 2)):
        raise AssertionError(
            f"All given arguments are not the same object. Arguments: "
            f"{','.join(str(a) for a in args)}")


def assert_all_equal(*args):
    """Asserts that all given arguments are equal. Raises AssertionError if
    that is not the case.
    """
    if not all(x == y for x, y in itertools.combinations(args, 2)):
        raise AssertionError(
            f"All given arguments are not equal. Arguments: "
            f"{','.join(str(a) for a in args)}")
