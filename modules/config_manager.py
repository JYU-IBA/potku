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

config_file = "tl_test_config.mccfg"

class ConfigManager:

    config_data = None

    def __init__(self):
        if ConfigManager.config_data == None:
            print("ConfigManager init: load config")
            self.load_config()

    def load_config(self):
        ConfigManager.config_data = {}
        # try:
        #     with open(config_file,"r") as config_file:
        #         config_data = json.load(config_file)
        # except (json.JSONDecodeError, OSError, KeyError, AttributeError) as e:
        #     msg = f"Failed to read data from configuration file " \
        #           f"file {config_file}: {e}."

    def get_config(self, path=None):
        return ConfigManager.config_data

    def get_node(self, path):
        print(f'get_node: {path}')
        node_path = ConfigManager.config_data
        if path == None:
            return ConfigManager.config_data
        if  isinstance(path, str):
            return ConfigManager.config_data[path]
        for part in path:
            node_path = node_path[part]
        return node_path

    def save(self):
        print("Saving configuration:")
        print(json.dumps(ConfigManager.config_data))

    def add_to_array(self, path, item):
        print(f'Add to array: {path}:{item}')
        print(f'node: {self.get_node(path)}')
        self.get_node(path).append(item)

    def add_element(self, path, key, item):
        print(f'Add element ({key}:{element} to {path}')
        ConfigManager.config_data[self.get_node(path)][key]=item

    def read_simulation(self, simulation):
        ConfigManager.config_data=simulation.get_json_content()
        print(f"Read_simulation")
        print(json.dumps(ConfigManager.config_data, indent=4))
        pass
