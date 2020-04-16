# coding=utf-8
"""
Created on 15.02.2020

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

Concurrency module provides helper functions and classes for asynchronous,
multithreaded or multiprocessing operations.
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"

import sys


class CancellationToken:
    """A token that can be used issue stopping requests from one thread to
    another.

    Holds a single flag that is set to False at initialization. The value can
    be set to True by calling request_cancellation.

    Flag status can be checked with is_cancellation_requested or
    raise_if_cancelled functions. The latter will raise a SystemExit if the
    flag is True, killing the calling Thread.
    """

    def __init__(self):
        """Initializes a new CancellationToken.
        """
        self.__cancel = False

    def request_cancellation(self):
        """Requests cancellation.
        """
        self.__cancel = True

    def is_cancellation_requested(self):
        """Whether cancellation has been requested.
        """
        return self.__cancel

    def raise_if_cancelled(self):
        """Raises SystemExit if cancellation has been requested.
        """
        if self.is_cancellation_requested():
            sys.exit()
