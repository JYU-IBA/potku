# coding=utf-8
"""
Created on 27.10.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, Tuomas Pitkänen

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

__author__ = "Tuomas Pitkänen"
__version__ = "2.0"

import json
import logging
import time

from pathlib import Path
from typing import Set

from modules.base import AdjustableSettings, Serializable


# TODO: Create unit tests / copy unit tests from measurement
# TODO: Give a class name that is not already in use?
class Profile(AdjustableSettings, Serializable):
    """Profile class for measurement profile data."""

    __slots__ = "name", "description", "modification_time",\
                "reference_density", "number_of_depth_steps",\
                "depth_step_for_stopping", "depth_step_for_output",\
                "depth_for_concentration_from", "depth_for_concentration_to",\
                "reference_cut",\
                "channel_width", "number_of_splits", "normalization"

    def __init__(self, name="Default", description="",
                 modification_time=None, reference_density=3.0,
                 number_of_depth_steps=150, depth_step_for_stopping=10,
                 depth_step_for_output=10, depth_for_concentration_from=200,
                 depth_for_concentration_to=400, channel_width=0.025,
                 reference_cut="",
                 number_of_splits=10, normalization="First"):
        """Initializes a profile."""
        self.name = name
        self.description = description
        if modification_time is None:
            self.modification_time = time.time()
        else:
            self.modification_time = modification_time

        self.reference_density = reference_density
        self.number_of_depth_steps = number_of_depth_steps
        self.depth_step_for_stopping = depth_step_for_stopping
        self.depth_step_for_output = depth_step_for_output
        self.depth_for_concentration_from = depth_for_concentration_from
        self.depth_for_concentration_to = depth_for_concentration_to
        self.reference_cut = reference_cut
        self.channel_width = channel_width
        self.number_of_splits = number_of_splits
        self.normalization = normalization

    @classmethod
    def from_file(cls, profile_file: Path) -> "Profile":
        # TODO: Copy from measurement.from_file (lines 502 to 556)
        try:
            with profile_file.open("r") as prof_file:
                obj_prof = json.load(prof_file)

            prof_gen = {
                "name": obj_prof["general"]["name"],
                "description": obj_prof["general"]["description"],
                "modification_time": obj_prof["general"][
                    "modification_time_unix"]
            }
            depth = obj_prof["depth_profiles"]
            channel_width = obj_prof["energy_spectra"]["channel_width"]
            comp = obj_prof["composition_changes"]

        except (OSError, KeyError, AttributeError, json.JSONDecodeError) as e:
            logging.getLogger("request").error(
                f"Failed to read settings from file {profile_file}: {e}"
            )
            # TODO: Initialize a request.default_profile elsewhere and
            #       use its values here, or just let it crash?
            raise NotImplementedError

        return cls(channel_width=channel_width, **prof_gen, **depth, **comp)

    def to_file(self, profile_file: Path):
        """Write a .profile file.

        Args:
            profile_file: Path to .profile file.
        """
        obj_profile = {
            "general": {},
            "depth_profiles": {},
            "energy_spectra": {},
            "composition_changes": {}
        }

        obj_profile["general"]["name"] = self.name
        obj_profile["general"]["description"] = \
            self.description
        obj_profile["general"]["modification_time"] = \
            time.strftime("%c %z %Z", time.localtime(time.time()))
        obj_profile["general"]["modification_time_unix"] = \
            self.modification_time

        obj_profile["depth_profiles"]["reference_density"] = \
            self.reference_density
        obj_profile["depth_profiles"]["number_of_depth_steps"] = \
            self.number_of_depth_steps
        obj_profile["depth_profiles"]["depth_step_for_stopping"] = \
            self.depth_step_for_stopping
        obj_profile["depth_profiles"]["depth_step_for_output"] = \
            self.depth_step_for_output
        obj_profile["depth_profiles"]["depth_for_concentration_from"] = \
            self.depth_for_concentration_from
        obj_profile["depth_profiles"]["depth_for_concentration_to"] = \
            self.depth_for_concentration_to
        obj_profile["energy_spectra"]["channel_width"] = self.channel_width
        obj_profile["composition_changes"]["reference_cut"] = self.reference_cut
        obj_profile["composition_changes"]["number_of_splits"] = \
            self.number_of_splits
        obj_profile["composition_changes"]["normalization"] = self.normalization

        with profile_file.open("w") as file:
            json.dump(obj_profile, file, indent=4)

    def _get_attrs(self) -> Set[str]:
        return set(self.__slots__)
