# coding=utf-8
'''
Created on 29.4.2013
Updated on 23.5.2013

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import configparser
from os import path
from os import makedirs

class GlobalSettings:
    '''Global settings class to handle software settings.
    '''
    def __init__(self):
        '''Inits GLobalSettings class.
        '''
        self.__config_directory = path.join(path.expanduser("~"), "potku")
        self.__config_file = path.join(self.__config_directory, "potku.ini")
        if not path.exists(self.__config_directory):
            makedirs(self.__config_directory)
            
        self.__config = configparser.ConfigParser()
        
        self.__project_directory = path.join(self.__config_directory, "projects")
        self.__project_directory_last_open = self.__project_directory
        self.__element_colors = {"H" : "black",
                              "He" : "red",
                              "Li" : "red",
                              "Be" : "red",
                              "B" : "red",
                              "C" : "red",
                              "N" : "red",
                              "O" : "blue",
                              "F" : "red",
                              "Ne" : "red",
                              "Na" : "red",
                              "Mg" : "red",
                              "Al" : "red",
                              "Si" : "purple",
                              "P" : "red",
                              "S" : "red",
                              "Cl" : "red",
                              "Ar" : "red",
                              "K" : "red",
                              "Ca" : "red",
                              "Sc" : "red",
                              "Ti" : "red",
                              "V" : "red",
                              "Cr" : "red",
                              "Mn" : "red",
                              "Fe" : "red",
                              "Co" : "red",
                              "Ni" : "red",
                              "Cu" : "red",
                              "Zn" : "red",
                              "Ga" : "red",
                              "Ge" : "red",
                              "As" : "red",
                              "Se" : "red",
                              "Br" : "red",
                              "Kr" : "red",
                              "Rb" : "red",
                              "Sr" : "red",
                              "Y" : "red",
                              "Zr" : "red",
                              "Nb" : "red",
                              "Mo" : "red",
                              "Tc" : "red",
                              "Ru" : "red",
                              "Rh" : "red",
                              "Pd" : "red",
                              "Ag" : "red",
                              "Cd" : "red",
                              "In" : "red",
                              "Sn" : "red",
                              "Sb" : "red",
                              "Te" : "red",
                              "I" : "red",
                              "Xe" : "red",
                              "Cs" : "red",
                              "Ba" : "red",
                              "La" : "red",
                              "Ce" : "red",
                              "Pr" : "red",
                              "Nd" : "red",
                              "Pm" : "red",
                              "Sm" : "red",
                              "Eu" : "red",
                              "Gd" : "red",
                              "Tb" : "red",
                              "Dy" : "red",
                              "Ho" : "red",
                              "Er" : "red",
                              "Tm" : "red",
                              "Yb" : "red",
                              "Lu" : "red",
                              "Hf" : "red",
                              "Ta" : "red",
                              "W" : "red",
                              "Re" : "red",
                              "Os" : "red",
                              "Ir" : "red",
                              "Pt" : "red",
                              "Au" : "red",
                              "Hg" : "red",
                              "Tl" : "red",
                              "Pb" : "red",
                              "Bi" : "red",
                              "Po" : "red",
                              "At" : "red",
                              "Rn" : "red",
                              "Fr" : "red",
                              "Ra" : "red",
                              "Ac" : "red",
                              "Th" : "red",
                              "Pa" : "red",
                              "U" : "red",
                              "Np" : "red",
                              "Pu" : "red",
                              "Am" : "red",
                              "Cm" : "red",
                              "Bk" : "red",
                              "Cf" : "red",
                              "Es" : "red",
                              "Fm" : "red",
                              "Md" : "red",
                              "No" : "red",
                              "Lr" : "red",
                              "Rf" : "red",
                              "Db" : "red",
                              "Sg" : "red",
                              "Bh" : "red",
                              "Hs" : "red",
                              "Mt" : "red",
                              "Ds" : "red",
                              "Rg" : "red",
                              "Cn" : "red",
                              "Uut" : "red",
                              "Uuq" : "red",
                              "Uup" : "red",
                              "Uuh" : "red",
                              "Uus" : "red",
                              "Uuo" : "red"}
        
        self.__set_defaults()
        if not path.exists(self.__config_file):
            self.save_config()
        else:
            self.__load_config()
        
        
    def __set_defaults(self):
        '''Set settings to default values.
        '''
        self.__config.add_section("default")
        self.__config.add_section("colors")
        self.__config.set("default", "project_directory", self.__project_directory)
        self.__config.set("default", "project_directory_last_open", 
                          self.__project_directory_last_open)
        keys = self.__element_colors.keys()
        for key in keys:
            self.__config.set("colors", key, self.__element_colors[key])
    
    
    def __load_config(self):
        '''Load old settings and set values.
        '''
        self.__config.read(self.__config_file)
        # Rest is deprecated code
        try:
            pdlo = "project_directory_last_open"
            self.__project_directory = self.__config["default"]["project_directory"]
            self.__project_directory_last_open = self.__config["default"][pdlo]
            keys = self.__config["colors"].keys()
            for key in keys:
                self.__element_colors[key.title()] = self.__config["colors"][key]
        except:
            self.__set_defaults()
        
        
    def save_config(self):
        '''Save current global settings.
        '''
        with open(self.__config_file, 'wt+') as configfile:
            self.__config.write(configfile)
           
           
    def get_project_directory(self):
        '''Get default project directory.
        '''
        return self.__config["default"]["project_directory"]
    
    
    def set_project_directory(self, directory):
        '''Save default project directory.
        
        Args:
            directory: String representing folder where projects will be saved
            by default.
        '''
        self.__config["default"]["project_directory"] = directory
        self.save_config()
        
    
    def get_project_directory_last_open(self):
        '''Get directory where last project was opened.
        '''
        return self.__config["default"]["project_directory_last_open"]
    
    
    def set_project_directory_last_open(self, directory):
        '''Save last opened project directory.
        
        Args:
            directory: String representing project folder.
        '''
        self.__config["default"]["project_directory_last_open"] = directory
        self.save_config()
        
        
    def get_element_colors(self):
        '''Get all elements' colors.
        '''
        return self.__config["colors"]
    
    
    def get_element_color(self, element):
        '''Get a specific element's color.
        
        Args:
            element: String representing element name.
        '''
        return self.__config["colors"][element]
    
    
    def set_element_color(self, element, color):
        '''Set default color for an element.
        
        Args:
            element: String representing element.
            color: String representing color.
        '''
        self.__config["colors"][element] = color
