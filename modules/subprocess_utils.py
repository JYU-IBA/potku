# coding=utf-8
"""
Created on 01.10.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"


import subprocess
from pathlib import Path
from typing import Callable
from typing import Iterable
from typing import Optional
from typing import TypeVar

T0 = TypeVar("T0")
T1 = TypeVar("T1")


class StdoutStream:
    """Class for processing stdout of a subprocess.Popen. Can be used as a
    context manager.
    """
    def __init__(self, process: subprocess.Popen):
        """Initializes a new StdoutStream.

        Args:
            process: a subprocess.Popen object
        """
        self._stdout = process.stdout
        self._output = iter(self._stdout.readline, "")

    @property
    def closed(self) -> bool:
        """Whether the StdoutStream is closed or not. Iterating a closed
        stream raises an exception.
        """
        return self._stdout.closed

    def close(self):
        """Closes the stdout.
        """
        self._stdout.close()

    # Iterator methods
    def __iter__(self):
        return self

    def __next__(self):
        return next(self._output)

    # context manager methods
    def __enter__(self) -> "StdoutStream":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def write_to_file(
        iterable: Iterable[T0],
        file: Path,
        text_func: Callable[[T0], str] = str) -> Iterable[T0]:
    """Writes the iterable to a file and yields each item as they were.

    Args:
        iterable: iterable to be written to a file
        file: path to file where items are written
        text_func: function that transforms each item into a string (str by
            default)

    Yield:
        unchanged items from the original iterable
    """
    if text_func is None:
        raise ValueError("text_func must be provided")
    with file.open("w") as output_file:
        for item in iterable:
            output_file.write(text_func(item))
            yield item


def process_output(
        process: subprocess.Popen,
        parse_func: Optional[Callable[[str], T0]] = None,
        file: Optional[Path] = None,
        text_func: Callable[[T0], str] = str,
        output_func: Callable[[Iterable[T0]], T1] = list) -> T1:
    """Processes the output from a subprocess line by line.

    Args:
        process: a subprocess.Popen object
        parse_func: optional function to parse each line
        file: optional path to a file in which the parsed output is written
        text_func: function that transforms each line into a string to be
            written to a file (str by default)
        output_func: function that returns an aggregate of all lines (list by
            default)

    Return:
        processed lines as an object returned by output_func
    """
    with StdoutStream(process) as stream:
        if parse_func is not None:
            stream = map(parse_func, stream)
        if file is not None:
            stream = write_to_file(stream, file, text_func=text_func)
        return output_func(stream)
