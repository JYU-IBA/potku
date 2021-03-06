# coding=utf-8
"""
Created on 15.04.2020

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
__author__ = "Juhani Sundell \n Tuomas Pitkänen"
__version__ = "2.0"

from typing import List
from typing import NamedTuple
from typing import Dict
from typing import Any
from typing import Union
from typing import Tuple
from typing import Set

# This is a collection of base classes for various backend components that share
# similar functions. Logically these base classes would be ABCs, but in
# Python3.6, ABC does not have a __slots__ declaration, which would make
# __slots__ useless in inheriting classes. If Potku is upgraded to a higher
# version of Python, these classes should be made into ABCs.

# Type hint aliases that can be imported to other modules
ElemSimList = List["ElementSimulation"]
Range = Tuple[Union[float, int], Union[float, int]]
StrTuple = Tuple[str, str]

# Helper type hint for energy spectrum data
Espe = List[Tuple[float, float]]


class ElementSimulations(NamedTuple):
    running_simulations: ElemSimList
    finished_simulations: ElemSimList
    running_optimizations: ElemSimList
    finished_optimizations: ElemSimList


class ElementSimulationContainer:
    """Base class for objects that maintain a collection of ElementSimulation
    objects.
    """
    __slots__ = ()

    def get_active_simulations(self) -> ElementSimulations:
        """Returns simulations that are either running, finished or are being
        used in optimization. Simulations that have not yet started, are not
        included.
        """
        return ElementSimulations(
            self.get_running_simulations(),
            self.get_finished_simulations(),
            self.get_running_optimizations(),
            self.get_finished_optimizations()
        )

    def get_running_simulations(self) -> ElemSimList:
        """Returns a list of currently running ElementSimulations.
        """
        raise NotImplementedError

    def get_finished_simulations(self) -> ElemSimList:
        """Returns a list of ElementSimulations that have finished.
        """
        raise NotImplementedError

    def get_running_optimizations(self) -> ElemSimList:
        """Returns a list of ElementSimulations that are being used in a
        currently running optimization.
        """
        raise NotImplementedError

    def get_finished_optimizations(self) -> ElemSimList:
        """Returns a list of ElementSimulations that have been used in a
        finished optimization.
        """
        raise NotImplementedError


class Serializable:
    """Base class for objects that can be serialized into a file and
    deserialized back.
    """
    __slots__ = ()

    @classmethod
    def from_file(cls, *args, **kwargs) -> "Serializable":
        """Deserializes an object from file.
        """
        raise NotImplementedError

    def to_file(self, *args, **kwargs):
        """Serializes the object into a file.
        """
        raise NotImplementedError


class AdjustableSettings:
    """Base class for objects that contain a collection of settings that can
    be edited (in a GUI for example).
    """
    __slots__ = ()

    def _get_attrs(self) -> Set[str]:
        """Returns names of attributes that can be adjusted."""
        # if settings were properties, this could be done using reflection
        raise NotImplementedError

    def _get_setting_value(self, attr) -> Any:
        value = getattr(self, attr)
        if isinstance(value, AdjustableSettings):
            return value.get_settings()
        return value

    def _set_setting_value(self, attr, value) -> None:
        attr_val = getattr(self, attr)
        if isinstance(attr_val, AdjustableSettings):
            attr_val.set_settings(**value)
        else:
            setattr(self, attr, value)

    def get_settings(self) -> Dict[str, Any]:
        """Returns names and values of settings that can be adjusted.
        Recursively returns names and values for objects that inherit
        AdjustableSettings.
        """
        return {
            attr: self._get_setting_value(attr)
            for attr in self._get_attrs()
        }

    def set_settings(self, **kwargs) -> None:
        """Sets the values of the settings. Recursively sets values for objects
        that inherit AdjustableSettings."""
        allowed_attrs = self._get_attrs()
        for k, v in kwargs.items():
            if k in allowed_attrs:
                self._set_setting_value(k, v)


class MCERDParameterContainer:
    """Base class for objects that contain parameters that are used in MCERD
    simulations.
    """
    __slots__ = ()

    def get_mcerd_params(self) -> Union[List, str]:
        """Returns either a single string or a list of strings that contain
        parameters used by MCERD.
        """
        raise NotImplementedError
