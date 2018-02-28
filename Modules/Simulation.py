# coding=utf-8
"""
Created on 26.2.2018
Updated on 28.2.2018

#TODO Description of Potku and copyright
#TODO Lisence

Simulation.py runs the MCERD simulation with a command file.
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
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

        self.command_win = "cd " + self.bin_dir + " && mcerd.exe " + command_file_path
        self.command_unix = "cd " + self.bin_dir + " && ./mcerd " + command_file_path

    def run_simulation(self):
        """Runs the simulation.

        """
        used_os = platform.system()
        if used_os == "Windows":
            subprocess.call(self.command_win, shell=True)
        elif used_os == "Linux":
            subprocess.call(self.command_unix, shell=True)
        elif used_os == "Darwin":
            subprocess.call(self.command_unix, shell=True)
        else:
            print("It appears we do no support your OS.")

# For testing this class alone:
# Simulation("/home/siansiir/mcerd/source/Examples/35Cl-85-LiMnO_Li").run_simulation()
# Simulation(r"C:\MyTemp\Source\Examples\35Cl-85-LiMnO_Li").run_simulation()
