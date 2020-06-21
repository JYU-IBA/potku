# coding=utf-8
"""
Created on 8.2.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""

__author__ = "Juhani Sundell"
__version__ = "2.0"

import tempfile
import random
import rx

import modules.masses as masses

from pathlib import Path

from modules.detector import Detector
from modules.recoil_element import RecoilElement
from modules.element import Element
from modules.element_simulation import ElementSimulation
from modules.beam import Beam
from modules.target import Target
from modules.simulation import Simulation
from modules.run import Run
from modules.point import Point
from modules.layer import Layer
from modules.measurement import Measurement
from modules.global_settings import GlobalSettings
from modules.observing import Observer
from modules.request import Request


# This module can be used to generate various helper objects for testing
# purposes.

_TEMP_DIR = Path(tempfile.TemporaryDirectory().name).resolve()


def get_detector() -> Detector:
    """Returns a Detector object that has the default foils (3 circular,
    1 rectangular).
    """
    path = Path(_TEMP_DIR, ".detector")
    mesu = Path(_TEMP_DIR, "mesu")

    d = Detector(path, mesu, save_on_creation=False)
    return d


def get_element(randomize=False, isotope_p=0.5, amount_p=0.5,
                symbol="He", **kwargs) -> Element:
    """Returns either a random Element or a Helium element.

    Args:
        randomize: whether a random Element is returned
        isotope_p: the likelihood of the random Element having an isotope
        amount_p: likelihood that the Element is provided a random amount
            argument.
        symbol: element's symbol as a string for a non-randomized element
        kwargs: keyword arguments passed down to non-randomized element

    Return:
        Element object.
    """
    if randomize:
        symbol = random.choice(list(masses._ISOTOPES.keys()))
        if random.random() < isotope_p:
            isotope = random.choice(
                masses.get_isotopes(symbol, filter_unlikely=False))["number"]
        else:
            isotope = None

        if random.random() < amount_p:
            amount = random.uniform(0, 100)
        else:
            amount = 0

        return Element(symbol, isotope=isotope, amount=amount)

    return Element(symbol, **kwargs)


def get_beam() -> Beam:
    """Returns a default Beam object.
    """
    return Beam()


def get_target() -> Target:
    """Returns a default Target object.
    """
    return Target()


def get_recoil_element(recoil_widget=None) -> RecoilElement:
    """Returns a RecoilElement object.
    """
    re = RecoilElement(get_element(), [
        Point((1, 1)),
        Point((2, 2)),
    ], "red")
    re.widgets.append(recoil_widget)
    return re


def get_run() -> Run:
    """Returns a Run object.
    """
    return Run(get_beam())


def get_element_simulation(request=None, recoil_widget=None) \
        -> ElementSimulation:
    """Returns an ElementSimulation object.
    """
    if request is None:
        request = get_request()

    return ElementSimulation(
        _TEMP_DIR, request, [get_recoil_element(recoil_widget=recoil_widget)],
        save_on_creation=False)


def get_simulation(request=None) -> Simulation:
    """Returns a Simulation object.
    """
    if request is None:
        request = get_request()

    return Simulation(
        _TEMP_DIR / "foo.simulation", request, save_on_creation=False,
        enable_logging=False)


def get_measurement(request=None) -> Measurement:
    """Returns a Measurement object.
    """
    if request is None:
        request = get_request()

    return Measurement(
        request, _TEMP_DIR / "mesu", save_on_creation=False,
        enable_logging=False)


def get_layer(element_count=1, randomize=False) -> Layer:
    """Returns a Layer object.

    Args:
        element_count: how many Elements will the layer contain
        randomize: whether the Elements are randomized

    Return:
        Layer object
    """
    return Layer(
        "layer1",
        [get_element(randomize=randomize, amount_p=1.0)
         for _ in range(element_count)], 1, 2)


def get_global_settings() -> GlobalSettings:
    """Returns a GlobalSettings object.
    """
    return GlobalSettings(
        config_dir=_TEMP_DIR, save_on_creation=False)


def get_request() -> Request:
    """Returns a MockRequest object.

    This is done to avoid lengthy file writing operations when a real
    Request is initialized
    """
    return Request(_TEMP_DIR, "request", get_global_settings(),
                   save_on_creation=False, enable_logging=False)


class MockSelection:
    # Selection class should be refactored so that it contains no Qt or
    # matplotlib references. Until then, this class is used
    def __init__(self):
        self.element = get_element()
        self.element_scatter = get_element(symbol="Cl")
        self.type = "RBS"
        self.weight_factor = 1.0


def get_selection() -> "MockSelection":
    return MockSelection()


class TestObserver(Observer):
    """Observer that appends messages it receives to its collections.
    """
    def __init__(self):
        self.nexts = []
        self.errs = []
        self.compl = []

    def on_next(self, msg):
        self.nexts.append(msg)

    def on_error(self, err):
        self.errs.append(err)

    def on_completed(self, msg="done"):
        self.compl.append(msg)


def get_mcerd_stream() -> rx.Observable:
    """Returns a single item stream.
    """
    return rx.from_iterable([{"is_running": False, "msg": ""}])

