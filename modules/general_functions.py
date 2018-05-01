# coding=utf-8
"""
Created on 15.3.2013
Updated on 30.4.2018

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
"""

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli " \
             "Rahkonen \n Miika Raunio" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import platform
import shutil
import re
import subprocess
import sys
from subprocess import Popen

import hashlib
import json
import numpy
from PyQt5 import QtWidgets
from os import makedirs, rename, path


def open_file_dialog(parent, default_folder, title, files):
    """Opens open file dialog

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
    """
    filename = QtWidgets.QFileDialog.getOpenFileName(parent, title,
                                                     default_folder,
                                                     parent.tr(files))
    return filename[0]


def open_files_dialog(parent, default_folder, title, files):
    """Opens open file dialog for multiple files

    Opens dialog to select files to be opened and returns full file path to
    selected file if one or more is selected.
    If no file is selected returns None.

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
    """
    filenames = QtWidgets.QFileDialog.getOpenFileNames(parent, title,
                                                       default_folder,
                                                       parent.tr(files))
    return filenames


def save_file_dialog(parent, default_folder, title, files):
    """Opens save file dialog

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
    """
    filename = QtWidgets.QFileDialog.getSaveFileName(parent, title,
                                                     default_folder,
                                                     parent.tr(files))[0]
    return filename


def rename_file(old_path, new_name):
    """Renames file or directory and returns new path.

    Args:
        old_path: Path of file or directory to rename.
        new_name: New name for the file or directory.
    """
    if not new_name:
        return
    dir_path, old_name = path.split(old_path)
    try:
        new_file = path.join(dir_path, new_name)
        if path.exists(new_file):
            raise OSError
        rename(old_path, new_file)
    except OSError:
        # os.rename should raise this if directory or file exists on the
        # same name, but it seems it always doesn't.
        raise OSError
    return new_file


def remove_file(file_path):
    """Removes file or directory.

    Args:
        file_path: Path of file or directory to remove.
    """
    if not file_path:
        return
    try:
        shutil.rmtree(file_path)
    except Exception as e:
        # Removal failed
        print(e)


def hist(data, width=1.0, col=1):
    """Format data into slices of given width.

    Python version of Arstila's hist code. This purpose is to format data's
    column at certain widths so the graph won't include all information.

    Args:
        data: List representation of data.
        width: Float defining width of data.
        col: Integer representing what column of data is used.

    Return:
        Returns formatted list to use in graphs.
    """
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
    # Add zero to the end.
    # hist_list.append((a - (width / 2.0), 0))
    return hist_list


def save_settings(obj, extension, encoder, filepath=None):
    """Saves an object in JSON format in a file.

    Args:
        obj: object to be saved
        extension: Extension for the file.
        encoder: JSONEncoder class used in converting to JSON.
        filepath: Filepath including the name of the file.
    """
    if filepath is None:
        filepath = obj.directory
    filepath = filepath + extension
    with open(filepath, 'w') as savefile:
        json.dump(obj, savefile, indent=4, cls=encoder)


def read_espe_file(directory, espe_file):
    """Reads a file generated by get_espe.

    Args:
        espe_file: A string representing energy spectrum data file to be read.
        directory: A string representing the file's location.

    Returns:
        Returns energy spectrum data as a list.
        """
    file = path.join(directory, espe_file)
    lines = load_file(file)
    if not lines:
        # TODO Handle exception when file can not be read.
        return
    data = []
    for line in lines:
        data_point = line.strip().split()
        data.append(data_point)
    return data


# TODO This function is copied from MeasurementTabWidget.
def load_file(file):
    """Load file

    Args:
        file: A string representing full filepath to the file.
    """
    lines = []
    try:
        with open(file, "rt") as fp:
            for line in fp:
                lines.append(line)
    except:
        pass
    return lines


