# coding=utf-8
"""
Created on 11.08.2022

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

Concurrency module provides helper functions and classes for asynchronous,
multithreaded or multiprocessing operations.
"""
__author__ = "Timo Leppälä"
__version__ = "1.0"

import json


class ConfigManager:

    config_data = None

    def __init__(self):
        if ConfigManager.config_data == None:
            ConfigManager.config_data = {}
            ConfigManager.config_file = None

    def load_config(self, config_file):
        ConfigManager.config_data = {}
        ConfigManager.config_file = config_file
        try:
            with open(config_file,"r") as cfgfile:
                ConfigManager.config_data = json.load(cfgfile)
        except (json.JSONDecodeError, OSError, KeyError, AttributeError) as e:
            msg = f"Failed to read data from configuration file " \
                  f"file {config_file}: {e}."

    def set_config_file(self, filename):
        ConfigManager.config_file = filename

    def get_config(self, path=None):
        return ConfigManager.config_data

    def set_simulation(self, simulation):
        ConfigManager.simulation = simulation

    def get_node(self, path):
        node_path = ConfigManager.config_data
        if path == None:
            return ConfigManager.config_data
        if  isinstance(path, str):
            return ConfigManager.config_data[path]
        for part in path:
            node_path = node_path[part]
        return node_path

    def save(self):
        self.update_simulation()


        config_file = ConfigManager.config_file
        if config_file != None:
            try:
                with open(config_file, "w") as cfgfile:
                    cfgfile.write(json.dumps(ConfigManager.config_data, indent=4))
            except (json.JSONDecodeError, OSError, KeyError, AttributeError) as e:
                msg = f"Failed to write data to configuration file " \
                      f"file {config_file}: {e}."

    def add_to_array(self, path, item):
        self.get_node(path).append(item)

    def add_element(self, path, key, item):
        ConfigManager.config_data[self.get_node(path)][key]=item

    def read_simulation(self):
        ConfigManager.config_data=ConfigManager.simulation.get_json_content()

    def update_simulation(self):
        ConfigManager.config_data=ConfigManager.simulation.get_json_content()

