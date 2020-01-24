# coding=utf-8
"""
Created on 23.1.2020

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

ProgressReporter is used to report progress from running processes.
It can be used to for example update the value of a progress bar.
"""

__author__ = "Juhani Sundell"
__version__ = ""    # TODO

import abc


class ProgressReporter(abc.ABC):
    """Base abstract class from which all progress reporters should derive."""
    def __init__(self, progress_callback):
        """Inits a ProgressReporter.

        Args:
            progress_callback: function that will be called, when the reporter
                               reports progress
        """
        self.progress_callback = progress_callback

    @abc.abstractmethod
    def report(self, value):
        """Method that is used to invoke the callback.

        Args:
            value: progress value to report.
        """
        pass


class GUIProgressReporter(ProgressReporter):
    """Class that is used to report progress in a GUI program."""

    def report(self, value):
        """Reports the value of progress by invoking the progress callback.

        Args:
            value: progress value to report
        """
        # TODO this should be called in the original (GUI) thread that created
        #      the ProgressReporter
        self.progress_callback(value)


if __name__ == "__main__":
    # For testing purposes
    pro = GUIProgressReporter(lambda x: print(x**2))
    pro.report(10)
    pro.report(20)
