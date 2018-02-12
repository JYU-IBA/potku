# coding=utf-8
'''
Created on 15.3.2013
Updated on 26.8.2013

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

import numpy, hashlib
from os import makedirs
from os.path import curdir, join, exists, realpath, split, splitext
import platform, re, subprocess, sys
from PyQt5 import QtGui, QtWidgets
from subprocess import Popen


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
    return filename


def open_files_dialog(parent, default_folder, title, files):
    '''Opens open file dialog for multiple files
    
    Opens dialog to select files to be opened and returns full file path to 
    selected file if one or more is selected. If no file is selected returns None.
    
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
    filenames = QtWidgets.QFileDialog.getOpenFileNames(parent,
                                                   title,
                                                   default_folder,
                                                   parent.tr(files))
    return filenames


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

    a = int(y[0] / width) * width;
    i = 0;
    hist_list = []
    while i < data_length:
        b = 0.0
        while i < data_length and y[i] < a:
            b += 1
            i += 1
        hist_list.append((a - (width / 2.0), b)) 
        a += width
    # Add zero to the end.
    # hist_list.append((a - (width / 2.0), 0))
    return hist_list


def tof_list(cut_file, directory, save_output=False):
    '''ToF_list 
    
    Arstila's tof_list executables interface for Python.
    
    Args:
        cut_file: A string representing cut file to be ran through tof_list.
        directory: A string representing measurement's energy spectrum directory.
        save_output: A boolean representing whether tof_list output is saved.
        
    Returns:
        Returns cut file as list transformed through Arstila's tof_list program.
    '''
    bin_dir = join(realpath(curdir), "external", "Potku-bin")
    tof_list_array = []
    if not cut_file:
        return []
    stdout = None
    try:
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            command = (str(join(bin_dir, "tof_list.exe")),
                       cut_file)
            stdout = subprocess.check_output(command,
                                             cwd=bin_dir,
                                             shell=True,
                                             startupinfo=startupinfo)
        else:
            command = "{0} {1}".format(join(".", "tof_list"), cut_file, bin_dir)
            p = subprocess.Popen(command.split(' ', 1), cwd=bin_dir,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, unused_stderr = p.communicate()
        
        lines = stdout.decode().strip().replace("\r", "").split("\n")
        for line in lines:
            if not line:  # Can still result in empty lines at the end, skip.
                continue
            line_split = re.split("\s+", line.strip())
            tupled = (float(line_split[0]),
                      float(line_split[1]),
                      float(line_split[2]),
                      int(line_split[3]),
                      float(line_split[4]),
                      line_split[5],
                      float(line_split[6]),
                      int(line_split[7]))
            tof_list_array.append(tupled)
        if save_output:
            if not directory:
                directory = join(realpath(curdir), "energy_spectrum_output")
            if not exists(directory):
                makedirs(directory)
            unused_dir, file = split(cut_file)
            directory_es_file = join(directory,
                                     "{0}.tof_list".format(splitext(file)[0]))
            numpy_array = numpy.array(tof_list_array,
                                         dtype=[('float1', float),
                                                ('float2', float),
                                                ('float3', float),
                                                ('int1', int),
                                                ('float4', float),
                                                ('string', numpy.str_, 3),
                                                ('float5', float),
                                                ('int2', int)])
            numpy.savetxt(directory_es_file, numpy_array,
                          delimiter=" ",
                          fmt="%5.1f %5.1f %10.5f %3d %8.4f %s %6.3f %d")  
    except:
        import traceback
        msg = "Error in tof_list: "
        err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
        str_err = ", ".join([sys.exc_info()[0].__name__ + ": " + \
                      traceback._some_str(sys.exc_info()[1]),
                      err_file,
                      str(sys.exc_info()[2].tb_lineno)])
        msg += str_err
        print(msg)
    finally:
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
    '''Calculate stopping of a particle in a carbon foil
    
    Args:
        element: Name of the element (e.g. "Si")
        isotope: Mass number of the element (e.g. 28)
        energy: Energy of the incident particle in MeVs (e.g. 2.0)
        carbon_thickness: Thickness of the carbon foil in ug/cm^2. (e.g. 3.0)
        
    Returns:
        Energy loss of particle in a carbon foil of some thickness in Joules
    '''
    bin_dir = join(realpath(curdir), 'external', 'Potku-bin')
    # parameters can be 0 but not None
    if element != None and isotope != None \
            and energy != None and carbon_thickness != None: 
        inputdata = bytes("{0}-{1}".format(isotope, element), 'utf-8')
        if platform.system() == 'Windows':
            print("Running gsto_stop.exe on Windows.")
            args = [join(bin_dir, 'gsto_stop.exe'), "{0}-{1}".format(isotope, element), 'C', str(energy)]
            print(args) 
            p = Popen(args, cwd=bin_dir, stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            print("Running gsto_stop on Unix.")
            args = ['./gsto_stop', "{0}-{1}".format(isotope, element), 'C', str(energy)]
            print(args)
            p = Popen(args, cwd=bin_dir, stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)   

        stdout, unused_stderr = p.communicate()
        output = stdout.decode()
        print(unused_stderr.decode())
        print("Stopping: ", output, "eV/(1e15 at/cm^2)");
        amu=1.660548782e-27 #FIXME: This should be somewhere globally
        E_loss = (float(output)/1e15)*(carbon_thickness*1e-9/ (12*amu)) #Energy loss in eV calculated from energy loss (eV/10e15 at/cm^2) and thickness (kg/cm^2)
        E_loss *= 1.6021765e-19; # eV to Joule
        return E_loss
    else:
        print("No parameters to calculate carbon stopping energy.")
        return None
    

def coinc(input_file, output_file, skip_lines, tablesize, trigger, adc_count,
          timing, columns="$3,$5", nevents=0, timediff=True, temporary=False):
    '''Calculate coincidences of file.
    
    Args:
        input_file: A string representing input file.
        output_file: A string representing destination file.
        skip_lines: An integer representing how many lines from the beginning
                    of the file is skipped.
        tablesize: An integer representing how large table is used to calculate
                   coincidences.
        trigger: An integer representing trigger ADC.
        adc_count: An integer representing the count of ADCs.
        nevents: An integer representing limit of how many events will the program
                 look for. 0 means no limit.
        timing: A tupple consisting of (min, max) representing different ADC 
                timings.
        timediff: A boolean representing whether timediff is output or not.
        temporary: A boolean representing whether temporary file is used. This
                   is used when doing first-time-import for file set to 
                   approximately get correct timing limits.
    
    Return:
        Returns 0 if it was success, 1 if it resulted in error
    '''
    timing_str = ""
    for key in timing.keys():
        tmp_str = "--low={0},{1} --high={0},{2}".format(key,
                                                        timing[key][0],
                                                        timing[key][1])
        timing_str = "{0} {1}".format(timing_str, tmp_str)
    column_count = len(columns.split(','))
    column_template = "%i " * column_count
    if not column_count or not timing_str:  # No columns or timings...
        return
    bin_dir = join(realpath(curdir), "external", "Potku-bin")
    timediff_str = ""
    if timediff or temporary:
        timediff_str = "--timediff"
        
    executable = "coinc.exe"
    if platform.system() != "Windows":
        executable = "./coinc"
    command = "{0} {1} && {2}".format(
        "cd",
        bin_dir,
        "{7} --silent {0} {1} {2} {3} {4} {5} {8} {6}".format(
            "--skip={0}".format(skip_lines),
            "--tablesize={0}".format(tablesize),
            "--trigger={0}".format(trigger),
            "--nadc={0}".format(adc_count),
            timediff_str,
            timing_str.strip(),
            input_file,
            executable,
            "--nevents={0}".format(nevents)
            )         
        )
    if temporary:
        command = "{0} {1}".format(
           command,
           "> {0}".format(output_file)
           )
    else:
        command = "{0} {1}".format(
           command,
           "| awk {0} > {1}".format("\"{print "+columns+"}\"", output_file)
           )
    # print(command)
    try:
        subprocess.call(command, shell=True)
        return True
    except:
        return False
    


def md5_for_file(f, block_size=2 ** 20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data.encode('utf8'))
    return md5.digest()



