# coding=utf-8
"""
Created on 19.1.2020
Updated on 8.2.2020

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

utils.py contains various utility functions to be used in tests
"""

__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import os
import hashlib
import unittest
import logging
import platform


def get_sample_data_dir():
    """Returns the absolute path to the sample data directory"""
    # Absolute path to the directory where utils.py file is
    path_to_this_file = os.path.dirname(__file__)
    # Traverse the path to sample data
    path_to_sample_data = os.path.join(path_to_this_file,
                                       os.pardir,
                                       "sample_data")
    # Return the path as an absolute path
    return os.path.abspath(path_to_sample_data)


def get_resource_dir():
    return os.path.join(os.path.dirname(__file__), "resource")


def change_wd_to_root(func):
    """Helper wrapper function that changes the working directory to the root
    directory of Potku for the duration of the wrapped function. After the
    function has run, working directory is changed back so other tests are
    not affected.

    Use this function if the code you are testing is referencing some relative
    path, like 'external/Potku-data/masses.dat'. The tested code will then
    need to be imported inside that function.
    """
    # Get old working directory and path to this file. Then traverse to
    # parent directory (i.e. the root)
    old_wd = os.getcwd()
    path_to_this_file = os.path.dirname(__file__)
    path_to_root = os.path.join(path_to_this_file,
                                os.pardir)

    def wrapper(*args, **kwargs):
        # Change the dir, run the func and change back in the finally
        # block
        os.chdir(path_to_root)
        try:
            func(*args, **kwargs)
        finally:
            os.chdir(old_wd)

    # Return the wrapper function
    return wrapper


def get_md5_for_files(file_paths):
    """Calculates MD5 hash for the combined content of all given
    files."""
    for file_path in file_paths:
        hasher = hashlib.md5()
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
    running a test."""
    b, reason = check_md5_for_files(file_paths, checksum)
    if b:
        return lambda func: func
    if msg is not None:
        return unittest.skip("{0}: {1}.".format(msg, reason))
    return unittest.skip(reason)


def disable_logging():
    """Disables loggers and removes their file handles"""
    loggers = [logging.getLogger(name) for name in
               logging.root.manager.loggerDict]
    for logger in loggers:
        logger.disabled = True
        for handler in logger.handlers:
            handler.close()


class PlatformSwitcher:
    platforms = {
        "Windows": ("Windows", "\\"),
        "Linux": ("Linux", "/"),
        "Darwin": ("Darwin", "/")
    }

    def __init__(self, system):
        # TODO os.sep does not affect file paths
        try:
            self.system, self.sep = PlatformSwitcher.platforms[system]
        except KeyError:
            raise ValueError(f"PlatformSwitcher was given an unsupported os "
                             f"{system}")

        self.old_platsys = platform.system
        self.old_os_sep = os.sep

    def __enter__(self):
        platform.system = lambda: self.system
        os.sep = self.sep

    def __exit__(self, exc_type, exc_val, exc_tb):
        platform.system = self.old_platsys
        os.sep = self.old_os_sep


