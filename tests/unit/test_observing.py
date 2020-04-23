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

from modules.observing import Observable
from modules.observing import Observer
from modules.observing import ProgressReporter


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

        # If the sub unsubscribes, messages do not get through
        pub.unsubscribe(sub)
        pub.on_next("bar")
        self.assertEqual(["foo"], sub.nexts)

    def test_multisubscriptions(self):
        pub1 = Pub()
        pub2 = Pub()

        sub1 = Sub()
        sub2 = Sub()

        # Subscriber can receive messages from multiple observables and
        # publisher can send messages to multiple subscribers
        pub1.subscribe(sub1)
        pub1.subscribe(sub2)
        pub2.subscribe(sub1)
        pub2.subscribe(sub2)

        pub1.on_next("hello")
        pub2.on_next("bonjour")

        self.assertEqual(["hello", "bonjour"], sub1.nexts)
        self.assertEqual(sub1.nexts, sub2.nexts)

        # Subscribing twice to the same publisher means messages are received
        # twice
        pub1.subscribe(sub1)
        pub1.on_complete("done")
        self.assertEqual(["done", "done"], sub1.compl)
        self.assertEqual(["done"], sub2.compl)

    def test_weakrefs(self):
        """Observers are weakly referenced so they should be removed when
        they no longer exist"""
        pub = Pub()
        sub = Sub()

        pub.subscribe(sub)
        self.assertEqual(1, pub.get_observer_count())

        # Store a reference to sub's nexts list so and delete sub so we can
        # check that the list stays empty
        nexts = sub.nexts
        del sub

        # Observer count is 0 and nothing happens when the publisher tries to
        # publish
        self.assertEqual(0, pub.get_observer_count())
        pub.on_next("are you still there?")
        self.assertEqual([], nexts)

        # Also if the Sub is only initialized in the context of the subscribe
        # function, observer count stays at 0
        pub.subscribe(Sub())
        self.assertEqual(0, pub.get_observer_count())

    def test_unreferenceable(self):
        """It must be possible to make a weak reference to the Observer"""
        class Unreffable(Observer):
            # this has no __weakref__ attribute in its slots
            __slots__ = ()

        pub = Pub()
        unr = Unreffable()
        self.assertRaises(TypeError, lambda: pub.subscribe(unr))
        self.assertRaises(TypeError, lambda: pub.unsubscribe(unr))

        self.assertEqual(0, pub.get_observer_count())

        # An object that has '__weakref__' in its slots can be an observer
        class Reffable(Observer):
            __slots__ = "__weakref__",

        ref = Reffable()
        pub.subscribe(ref)
        self.assertEqual(1, pub.get_observer_count())

    def test_default_observer(self):
        """If no implementation for Observers functions are made,
        NotImplementedErrors are raised.
        """
        class Obs(Observer):
            pass

        self.assertRaises(NotImplementedError, lambda: Obs().on_complete(""))
        self.assertRaises(NotImplementedError, lambda: Obs().on_error(""))
        self.assertRaises(NotImplementedError, lambda: Obs().on_next(""))


class TestProgressReporting(unittest.TestCase):
    def setUp(self):
        self.x = 0

    def test_progress_reporting(self):
        self.assertEqual(0, self.x)

        def increment(value):
            self.x += value

        reporter = ProgressReporter(increment)
        reporter.report(1)
        self.assertEqual(1, self.x)

    def test_subprogress(self):
        self.assertEqual(0, self.x)

        def increment(value):
            self.x += value

        reporter = ProgressReporter(increment)
        sub_reporter1 = reporter.get_sub_reporter(lambda x: x / 2)
        sub_reporter2 = sub_reporter1.get_sub_reporter(lambda x: x / 2)

        reporter.report(1)
        self.assertEqual(1, self.x)

        sub_reporter1.report(1)
        self.assertEqual(1.5, self.x)

        sub_reporter2.report(1)
        self.assertEqual(1.75, self.x)

        # Callback still maintain references to parent progresses so deleting
        # these does not matter
        del reporter
        del sub_reporter1
        del increment

        sub_reporter2.report(1)
        self.assertEqual(2, self.x)

    def test_bad_values(self):
        reporter = ProgressReporter(int)
        sub_reporter = reporter.get_sub_reporter(list)

        self.assertRaises(TypeError, lambda: sub_reporter.report(1))


if __name__ == "__main__":
    unittest.main()
