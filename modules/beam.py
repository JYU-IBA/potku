# coding=utf-8
# TODO: Add licence information
"""
Created on 25.4.2018
Updated on ...
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

from modules.element import Element

class Beam:

    def __init__(self, ion=Element("Cl", 35), energy=10, charge=4,
                 energy_distribution=0, spot_size=(3.0, 5.0), divergence=0,
                 profile="uniform"):

        self.ion = ion
        self.energy = energy
        self.charge = charge
        self.energy_distribution = energy_distribution
        self.spot_size = spot_size
        self.divergence = divergence
        self.profile = profile