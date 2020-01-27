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

TODO
"""

__author__ = "Juhani Sundell"
__version__ = ""    # TODO

import abc
import weakref


class ABCReporter(abc.ABC):
    """Base abstract class from which all progress reporters should derive.

    Reporters report the progress of a single task and can be used to for
    example update a value of a progress bar.
    """
    def __init__(self, progress_callback):
        """Inits a ProgressReporter.

        Args:
            progress_callback: function that will be called, when the
                               reporter reports progress
        """
        self.progress_callback = progress_callback

    @abc.abstractmethod
    def report(self, value):
        """Method that is used to invoke the callback.

        Args:
            value: progress value to report.
        """
        pass


class ProgressReporter(ABCReporter):
    """A vanilla ProgressReporter that merely invokes the progress
    callback and does not care about thread safety."""

    def report(self, value):
        """Reports the value of progress by invoking the progress
        callback.

        Args:
            value: progress value to report
        """
        self.progress_callback(value)

# TODO thread safe reporter for GUI purposes


class Observable(abc.ABC):
    """Observables are objects that publish messages to subscribed
    observers by invoking their receive method.

    This is a simple implementation of the Observer pattern. If an
    Observable is going to report about some internal state or a
    mutable value, it is up to the Observable to lock
    and/or clone necessary resources.

    Only a weak reference to an Observer is stored. If the Observer
    is deleted, the Observable will no longer keep it alive.
    """
    __slots__ = "refs"

    def __init__(self):
        """Initializes a new observable.
        """
        # Refs are stored in a list. If there is ever a need to have
        # a large number of observers on a single observable, consider
        # implementing a way to hash them all into a set.
        self.refs = []

    def subscribe(self, observer):
        """Subscribes an observer to the observable.

        Raises TypeError if the observer is not an instance
        of the Observer class.

        Same observer can subscribe multiple times.

        Args:
            observer: object that is an instance of the
                      Observer class
        """
        if isinstance(observer, Observer):
            # TODO what if no weakref cannot be created
            ref = weakref.ref(observer)
            self.refs.append(ref)
            # TODO this could also return some means
            #      to unsubscribe
        else:
            raise TypeError

    def unsubscribe(self, observer):
        """Unsubscribes the observer from the Observable.

        The observer will no longer receive published messages
        from the observable.

        Args:
            observer: observer to unsubscribe
        """
        ref = weakref.ref(observer)
        try:
            self.refs.remove(ref)
        except ValueError:
            # Observer was not in the list of observers,
            # nothing to do.
            pass

    def publish(self, msg):
        """Publishes a message to all observers.

        Args:
            msg: message to publish
        """
        def __publish(weak_ref):
            """This inner method will publish the message to an
            observer if the observer is not None (i.e. it still
            exists).

            Args:
                weak_ref: weak reference to an observer

            Return:
                True if observer is not None, False otherwise.
            """
            observer = weak_ref()
            if observer is not None:
                observer.receive(msg)
                return True
            return False

        # Iterate over the references, publishing the message to
        # existing observers and removing those that do not exist.
        self.refs = [ref for ref in self.refs if __publish(ref)]


class Observer: # TODO check the conflict between this and
                #      SimulationControls, which prevents this
                #      from being an ABC
    """Observer class receives messages from an Observable.
    """
    #@abc.abstractmethod
    def receive(self, msg):
        """Observable invokes this method so the Observer
        can receive the message.

        Args:
            msg: message from the Observable
        """
        pass


if __name__ == "__main__":
    # For testing purposes
    # TODO formulate this to a proper unittest
    import gc

    class Pub(Observable):
        pass

    class Sub(Observer):
        def __init__(self, idx=0):
            self.idx = idx

        def receive(self, msg):
            print(self.idx, "Received:", msg)

    pub = Pub()
    sub = Sub()

    pub.subscribe(sub)
    pub.publish("hello")

    pub.unsubscribe(sub)
    pub.publish("hello again")

    pub.unsubscribe(sub)
    pub.subscribe(sub)
    pub.subscribe(sub)

    pub.publish("howdy y'all")
    del sub
    gc.collect()

    pub.publish("are you still there")
