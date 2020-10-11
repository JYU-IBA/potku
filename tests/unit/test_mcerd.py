# coding=utf-8
"""
Created on 27.04.2020

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

import unittest
import rx
import subprocess
import time
import tempfile
import platform
from pathlib import Path

from modules.concurrency import CancellationToken
import modules.mcerd as mcerd

from tests.mock_objects import TestObserver


class TestParseOutput(unittest.TestCase):
    def test_calculated_amounts(self):
        s1 = "Calculated 0 of 0 ions (0%)"
        s2 = "Calculated 9595 of 10100 ions (5%)"
        s3 = "Calculated 0 of n ions (50%)"
        s4 = "Calculated -10 of -1000 ions (10%)"

        self.assertEqual({
            "calculated": 0,
            "total": 0,
            "percentage": 0
        }, mcerd.parse_raw_output(s1))

        self.assertEqual({
            "calculated": 9595,
            "total": 10100,
            "percentage": 5
        }, mcerd.parse_raw_output(s2))

        self.assertEqual({
            "msg": "Calculated 0 of n ions (50%)"
        }, mcerd.parse_raw_output(s3))

        self.assertEqual({
            "msg": "Calculated -10 of -1000 ions (10%)"
        }, mcerd.parse_raw_output(s4))

    def test_others(self):
        s1 = "Presimulation finished"
        s2 = "Energy would change too much in virtual detector"
        s3 = "Energy would change too much in virtual detector     -1.582 MeV"

        self.assertEqual({
            "calculated": 0,
            "percentage": 0,
            "msg": "Presimulation finished"
        }, mcerd.parse_raw_output(s1))

        self.assertEqual({
            "msg": "Energy would change too much in virtual detector"
        }, mcerd.parse_raw_output(s2))

        self.assertEqual({
            "msg": "Energy would change too much in virtual detector     "
                   "-1.582 MeV",
        }, mcerd.parse_raw_output(s3))

    def test_pipeline(self):
        output = [
            "Initializing parameters.",
            "Reading input files.",
            "Beam ion: Z=17, M=34.969",
            "Starting simulation.",
            "Calculated 20 of 100 ions (20%)",
            "Presimulation finished",
            "Calculated 50 of 100 ions (50%)",
            "Energy would change too much in virtual detector",
            "Opening target file xyz",
            "atom: 1 1.0, con: 0.048 6.920",
            "angave 25.6119865",
            "bar"
        ]

        obs = TestObserver()
        rx.from_iterable(iter(output)).pipe(
            mcerd.MCERD.get_pipeline(100, "foo"),
        ).subscribe(obs)

        # Dictionaries should all contain the same keys
        self.assertTrue(all(
            obs.nexts[0].keys() == x.keys() for x in obs.nexts[1:])
        )
        # No errors in the given data set
        self.assertEqual([], obs.errs)
        # Stream should be completed
        self.assertEqual(["done"], obs.compl)
        # Input has been parsed into 7 items
        self.assertEqual(7, len(obs.nexts))

        self.assertEqual({
            "presim": True,
            "calculated": 0,
            "total": 0,
            "percentage": 0,
            "seed": 100,
            "name": "foo",
            "msg": "Initializing parameters.",
            "is_running": True
        }, obs.nexts[0])

        self.assertEqual({
            "presim": True,
            "msg": "Reading input files.\n"
                   "Beam ion: Z=17, M=34.969\n"
                   "Starting simulation.",
            "seed": 100,
            "name": "foo",
            "calculated": 0,
            "percentage": 0,
            "total": 0,
            "is_running": True
        }, obs.nexts[1])

        self.assertEqual({
            "presim": True,
            "msg": "",
            "seed": 100,
            "name": "foo",
            "calculated": 20,
            "percentage": 20,
            "total": 100,
            "is_running": True
        }, obs.nexts[2])

        self.assertEqual({
            "presim": False,
            "msg": "Opening target file xyz\n"
                   "atom: 1 1.0, con: 0.048 6.920\n"
                   "angave 25.6119865",
            "seed": 100,
            "name": "foo",
            "percentage": 100,
            "calculated": 50,
            "total": 100,
            "is_running": False
        }, obs.nexts[-1])


FAILURE_MSG = "This test is based on timing and may fail because the " \
              "code being tested ran faster or slower than expected. " \
              "Run this test again to see if the problem persists and " \
              "adjust the timing parameters if necessary."

if platform.system() == "Windows":
    # Add little extra to the sleep time on Windows as the TASKKILL call
    # seems to block until the process is fully killed.
    DEFAULT_SLEEP_TIME = 0.2
else:
    DEFAULT_SLEEP_TIME = 0.1


class TestTimeoutCheck(unittest.TestCase):
    def test_process_is_killed_after_timeout(self):
        ct = CancellationToken()
        with subprocess.Popen(["sleep", "1"]) as proc:
            res = mcerd.MCERD.timeout_check(proc, 0.01, ct)

            obs = TestObserver()
            res.subscribe(obs)
            time.sleep(DEFAULT_SLEEP_TIME)

            self.assertNotEqual(0, int(proc.poll()), msg=FAILURE_MSG)
            self.assertEqual([{
                "is_running": False,
                "msg": "Simulation timed out"
                }],
                obs.nexts, msg=FAILURE_MSG)
            self.assertTrue(ct.is_cancellation_requested(), msg=FAILURE_MSG)

    def test_timeout_check_returns_only_one_item_at_maximum(self):
        ct = CancellationToken()
        with subprocess.Popen(["sleep", "1"]) as proc:
            res = mcerd.MCERD.timeout_check(proc, 0.01, ct)

            obs = TestObserver()
            res.subscribe(obs)
            time.sleep(DEFAULT_SLEEP_TIME)

            self.assertEqual(1, len(obs.nexts), msg=FAILURE_MSG)

    def test_process_ending_before_timeout_does_not_change_outcome(self):
        ct = CancellationToken()
        with subprocess.Popen(
                ["echo", "hello"], stdout=subprocess.DEVNULL) as proc:
            res = mcerd.MCERD.timeout_check(proc, 0.01, ct)

        obs = TestObserver()
        res.subscribe(obs)
        time.sleep(DEFAULT_SLEEP_TIME)

        self.assertEqual(0, proc.poll(), msg=FAILURE_MSG)
        self.assertEqual([{
            "is_running": False,
            "msg": "Simulation timed out"
        }],
            obs.nexts, msg=FAILURE_MSG)
        self.assertTrue(ct.is_cancellation_requested(), msg=FAILURE_MSG)

    def test_process_is_not_killed_before_timeout(self):
        ct = CancellationToken()
        with subprocess.Popen(["sleep", "1"]) as proc:
            res = mcerd.MCERD.timeout_check(proc, 0.1, ct)

            obs = TestObserver()
            res.subscribe(obs)

            self.assertIsNone(proc.poll(), msg=FAILURE_MSG)
            self.assertEqual([], obs.nexts, msg=FAILURE_MSG)
            self.assertFalse(ct.is_cancellation_requested(), msg=FAILURE_MSG)


class TestCancellationCheck(unittest.TestCase):
    def test_requesting_cancellation_kills_the_process(self):
        ct = CancellationToken()
        with subprocess.Popen(["sleep", "1"]) as proc:
            res = mcerd.MCERD.cancellation_check(proc, 0.01, ct)

            obs = TestObserver()
            res.subscribe(obs)
            ct.request_cancellation()

            time.sleep(DEFAULT_SLEEP_TIME)
            self.assertNotEqual(0, int(proc.poll()), msg=FAILURE_MSG)
            self.assertEqual([{
                "is_running": False,
                "msg": "Simulation was stopped"
                }],
                obs.nexts, msg=FAILURE_MSG)

    def test_not_requesting_cancellation_lets_the_process_finish(self):
        ct = CancellationToken()
        with subprocess.Popen(["sleep", "0.1"]) as proc:
            res = mcerd.MCERD.cancellation_check(proc, 0.01, ct)

            obs = TestObserver()
            res.subscribe(obs)

            time.sleep(0.2)
            self.assertEqual(0, proc.poll(), msg=FAILURE_MSG)
            self.assertEqual([], obs.nexts, msg=FAILURE_MSG)

    def test_cancellation_check_returns_one_item_at_maximum(self):
        ct = CancellationToken()
        with subprocess.Popen(["sleep", "1"]) as proc:
            res = mcerd.MCERD.cancellation_check(proc, 0.01, ct)

            obs = TestObserver()
            res.subscribe(obs)

            time.sleep(0.25)
            ct.request_cancellation()
            time.sleep(0.25)

            self.assertEqual(1, len(obs.nexts), msg=FAILURE_MSG)

    def test_cancelling_after_process_ends_does_not_change_observed_values(
            self):
        ct = CancellationToken()
        with subprocess.Popen(["echo", "hello"], stdout=subprocess.DEVNULL) as \
                proc:
            res = mcerd.MCERD.cancellation_check(proc, 0.01, ct)

        obs = TestObserver()
        res.subscribe(obs)
        ct.request_cancellation()

        time.sleep(DEFAULT_SLEEP_TIME)
        self.assertEqual(0, proc.poll(), msg=FAILURE_MSG)
        self.assertEqual([{
            "is_running": False,
            "msg": "Simulation was stopped"
        }],
            obs.nexts, msg=FAILURE_MSG)

    def test_process_is_not_killed_immediately_after_cancellation(self):
        ct = CancellationToken()
        with subprocess.Popen(["sleep", "1"]) as proc:
            res = mcerd.MCERD.cancellation_check(proc, 0.05, ct)

            obs = TestObserver()
            res.subscribe(obs)
            ct.request_cancellation()

            self.assertIsNone(proc.poll(), msg=FAILURE_MSG)
            self.assertEqual([], obs.nexts, msg=FAILURE_MSG)


class TestRunningCheck(unittest.TestCase):
    def test_running_check_produces_dicts_with_running_status(self):
        with subprocess.Popen(["sleep", "0.1"]) as proc:
            res = mcerd.MCERD.running_check(proc, 0.01, 0.01)
            obs = TestObserver()
            res.subscribe(obs)

        time.sleep(0.05)
        self.assertLess(1, len(obs.nexts), msg=FAILURE_MSG)
        for item in obs.nexts[:-1]:
            self.assertEqual({
                "is_running": True
            }, item)

        self.assertEqual({
                "is_running": False
        }, obs.nexts[-1], msg=FAILURE_MSG)


class TestIsRunning(unittest.TestCase):
    def test_is_running_returns_false_if_process_is_not_running(self):
        with subprocess.Popen(
                ["echo", "hello"], stdout=subprocess.DEVNULL) as proc:
            pass
        self.assertFalse(mcerd.MCERD.is_running(proc), msg=FAILURE_MSG)

    def test_is_running_returns_true_if_process_is_running(self):
        with subprocess.Popen(["sleep", "0.1"]) as proc:
            self.assertTrue(mcerd.MCERD.is_running(proc), msg=FAILURE_MSG)

    def test_is_running_raises_error_if_process_finishes_with_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir, "foo")
            with subprocess.Popen(
                    ["ls", str(p)], stderr=subprocess.DEVNULL) as proc:
                pass
            self.assertRaises(
                subprocess.SubprocessError,
                lambda: mcerd.MCERD.is_running(proc))


if __name__ == '__main__':
    unittest.main()
