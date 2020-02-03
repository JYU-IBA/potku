# coding=utf-8
"""
Created on 2.2.2020

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

import abc

from PyQt5 import QtWidgets


def switch_buttons(func, button_a, button_b):
    """Decorator for that switches the status of two buttons.

    First button is switched before the execution of a function and
    second one is switched after the execution.
    """
    def wrapper(*args, **kwargs):
        button_a.setEnabled(not button_a.isEnabled())
        func(*args, **kwargs)
        button_b.setEnabled(not button_b.isEnabled())
    return wrapper


class QtOABCMeta(type(QtWidgets.QWidget), abc.ABCMeta):
    """A common metaclass for ABCs and QWidgets.

    QWidget has the metaclass 'sip.wrappertype' which causes a conflict
    in multi-inheritance with an ABC.

    Originally this was intended as a metaclass for QWidgets and Observers
    but since Observers are no longer ABCs, this class may not be needed.
    """
    pass