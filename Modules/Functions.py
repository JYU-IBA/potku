# coding=utf-8
'''
Created on 15.3.2013
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

from subprocess import Popen
from os.path import curdir
from os.path import join
from os.path import realpath
import platform
import re
import subprocess
from PyQt5 import QtGui, QtWidgets


def open_file_dialog(parent, default_folder, title, files):
    '''Opens open file dialog
    
    Opens dialog to select file to be opened and returns full file path to 
    selected file if one is selected. If no file is selected returns None.
    
    Args:
        parent: Parent object which opens the open file dialog.
        default_folder: String representing which folder is shown when dialog 
            opens. 
        title: String representing open file dialog title.
        files: String representing what type of file can be opened.
    
    Returns:
        A full path to the selected filename if a file is selected. For
        example:
        
        "C:/Transfer/FinlandiaData/esimerkkidata.zip"
    '''
    filename = QtWidgets.QFileDialog.getOpenFileName(parent,
                                                 title,
                                                 default_folder,
                                                 parent.tr(files))
    return filename[0]


def save_file_dialog(parent, default_folder, title, files):
    '''Opens save file dialog
    
    Opens dialog to select savefile name and returns full file path to 
    selected file if one is selected. If no file is selected returns None.
    
    Args:
        parent: Parent object which opens the open file dialog.
        default_folder: String representing which folder is shown when dialog 
            opens. 
        title: String representing open file dialog title.
        files: String representing what type of file can be opened.
    
    Returns:
        A full path to the selected filename if a file is selected. For
        example:
        
        "C:/Transfer/FinlandiaData/esimerkkidata.zip"
    '''
    filename = QtWidgets.QFileDialog.getSaveFileName(parent,
                                                 title,
                                                 default_folder,
                                                 parent.tr(files))
    return filename


def hist(data, width=1.0, col=1):
    '''Format data into slices of given width.
    
    Python version of Arstila's hist code. This purpose is to format data's 
    column at certain widths so the graph won't include all information.
    
    Args:
        data: List representation of data.
        width: Float defining width of data.
        col: Integer representing what column of data is used.
        
    Return:
        Returns formatted list to use in graphs.
    '''
    col -= 1  # Same format as Arstila's code, actual column number (not index)
    if col < 0 or col >= len(data):
        return []
    y = tuple(float(pair[col]) for pair in data)
    y = sorted(y, reverse=False)
    data_length = len(y)

    a = int(y[0] / width) * width
    i = 0
    hist_list = []
    while i < data_length:
        b = 0.0
        while i < data_length and y[i] < a:
            b += 1
            i += 1
        hist_list.append((a - (width / 2.0), b)) 
        a += width
    return hist_list


def tof_list(cut_file):
    '''ToF_list 
    
    Arstila's tof_list executables interface for Python.
    
    Args:
        cut_file: String representing cut file to be ran through tof_list.
        
    Returns:
        Returns cut file as list transformed through Arstila's tof_list program.
    '''
    bin_dir = join(realpath(curdir), "external", "Potku-bin")
    tof_list_array = []
    if cut_file:
        stdout = None
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            command = "{0} {1}".format(join(bin_dir, "tof_list.exe"), cut_file)
            try:
                stdout = subprocess.check_output(command.split(' '),
                                             cwd=bin_dir,
                                             shell=False,
                                             startupinfo=startupinfo)
            except subprocess.CalledProcessError as e:
                print(e)
        else:
            command = "{0} {1}".format(join(".", "tof_list"), cut_file, bin_dir)
            p = subprocess.Popen(command.split(' '), cwd=bin_dir,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, unused_stderr = p.communicate()
        lines = stdout.decode().strip().replace("\r", "").split("\n")
        for line in lines:
            if not line:  # Can still result in empty lines at the end, skip.
                continue
            split = re.split("\s+", line.strip())
            tupled = (float(split[0]),
                      float(split[1]),
                      float(split[2]),
                      int(split[3]),
                      float(split[4]),
                      split[5],
                      float(split[6]),
                      int(split[7]))
            tof_list_array.append(tupled)
    return tof_list_array
    
    
def convert_mev_to_joule(energy_in_MeV):
    """Converts MeV (mega electron volts) to joules.
    
    Args:
        energy_in_MeV: Value to be converted (float)
    
    Returns:
        Returns energy in MeVs (float)
    """
    # joule = 6.24150934 * pow(10, 18)  # 1 J = 6.24150934 * 10^18 eV
    joule = 6.24150934e18
    return float(energy_in_MeV) * 1000000.0 / joule


def convert_amu_to_kg(mass_in_amus):
    """Converts amus (atomic mass units) to kilograms.
    
    Args:
        mass_in_amus: Value to be converted (float)
    
    Returns:
        Returns mass in kilograms (float)
    """
    # amu = 1.660538921 * pow(10, -27)  # 1 u = 1.660538921×10−27 kg
    amu = 1.660538921e-27
    return float(mass_in_amus) * amu


def carbon_stopping(element, isotope, energy, carbon_thickness):
    '''ToF_list 
    
    Julin's carbon_stopping executables interface for Python.
    
    Args:
        element: Element's name as a string.
        isotope: Element's isotope.
        energy: Particle's (the isotope's) energy in joules.
        carbon_thickness: Thickness of the carbon foil in the measurement unit 
                          in µg/m^2.
        
    Returns:
        List containing (beam proton number, nuclide number, energy, stopping as 
        eV/10^15 atoms at given energy, energy loss in foil of given thickness)
    '''
    bin_dir = join(realpath(curdir), 'external', 'Potku-SRIMgen')
    # parameters can be 0 but not None
    if element != None and isotope != None \
            and energy != None and carbon_thickness != None: 
        inputdata = bytes("{0}-{1} {2}".format(isotope, element, energy), 'utf-8')
        if platform.system() == 'Windows':
            print("Running carbon_stopping on Windows.")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            command = "{0} {1}".format(join(bin_dir, "carbon_stopping.exe"),
                                       carbon_thickness)
            p = Popen(command.split(' '), cwd=bin_dir, stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      startupinfo=startupinfo)
        else:
            print("Running carbon_stopping on Unix.")
            command = "{0} {1}".format(join(".", "carbon_stopping"),
                                       carbon_thickness)
            p = Popen(command.split(' '), cwd=bin_dir, stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)   

        p.stdin.write(inputdata)
        stdout, unused_stderr = p.communicate()
        
        # output will consists of beam proton number, nuclide number, energy, stopping
        # as eV/10^15 atoms at given energy, energy loss in foil of given thickness
        # i.e. 2 4 1.000000e+000 3.780207e+001 5.880939e-003
        
        output = stdout.decode()
        return output.strip().split(' ')
    else:
        print("No parameters to calculate carbon stopping energy.")
        return None
    