def tof_list(cut_file, directory, save_output=False):
    """ToF_list

    Arstila's tof_list executables interface for Python.

    Args:
        cut_file: A string representing cut file to be ran through tof_list.
        directory: A string representing measurement's energy spectrum
                   directory.
        save_output: A boolean representing whether tof_list output is saved.

    Returns:
        Returns cut file as list transformed through Arstila's tof_list program.
    """
    bin_dir = path.join(path.realpath(path.curdir), "external", "Potku-bin")
    tof_list_array = []
    if not cut_file:
        return []
    stdout = None
    try:
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            command = (str(path.join(bin_dir, "tof_list.exe")),
                       cut_file)
            stdout = subprocess.check_output(command,
                                             cwd=bin_dir,
                                             shell=True,
                                             startupinfo=startupinfo)
        elif platform.system() == 'Linux':
            command = "{0} {1}".format(path.join(bin_dir, "tof_list_linux"),
                                       cut_file)
            p = subprocess.Popen(command.split(' ', 1), cwd=bin_dir,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, unused_stderr = p.communicate()

        else:
            command = "{0} {1}".format(path.join(bin_dir, "tof_list_mac"),
                                       cut_file)
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
                directory = path.join(path.realpath(path.curdir),
                                      "energy_spectrum_output")
            if not path.exists(directory):
                makedirs(directory)
            unused_dir, file = path.split(cut_file)
            directory_es_file = path.join(
                directory, "{0}.tof_list".format(path.splitext(file)[0]))
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
        str_err = ", ".join([sys.exc_info()[0].__name__ + ": " +
                             traceback._some_str(sys.exc_info()[1]), err_file,
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
    """Calculate stopping of a particle in a carbon foil

    Args:
        element: Name of the element (e.g. "Si")
        isotope: Mass number of the element (e.g. 28)
        energy: Energy of the incident particle in MeVs (e.g. 2.0)
        carbon_thickness: Thickness of the carbon foil in ug/cm^2. (e.g. 3.0)

    Returns:
        Energy loss of particle in a carbon foil of some thickness in Joules
    """
    bin_dir = path.join(path.realpath(path.curdir), 'external', 'Potku-bin')
    # parameters can be 0 but not None
    if element is not None and isotope is not None and energy is not None and \
            carbon_thickness is not None:
        # inputdata = bytes("{0}-{1}".format(isotope, element), 'utf-8')
        if platform.system() == 'Windows':
            print("Running gsto_stop.exe on Windows.")
            args = [path.join(bin_dir, 'gsto_stop.exe'),
                    "{0}-{1}".format(isotope, element), 'C', str(energy)]
            print(args)
            p = Popen(args, cwd=bin_dir, stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            print("Running gsto_stop on Unix.")
            args = ['./gsto_stop', "{0}-{1}".format(isotope, element),
                    'C', str(energy)]
            print(args)
            p = Popen(args, cwd=bin_dir, stdin=subprocess.PIPE,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, unused_stderr = p.communicate()
        output = stdout.decode()
        print(unused_stderr.decode())
        print("Stopping: ", output, "eV/(1e15 at/cm^2)")
        amu = 1.660548782e-27  # FIXME: This should be somewhere globally
        # Energy loss in eV calculated from energy loss (eV/10e15 at/cm^2)
        # and thickness (kg/cm^2)
        e_loss = (float(output) / 1e15) * (carbon_thickness * 1e-9 / (12 * amu))
        e_loss *= 1.6021765e-19  # eV to Joule
        return e_loss
    else:
        print("No parameters to calculate carbon stopping energy.")
        return None


def coinc(input_file, output_file, skip_lines, tablesize, trigger, adc_count,
          timing, columns="$3,$5", nevents=0, timediff=True, temporary=False):
    """Calculate coincidences of file.

    Args:
        input_file: A string representing input file.
        output_file: A string representing destination file.
        skip_lines: An integer representing how many lines from the beginning
                    of the file is skipped.
        tablesize: An integer representing how large table is used to calculate
                   coincidences.
        trigger: An integer representing trigger ADC.
        adc_count: An integer representing the count of ADCs.
        timing: A tupple consisting of (min, max) representing different ADC
                timings.
        columns: Columns.
        nevents: An integer representing limit of how many events will the
                 program look for. 0 means no limit.
        timediff: A boolean representing whether timediff is output or not.
        temporary: A boolean representing whether temporary file is used. This
                   is used when doing first-time-import for file set to
                   approximately get correct timing limits.

    Return:
        Returns 0 if it was success, 1 if it resulted in error
    """
    timing_str = ""
    for key in timing.keys():
        tmp_str = "--low={0},{1} --high={0},{2}".format(key,
                                                        timing[key][0],
                                                        timing[key][1])
        timing_str = "{0} {1}".format(timing_str, tmp_str)
    column_count = len(columns.split(','))
    # column_template = "%i " * column_count
    if not column_count or not timing_str:  # No columns or timings...
        return
    bin_dir = path.join(path.realpath(path.curdir), "external", "Potku-bin")
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
            "| awk {0} > {1}".format("\"{print " + columns + "}\"", output_file)
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


def to_superscript(string):
    sups = {"0": "\u2070",
            "1": "\xb9",
            "2": "\xb2",
            "3": "\xb3",
            "4": "\u2074",
            "5": "\u2075",
            "6": "\u2076",
            "7": "\u2077",
            "8": "\u2078",
            "9": "\u2079"}

    return ''.join(sups.get(char, char) for char in string)
