# coding=utf-8
"""
Created on 15.3.2013
Updated on 29.1.2020

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
             "\n Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import bisect
import hashlib
import numpy as np
import os
import platform
import shutil
import subprocess
import tempfile
import logging
import time

from timeit import default_timer as timer
from pathlib import Path
from decimal import Decimal

from .parsing import ToFListParser
from subprocess import Popen
from itertools import (takewhile, repeat)

# TODO this could still be organized into smaller modules

def stopwatch(log_file=None):
    """Decorator that measures the time it takes to execute a function
    and prints the results or writes them to a log file if one is provided
    as an argument.
    """
    def outer(func):
        def inner(*args, **kwargs):
            start = timer()
            res = func(*args, **kwargs)
            stop = timer()

            timestamp = time.strftime("%y/%m/%D %H:%M.%S")
            msg = f"{timestamp}: {func.__name__}({args, kwargs})\n\t" \
                  f"took {stop - start} to execute.\n"
            if log_file is None:
                print(msg)
            else:
                with open(log_file, "a") as file:
                    file.write(msg)
            return res
        return inner
    return outer


def rename_file(old_path, new_name):
    """Renames file or directory and returns new path.

    Args:
        old_path: Path of file or directory to rename.
        new_name: New name for the file or directory.
    """
    if not new_name:
        return
    dir_path, old_name = os.path.split(old_path)
    new_file = Path(dir_path, new_name)
    if new_file.exists():
        # os.rename should raise this if directory or file exists on the
        # same name, but it seems it always doesn't.
        raise OSError(f"File {new_file} already exists")
    os.rename(old_path, new_file)
    return new_file


def remove_file(file_path):
    """Removes file or directory.

    Args:
        file_path: Path of file or directory to remove.
    """
    if not file_path:
        return
    try:
        # shutil.rmtree(file_path)
        os.remove(file_path)
    except Exception as e:
        # Removal failed
        print(e)


def remove_files(directory, exts=None, filter_func=None):
    """Removes all files in a directory that match given conditions.

    Args:
        directory: directory where the files are located
        exts: collection of file extensions. Files with these extensions will
            be deleted.
        filter_func: additional filter function applied to the file name. If
            provided, only the files that have the correct extension and match
            the filter_func condition will be deleted.
    """
    if not exts:
        return
    if filter_func is None:
        def filter_func(_):
            return True

    try:
        for file in os.scandir(directory):
            fp = Path(file)
            if fp.suffix in exts and filter_func(file.name):
                try:
                    fp.unlink()
                except OSError:
                    # fp could be a directory, or permissions may prevent
                    # deletion
                    pass
    except OSError:
        # Directory not found (or directory is a file), nothing to do
        pass


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
    if not data:
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


def calculate_spectrum(tof_listed_files, spectrum_width, measurement,
                       directory_es, no_foil=False):
    """Calculate energy spectrum data from .tof_list files and writes the
    results to .hist files.

    Args:
        tof_listed_files: contents of .tof_list files belonging to the
                          measurement as a dict.
        spectrum_width: TODO
        measurement: measurement which the .tof_list files belong to
        directory_es: directory
        no_foil: whether foil thickeness was set to 0 or not. This affects
                 the file name

    Returns:
        contents of .hist files as a dict
    """
    histed_files = {}
    keys = tof_listed_files.keys()
    invalid_keys = set()

    for key in keys:
        histed_files[key] = hist(tof_listed_files[key],
                                 spectrum_width, 3)
        if not histed_files[key]:
            invalid_keys.add(key)
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

        if no_foil:
            foil_txt = ".no_foil"
        else:
            foil_txt = ""

        filename = Path(directory_es,
                        "{0}.{1}{2}.hist".format(os.path.splitext(file)[0],
                                                 key,
                                                 foil_txt))
        numpy_array = np.array(histed, dtype=[('float', float), ('int', int)])

        np.savetxt(filename, numpy_array, delimiter=" ", fmt="%5.5f %6d")

    return histed_files


def copy_cut_file_to_temp(cut_file) -> Path:
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
    cut_file_name = Path(cut_file).name

    # OS specific directory where temporary MCERD files will be stored.
    # In case of Linux and Mac this will be /tmp and in Windows this will
    # be the C:\Users\<username>\AppData\Local\Temp.
    tmp = tempfile.gettempdir()

    new_cut_file = Path(tmp, cut_file_name)
    shutil.copyfile(cut_file, new_cut_file)
    return new_cut_file


def tof_list(cut_file, directory, save_output=False, no_foil=False,
             logger_name=None):
    """ToF_list

    Arstila's tof_list executables interface for Python.

    Args:
        cut_file: A string representing cut file to be ran through tof_list.
        directory: A string representing measurement's energy spectrum
                   directory.
        save_output: A boolean representing whether tof_list output is saved.
        no_foil: whether foil thickness was used when .cut files were generated.
                 This affects the file path when saving output
        logger_name: name of a logging entity

    Returns:
        Returns cut file as list transformed through Arstila's tof_list program.
    """
    bin_dir = get_bin_dir()

    if not cut_file:
        return []

    new_cut_file = copy_cut_file_to_temp(cut_file)
    tof_parser = ToFListParser()

    try:
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            command = (str(bin_dir / "tof_list.exe"), str(new_cut_file))
            stdout = subprocess.check_output(command,
                                             cwd=bin_dir,
                                             shell=True,
                                             startupinfo=startupinfo)
        else:
            command = "{0} {1}".format("./tof_list", str(new_cut_file))
            p = subprocess.Popen(command.split(' ', 1),
                                 cwd=bin_dir,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout, _ = p.communicate()

        tof_output = list(tof_parser.parse_strs(
            stdout.decode().splitlines(), method="row", ignore="w"))

        if save_output:
            if not directory:
                directory = Path(
                    os.path.realpath(os.path.curdir), "energy_spectrum_output")

            os.makedirs(directory, exist_ok=True)

            if no_foil:
                foil_txt = ".no_foil"
            else:
                foil_txt = ""

            directory_es_file = Path(
                directory,
                "{0}{1}.tof_list".format(Path(cut_file).stem,
                                         foil_txt))
            numpy_array = np.array(
                tof_output, dtype=[
                    ('float1', float), ('float2', float), ('float3', float),
                    ('int1', int), ('float4', float), ('string', np.str_, 3),
                    ('float5', float), ('int2', int)])
            np.savetxt(directory_es_file, numpy_array, delimiter=" ",
                       fmt="%5.1f %5.1f %10.5f %3d %8.4f %s %6.3f %d")
        return tof_output
    except Exception as e:
        msg = f"Error in tof_list: {e}"
        if logger_name is not None:
            logging.getLogger(logger_name).error(msg)
        else:
            print(msg)
        return []
    finally:
        remove_file(new_cut_file)


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
    bin_dir = get_bin_dir()
    # parameters can be 0 but not None
    if element is not None and isotope is not None and energy is not None and \
            carbon_thickness is not None:
        areal_density_tfu = (carbon_density * 1.0e3 * carbon_thickness * 1.0e-9) / (12.0 * 1.66053906660e-27) / 1.0e19
        if platform.system() == 'Windows':
            get_stop = str(bin_dir / "get_stop.exe")
        else:
            get_stop = './get_stop'

        args = [get_stop, "{0}{1}".format(isotope, element), str(energy),
                '-l', 'C', '-t', "{0}tfu".format(areal_density_tfu)]
        print(args)
        p = subprocess.Popen(
            args, cwd=bin_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, unused_stderr = p.communicate()
        output = stdout.decode()
        print(unused_stderr.decode())
        print(output)
        energy_loss = 0.0
        for line in output.split("\n"):
            try:
                (var, val) = line.split(' = ', 1)
                (x, unit) = val.split()[:2]
                x = float(x)
                if unit == 'keV':
                    x *= 1.6021766e-16
                if unit == 'MeV':
                    x *= 1.6021766e-13
                if var == 'delta E':
                    energy_loss = x
            except ValueError:
                continue
        return energy_loss
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
    bin_dir = get_bin_dir()

    # TODO refactor the way the subprocess call arguments are made
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
                command, "| awk {0} > {1}".format(
                    "'{print " + columns + "}'", output_file))
            # mac needs '' # around awk print
        else:
            command = "{0} {1}".format(
                command,
                "| awk {0} > {1}".format("\"{print " + columns + "}\"",
                                         output_file)
            )
    # print(command)
    try:
        subprocess.call(command, shell=True)
        return True
    except:
        return False


def md5_for_file(f, block_size=2 ** 20):
    """Calculates MD5 checksum for a file.
    """
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data.encode('utf8'))
    return md5.digest()


def to_superscript(string):
    """TODO"""
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


def round_value_by_four_biggest(value):
    """
    Round given value by its biggest number. E.g. 12.4 -> 10, 368 -> 400.

    Args:
        value: Value to round.

    Return:
        Rounded value.
    """
    dec_val = Decimal(value)
    dec_string_val = str(dec_val)
    if "." not in dec_string_val:
        round_val_length = len(dec_string_val)
    else:
        round_val_length = dec_string_val.index(".")
    first = dec_val / Decimal(10 ** (round_val_length - 4))
    first_round = round(first)
    sol_flnal = first_round * (10 ** (round_val_length - 4))
    return sol_flnal


def count_lines_in_file(file_path, check_file_exists=False):
    """Returns the number of newline symbols in given file (ignores last line).

    Args:
        file_path: absolute path to a file
        check_file_exists: if True, function checks if the file exists before
                           counting lines. Returns 0 if the file does not exist.

    Return:
        number of newline symbols in a file
    """
    if check_file_exists and not os.path.isfile(file_path):
        return 0

    # source: https://stackoverflow.com/a/27518377
    f = open(file_path, 'rb')
    bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
    return sum( buf.count(b'\n') for buf in bufgen )

def rawincount(self, filename):
    """
        Reads the number of lines in a text file. Used for determining the shape
        of the ndarray which holds measurement data in memory.
        Source: https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python/27518377#27518377
    """
    f = open(filename, 'rb')
    bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
    return sum( buf.count(b'\n') for buf in bufgen )


@stopwatch()
def combine_files(file_paths, destination):
    """Combines an iterable of files into a single file.
    """
    with open(destination, "w") as dest:
        for file in file_paths:
            try:
                with open(file) as src:
                    for line in src:
                        dest.write(line)
            except OSError:
                pass


def _get_external_dir() -> Path:
    """Returns absolute path to 'external' folder
    """
    root_dir = Path(__file__).parent.parent
    return (root_dir / "external").resolve()


def get_bin_dir() -> Path:
    """Returns absolute path to Potku's bin directory.
    """
    return _get_external_dir() / "bin"


def get_data_dir() -> Path:
    """Returns absolute path to Potku's data directory.
    """
    # TODO maybe add -DDEVELOPER_MODE_ENABLE=ON option to Jibal's CMake
    #   configuration and change data dir to external/data instead of
    #   external/share
    return _get_external_dir() / "share"
