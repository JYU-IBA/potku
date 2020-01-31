# coding=utf-8
"""
Created on 31.1.2020

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
"""

__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import unittest
import gc

from modules.observing import Observable
from modules.observing import Observer


# Mock observable and observer
class Pub(Observable):
    """Mock Observable"""
    pass


class Sub(Observer):
    """Mock Observer that appends messages it receives to its collections."""
    def __init__(self):
        self.errs = []
        self.nexts = []
        self.compl = []

    def on_complete(self, msg):
        self.compl.append(msg)

    def on_error(self, err):
        self.errs.append(err)

    def on_next(self, msg):
        self.nexts.append(msg)


# TODO add tests for multithreaded system
# TODO test with an object that cannot be weakly referenced

class TestObserving(unittest.TestCase):
    def test_subscription(self):
        """Testing subscbring and unsubscribing"""
        pub = Pub()
        n = 10

        self.assertEqual(0, pub.get_observer_count())

        sub = Sub()
        pub.subscribe(sub)
        self.assertEqual(1, pub.get_observer_count())

        pub.unsubscribe(sub)
        self.assertEqual(0, pub.get_observer_count())

        # If an unsubscribed sub tries to unsubscribe, nothing
        # happens
        pub.unsubscribe(sub)
        self.assertEqual(0, pub.get_observer_count())

        # Same sub can subscribe multiple times
        for i in range(n):
            pub.subscribe(sub)

        self.assertEqual(n, pub.get_observer_count())

        # Multiple references to same sub are removed one by one
        pub.unsubscribe(sub)
        self.assertEqual(n - 1, pub.get_observer_count())

        # TypeError is raised if sub is not an Observer
        self.assertRaises(TypeError, lambda: pub.subscribe(1))

    def test_publishing(self):
        """Tests that the publisher uses the correct callbacks to publish
        messages."""
        pub = Pub()
        sub = Sub()

        pub.subscribe(sub)

        self.assertEqual([], sub.nexts)
        self.assertEqual([], sub.compl)
        self.assertEqual([], sub.errs)

        pub.on_next("foo")
        pub.on_complete("bar")
        pub.on_error("kissa istuu")

        self.assertEqual(["foo"], sub.nexts)
        self.assertEqual(["bar"], sub.compl)
        self.assertEqual(["kissa istuu"], sub.errs)

        # Subscriber can receive messages from multiple observables
        pub2 = Pub()
        pub2.subscribe(sub)

        pub.on_next("hello")
        pub2.on_next("hello again")

        self.assertEqual(["foo", "hello", "hello again"],
                         sub.nexts)

    def test_weakrefs(self):
        """Observers are weakly referenced so they should be removed when
        they no longer exist"""
        pub = Pub()
        sub = Sub()

        pub.subscribe(sub)
        self.assertEqual(1, pub.get_observer_count())

        del sub
        gc.collect()

        self.assertEqual(0, pub.get_observer_count())

        # Nothing happens when the publisher tries to publish something
        pub.on_next("hello")
        pub.on_error("are you there still there")
        pub.on_complete("are you there yet")


if __name__ == "__main__":
    unittest.main()
