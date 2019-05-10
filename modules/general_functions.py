# coding=utf-8
"""
Created on 15.3.2013
Updated on 10.5.2019

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen

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
             "Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"
__version__ = "2.0"

import bisect
import hashlib
import json
import numpy
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

from decimal import Decimal

from PyQt5 import QtWidgets

from subprocess import Popen


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
    return filenames[0]


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
    dir_path, old_name = os.path.split(old_path)
    try:
        new_file = os.path.join(dir_path, new_name)
        if os.path.exists(new_file):
            raise OSError
        os.rename(old_path, new_file)
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
    if col < 0:
        return []
    if data[0] and col >= len(data[0]):
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


def read_espe_file(espe_file):
    """Reads a file generated by get_espe.

    Args:
        espe_file: A string representing path of energy spectrum data file
        (.simu) to be read.

    Returns:
        Returns energy spectrum data as a list.
        """
    data = []
    with open(espe_file, 'r') as file:
        for line in file:
            data_point = line.strip().split()
            data.append(data_point)
    return data


def read_tof_list_file(tof_list_file):
    """
    Read a file in tof list format.

    Args:
        tof_list_file: File path to a tof list file.

    Return:
        List of the lines in the file as tuples.
    """
    data = []
    if os.path.exists((tof_list_file)):
        with open(tof_list_file, 'r') as file:
            for line in file:
                parts = line.split()
                part = float(Decimal(parts[0])), float(Decimal(parts[1])), \
                    float(Decimal(parts[2])), int(parts[3]), \
                    float(Decimal(parts[4])), parts[5], \
                    float(Decimal(parts[6])), int(parts[7])
                data.append(part)
    return data


def calculate_spectrum(tof_listed_files, spectrum_width, measurement,
                       directory_es):
    """Calculate energy spectrum data from cut files.

    Returns list of cut files
    """
    histed_files = {}
    keys = tof_listed_files.keys()
    invalid_keys = []
    for key in keys:
        histed_files[key] = hist(tof_listed_files[key],
                                 spectrum_width, 3)
        if not histed_files[key]:
            invalid_keys.append(key)
            continue
        first_val = (histed_files[key][0][0] - spectrum_width, 0)
        last_val = (histed_files[key][-1][0] + spectrum_width, 0)
        histed_files[key].insert(0, first_val)
        histed_files[key].append(last_val)
    for key in keys:
        if key in invalid_keys:
            continue
        file = measurement.name
        histed = histed_files[key]
        filename = os.path.join(directory_es,
                                "{0}.{1}.hist".format(
                                    os.path.splitext(file)[0], key))
        numpy_array = numpy.array(histed,
                                  dtype=[('float', float),
                                         ('int', int)])
        numpy.savetxt(filename, numpy_array, delimiter=" ",
                      fmt="%5.5f %6d")
    return histed_files


def copy_cut_file_to_temp(cut_file):
    """
    Copy cut file into temp directory.

    Args:
        cut_file: Cut file to copy.

    Return:
        Path to the cut file in temp directory.
    """
    # Move cut file to temp folder, at least in Windows tof_list works
    # properly when cut file is there.
    # TODO: check that this works in mac and Linux
    cut_file_name = os.path.split(cut_file)[1]

    # OS specific directory where temporary MCERD files will be stored.
    # In case of Linux and Mac this will be /tmp and in Windows this will
    # be the C:\Users\<username>\AppData\Local\Temp.
    tmp = tempfile.gettempdir()

    new_cut_file = os.path.join(tmp, cut_file_name)
    shutil.copyfile(cut_file, new_cut_file)
    return new_cut_file


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
    bin_dir = os.path.join(os.path.realpath(os.path.curdir), "external",
                           "Potku-bin")
    tof_list_array = []
    if not cut_file:
        return []

    new_cut_file = copy_cut_file_to_temp(cut_file)

    try:
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            command = (str(os.path.join(bin_dir, "tof_list.exe")),
                       new_cut_file)
            stdout = subprocess.check_output(command,
                                             cwd=bin_dir,
                                             shell=True,
                                             startupinfo=startupinfo)
        else:
            if platform.system() == "Linux":
                command = "{0} {1}".format("./tof_list", new_cut_file)

            else:
                command = "{0} {1}".format("./tof_list_mac", new_cut_file)
            p = subprocess.Popen(command.split(' ', 1),
                                 cwd=bin_dir,
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
                directory = os.path.join(os.path.realpath(os.path.curdir),
                                      "energy_spectrum_output")
            if not os.path.exists(directory):
                os.makedirs(directory)
            unused_dir, file = os.path.split(cut_file)
            directory_es_file = os.path.join(
                directory, "{0}.tof_list".format(os.path.splitext(file)[0]))
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
        remove_file(new_cut_file)
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


def carbon_stopping(element, isotope, energy, carbon_thickness, carbon_density):
    """Calculate stopping of a particle in a carbon foil

    Args:
        element: Name of the element (e.g. "Si")
        isotope: Mass number of the element (e.g. 28)
        energy: Energy of the incident particle in MeVs (e.g. 2.0)
        carbon_thickness: Thickness of the carbon foil in nm. (e.g. 13.0)
        carbon_density: Density of the carbon foil in g/cm3. (e.g. 2.27)

    Returns:
        Energy loss of particle in a carbon foil of some thickness in Joules
    """
    bin_dir = os.path.join(os.path.realpath(os.path.curdir), 'external',
                           'Potku-bin')
    # parameters can be 0 but not None
    if element is not None and isotope is not None and energy is not None and \
            carbon_thickness is not None:
        if platform.system() == 'Windows':
            print("Running gsto_stop.exe on Windows.")
            args = [os.path.join(bin_dir, 'gsto_stop.exe'),
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
        # amu = 1.660548782e-27
        # Energy loss in eV calculated from energy loss (eV/10e15 at/cm^2)
        # and thickness (kg/cm^2)
        # e_loss = (float(output) / 1e15) * (carbon_thickness * 1e-9 / (12 *
        # amu)) Original line

        # This only works for carbon, and with one layer in the carbon timing
        #  foil!!!
        e_loss = float(output) * ((((carbon_density / 12 * 6.0221409e+23) / 1e7)
                                   * carbon_thickness) / 1e15)
        # e_loss = stopping * ( ( (density/( unit mass)*
        # avogadro's number / (cm->nm) ) *  carbon_thickness) /1e15 )
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
    bin_dir = os.path.join(os.path.realpath(os.path.curdir), "external",
                           "Potku-bin")
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
        if platform.system() == "Darwin":
            command = "{0} {1}".format(
            command,
            "| awk {0} > {1}".format("'{print " + columns + "}'", output_file))  # mac needs '' around awk print
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

    return "".join(sups.get(char, char) for char in string)


def check_text(input_field):
    """Checks if the given QLineEdit input field contains text. If not,
    field's background is set red.

    Args:
        input_field: QLineEdit object.

    Return:
        True for white, False for red.
    """
    if not input_field.text():
        set_input_field_red(input_field)
        return False
    else:
        set_input_field_white(input_field)
        return True


def set_input_field_red(input_field):
    """Sets the background of given input field red.

    Args:
        input_field: Qt widget that supports Qt Style Sheets.
    """
    input_field.setStyleSheet("background-color: %s" % "#f6989d")


def set_input_field_white(input_field):
    """Sets the background of given input field white.

    Args:
        input_field: Qt widget that supports Qt Style Sheets.
    """
    input_field.setStyleSheet("background-color: %s" % "#ffffff")


def find_y_on_line(point1, point2, x):
    """
    Find the y(x) based on a line that goes through point1 and 2.

    Args:
         point1: Point object.
         point2: Point object.
         x: Value whose corresponding y is wanted.

    Return:
        Y for x.
    """
    y_part = point2.get_y() - point1.get_y()
    x_part = point2.get_x() - point1.get_x()
    k = y_part / x_part

    y = k * x - (k * point1.get_x()) + point1.get_y()
    return y


def validate_text_input(text, regex):
    """
    Validate the text using given regular expression. If not valid, remove
    invalid characters.

    Args:
        text: Text to validate.
        regex: Regular expression to match.
    """
    valid = re.match(regex + "$", text)

    if "_" in regex:  # Request name
        substitute_regex = "[^A-Za-z0-9_ÖöÄäÅå-]"
    else:  # Other names
        substitute_regex = "[^A-Za-z0-9-ÖöÄäÅå]"

    if not valid:
        valid_text = re.sub(substitute_regex, '', text)
        return valid_text
    else:
        return text


def find_nearest(x, lst):
    """
    Find given list's nearest point's x coordinate from x.

    Args:
        x: X coordinate.
        lst: List to search.

    Return:
        Nearest point's x coordinate.
    """
    # https://stackoverflow.com/questions/12141150/from-list-of-integers
    # -get-number-closest-to-a-given-value
    position = bisect.bisect_left(lst, x)
    if position == 0:
        return lst[0]
    if position == len(lst):
        return lst[len(lst) - 1]
    before = lst[position - 1]
    after = lst[position]
    if after - x < x - before:
        return after
    else:
        return before


def delete_simulation_results(element_simulation, recoil_element):
    """
    Delete simulation result files.

    Args:
         element_simulation: Element simulation object.
         recoil_element: Recoil element object.
    """
    files_to_delete = []
    for file in os.listdir(element_simulation.directory):
        if file.startswith(recoil_element.prefix):
            if file.endswith(".recoil") or file.endswith("erd") or \
                    file.endswith(".simu") or file.endswith(".scatter"):
                files_to_delete.append(os.path.join(
                    element_simulation.directory, file))
    for f in files_to_delete:
        os.remove(f)


def calculate_new_point(previous_point, new_x, next_point,
                        area_points):
    """
    Calculate a new point whose x coordinate is given, between previous
    and next point.

    Args:
        previous_point: Previous point.
        new_x: X coordinate for new point.
        next_point: Next point.
        area_points: List of points where a new point is added.
    """
    try:
        previous_x = previous_point.get_x()
        previous_y = previous_point.get_y()

        next_x = next_point.get_x()
        next_y = next_point.get_y()
    except AttributeError:
        previous_x = previous_point[0]
        previous_y = previous_point[1]
        next_x = next_point[0]
        next_y = next_point[1]

    x_diff = round(next_x - previous_x, 4)
    y_diff = round(next_y - previous_y, 4)

    if x_diff == 0.0:
        # If existing points are close enough
        return

    k = y_diff / x_diff
    new_y = k * new_x - k * previous_x + previous_y

    new_point = (new_x, new_y)
    area_points.append(new_point)


def uniform_espe_lists(lists, channel_width):
    """
    Modify given energy spectra lists to have the same amount of items.

    Return:
        Modified lists.
    """
    first = lists[0]
    second = lists[1]
    # check if first x values don't match
    # add zero values to the one missing the x values
    if second[0][0] < first[0][0]:
        x = first[0][0] - channel_width
        while round(x, 4) >= second[0][0]:
            first.insert(0, (round(x, 4), 0))
            x -= channel_width
    elif first[0][0] < second[0][0]:
        x = second[0][0] - channel_width
        while round(x, 4) >= first[0][0]:
            second.insert(0, (round(x, 4), 0))
            x -= channel_width

    # do the same for the last values
    if second[-1][0] < first[-1][0]:
        x = second[-1][0] + channel_width
        while round(x, 4) <= first[-1][0]:
            second.append((round(x, 4), 0))
            x += channel_width
    elif first[-1][0] < second[-1][0]:
        x = first[-1][0] + channel_width
        while round(x, 4) <= second[-1][0]:
            first.append((round(x, 4), 0))
            x += channel_width

    return first, second


def dominates(a, b):
    """
    Check if solution a dominates solution b. Minimization. This is related
    to the NSGA-II optimization function (modules/nsgaii.py).

    Args:
        a: Solution (objective values) a.
        b: Solution (objective values) b.

    Return:
        Whether a dominates b.
    """
    can_dominate = True
    dom = False
    for i in range(len(a)):
        if a[i] == b[i] and can_dominate:
            can_dominate = True
        elif a[i] > b[i]:
            can_dominate = False
            dom = False
        elif a[i] < b[i] and can_dominate:
            can_dominate = True
            dom = True
    return dom


def tournament_allow_doubles(t, p, fit):
    """
    Tournament selection that allows one individual to be in the mating pool
    several times.

    Args:
        t: Number of solutions to be compared, size of tournament.
        p: Number of solutions to be selected as parents in the mating pool.
        fit: Fitness vectors.

    Return:
        Index of selected solutions.
    """
    n = len(fit)
    pool = []
    for i in range(p):
        candidates = []
        # Find k different candidates for tournament
        j = 0
        while j in range(t):
            candidate = numpy.random.randint(n)
            if candidate not in candidates:
                candidates.append(candidate)
                j += 1
        min_front = min([fit[i, 0] for i in candidates])
        min_candidates = [i for i in candidates if fit[i, 0] == min_front]
        number_of_mins = len(min_candidates)
        if number_of_mins > 1:  # If multiple candidates from the same front
            # Find the candidate with smallest crowding distance
            max_dist = max([fit[i, 1] for i in min_candidates])
            max_cands = [i for i in min_candidates if fit[i, 1] == max_dist]
            pool.append(max_cands[0])
        else:
            pool.append(min_candidates[0])

    return numpy.array(pool)


def format_to_binary(var, length):
    """
    Format given integer into binary of a certain length.

    Args:
        var: Integer value to transform to binary.
        length: Length of the desired binary.

    Return:
        Formatted binary.
    """
    # Transform to binary
    var_bin = bin(var)
    # Add zeros to match the needed length
    try:
        b_index = var_bin.index("b")
        format_var = var_bin[b_index + 1:].zfill(length)
    except ValueError:
        format_var = var_bin.zfill(length)
    return format_var
