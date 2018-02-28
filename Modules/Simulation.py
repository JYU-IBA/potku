# coding=utf-8
"""
Created on 26.2.2018
Updated on 28.2.2018
"""
__author__ = ""
__versio__ = "2.0"

import os
import platform
import subprocess


class Simulation:

    def __init__(self, command_file_path):
        """Inits Simulation.

        Args:
            command_file_path: Full path of where simulation command file is located.
        """
        self.bin_dir = "%s%s%s" % ("external", os.sep, "Potku-bin")
        # TODO: Windows and Mac commands
    #    self.command_win = "cd " + self.bin_dir + " && mcerd.exe " + command_file_path
        self.command_unix = "cd " + self.bin_dir + " && ./mcerd " + command_file_path

    def run_simulation(self):
        used_os = platform.system()
        if used_os == "Linux":
            subprocess.call(self.command_unix, shell=True)
        # TODO: Windows and Mac commands
        # elif used_os == "Windows":
        #     subprocess.call(self.command_win, shell=True)
        else:
            print("It appears we do no support your OS.")


# For testing
Simulation("/home/siansiir/mcerd/source/Examples/35Cl-85-LiMnO_Li").run_simulation()
