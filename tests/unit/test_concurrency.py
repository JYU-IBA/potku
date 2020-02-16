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
"""
__author__ = ""  # TODO
__version__ = ""  # TODO

import unittest
import time

import threading

from timeit import default_timer as timer

from modules.concurrency import CancellationToken


def sleeper(sleep_time, ct):
    # Helper function that sleeps for a while and checks if cancellation has
    # been requested.
    time.sleep(sleep_time)
    ct.raise_if_cancelled()
    time.sleep(sleep_time)


class TestCancellationToken(unittest.TestCase):
    def setUp(self):
        self.ct = CancellationToken()
        self.sleep_time = 0.2
        self.count = 15

    def test_token(self):
        self.assertFalse(self.ct.is_cancellation_requested())
        self.ct.request_cancellation()
        self.assertTrue(self.ct.is_cancellation_requested())
        self.assertRaises(SystemExit,
                          lambda: self.ct.raise_if_cancelled())

    def test_cancelling_threads(self):
        # Create a bunch of threads and start a timer
        threads = [
            threading.Thread(target=sleeper,
                             args=(self.sleep_time, self.ct))
            for _ in range(self.count)
        ]
        start = timer()
        for t in threads:
            t.start()

        # Request cancellation and wait for threads to end
        self.ct.request_cancellation()
        for t in threads:
            t.join()

        # Assert that threads finished faster than 1.5x the sleep time
        stop = timer()
        self.assertLess(stop - start, 1.5 * self.sleep_time)


if __name__ == '__main__':
    unittest.main()