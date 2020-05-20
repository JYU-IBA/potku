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
"""

__author__ = "Juhani Sundell"
__version__ = "2.0"

import weakref
import sys

import rx.operators as ops


class ProgressReporter:
    """ProgressReporter allows various processes to report their progress.
    Reporting is done by calling the report function with a value that
    marks the current progress.

    Reporting can be divided into sub-tasks by using a ProgressReporter returned
    by get_sub_reporter function.

    Generally Potku assumes that each ProgressReporter goes from 0 to 100 but
    this is not enforced in anyway. Having an universal reporting scheme makes
    it easier to scale the values of sub-reporters.
    """

    def __init__(self, progress_callback):
        """Initializes a new ProgressReporter.

        Args:
            progress_callback: function that is invoked when progress is
                reported. This could for example set the value of a progress
                bar.
        """
        self.__progress_callback = progress_callback

    def report(self, value):
        """Reports the value of progress by invoking the progress
        callback.

        Args:
            value: progress value to report
        """
        self.__progress_callback(value)

    def get_sub_reporter(self, progress_callback):
        """Returns a new instance of ProgressReporter that calls the report
        function of this ProgressReporter with the value returned by the
        given callback function.

        Typically the progress_callback of a sub-reporter is in the form of:
            base + coef * x,
        where 'base' is the starting value, 'coef' is time it takes to
        process the sub-task relative to main task (number between 0.0 and
        1.0) and 'x' is the value of progress to be reported.

        Args:
            progress_callback: function that is called when the new
                ProgressReporter reports progress
        """
        return ProgressReporter(
            lambda value: self.report(progress_callback(value)))


class Observable:
    """Observables are objects that publish messages to subscribed
    observers by invoking their receive method.

    This is a simple implementation of the Observer pattern. If an
    Observable is going to report about some internal state or a
    mutable value, it is up to the Observable to lock
    and/or clone necessary resources.

    Only a weak reference to an Observer is stored. If the Observer
    is deleted, the Observable will no longer keep it alive.
    """
    __slots__ = "__observer_refs",

    def __init__(self):
        """Initializes a new observable.
        """
        # Refs are stored in a list. If there is ever a need to have
        # a large number of observers on a single observable, consider
        # implementing a way to hash them all into a set.
        self.__observer_refs = []

    def subscribe(self, observer):
        """Subscribes an observer to the observable.

        Raises TypeError if the observer is not an instance
        of the Observer class or it is not weakly referencable.

        Same observer can subscribe multiple times.

        Args:
            observer: object that is an instance of the
                      Observer class
        """
        if isinstance(observer, Observer):
            ref = weakref.ref(observer)
            self.__observer_refs.append(ref)
        else:
            raise TypeError("Observable expects the subscriber to be an "
                            "instance of Observer class.")

    def unsubscribe(self, observer):
        """Unsubscribes the observer from the Observable.

        The observer will no longer receive published messages
        from the observable. Raises TypeError if weak reference
        to the observer cannot be made.

        Args:
            observer: observer to unsubscribe
        """
        ref = weakref.ref(observer)
        try:
            self.__observer_refs.remove(ref)
        except ValueError:
            # Observer was not in the list of observers,
            # nothing to do.
            pass

    def on_error(self, err):
        """Publishes an error message to Observers.

        Args:
            err: error message
        """
        self.__publish(lambda obs: obs.on_error(err))

    def on_completed(self, msg=None):
        """Notifies the Observers that the Observable has completed its
        process.

        Args:
            msg: [optional] message to Observers
        """
        self.__publish(lambda obs: obs.on_completed(msg))

    def on_next(self, msg):
        """Publishes a status update to Observers.

        Args:
            msg: message to Observers
        """
        self.__publish(lambda obs: obs.on_next(msg))

    def __publish(self, func):
        """Publishes a message to all observers.

        Args:
            func: function that invokes the observer's callback
                  function
        """
        def __inner_pub(weak_ref):
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
                func(observer)
                return True
            return False

        # Iterate over the references, publishing the message to
        # existing observers and removing those that do not exist.
        # Filtered results are assigned to a slice of the existing list
        # to avoid potential problems with multiple references to the
        # refs list.
        self.__observer_refs[:] = [ref for ref in self.__observer_refs
                                   if __inner_pub(ref)]

    def get_observer_count(self):
        """Returns the number of observers currently subscribed to the
        Observable.
        """
        # Only return the number of observers that still exist
        return sum(1 for ref in self.__observer_refs if ref())


class Observer:
    """Observer class receives messages from an Observable.

    This class was originally intended to be an ABC. This idea
    was dropped as Potku uses Python 3.6 in which ABC's do not
    have a __slots__ attribute. Many classes in Potku use __slots__
    to reduce memory footprint so inheriting from an ABC would
    render the use of __slots__ useless.

    Observer class does not define '__weakref__' in its own
    __slots__. It is up to the inheriting class to add the
    definition if it uses __slots__.
    """
    __slots__ = ()

    def on_error(self, err):
        """Observable invokes this method to inform that it has
        encountered some exception and is not able to continue
        operating.

        Args:
            err: error message from the Observable
        """
        raise NotImplementedError

    def on_next(self, msg):
        """Observable invokes this method so the Observer
        can receive a status update.

        Args:
            msg: message from the Observable
        """
        raise NotImplementedError

    def on_completed(self, msg=None):
        """Observable invokes this method to inform that it has
        completed its operation.

        Args:
            msg: [optional] message from the Observable
        """
        raise NotImplementedError


def get_printer(completed_msg=""):
    """Returns an rx.operator that prints the observed item to console.

    Args:
        completed_msg: message shown when the observable completes.
    """
    return ops.do_action(
        on_next=print,
        on_error=lambda x: print("Error:", x, file=sys.stderr),
        on_completed=lambda: print("Completed:", completed_msg)
    )


def _flag_start_end(start_condition, end_condition):
    """Helper operator that adds two boolean flags to the item depending on
    if the conditiotions are met.
    """
    return ops.scan(
        lambda acc, x: (
            x,
            start_condition(x) or acc[1] and not acc[2],
            end_condition(x)
        ), seed=(None, False)
    )


def reduce_while(reducer, start_from, end_at):
    """Reduces items into a single item while a condition is met.

    Args:
        reducer: function that takes as an input the last output of itself and
            an item and returns a combined result.
        start_from: function that takes an item and returns a boolean
        end_at: function that takes an item and returns a boolean
    """
    return ops.pipe(
        _flag_start_end(start_from, end_at),
        ops.scan(lambda acc, x: (
            reducer(acc[0], x[0]) if acc[1] else x[0],
            x[1] and not x[2]
        )),
        ops.filter(lambda x: not x[1]),
        ops.map(lambda x: x[0])
    )
