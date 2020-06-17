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
import os
import platform
import shutil
import subprocess
import tempfile
import time
import functools

from timeit import default_timer as timer
from pathlib import Path
from decimal import Decimal
from typing import Dict
from typing import List


# TODO this could still be organized into smaller modules

def stopwatch(log_file=None):
    """Decorator that measures the time it takes to execute a function
    and prints the results or writes them to a log file if one is provided
    as an argument.
    """
    def outer(func):
        @functools.wraps(func)
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


def remove_files(*file_paths):
    """Removes files.

    Args:
        *file_paths: file paths to remove
    """
    for f in file_paths:
        try:
            f.unlink()
        except OSError:
            pass


def remove_matching_files(directory, exts=None, filter_func=None):
    """Removes all files in a directory that match given conditions.

    Args:
        directory: directory where the files are located
        exts: collection of file extensions. Files with these extensions will
            be deleted.
        filter_func: additional filter function applied to the file name. If
            provided, only the files that have the correct extension and match
            the filter_func condition will be deleted.
    """
    # TODO should also allow deleting files while not declaring extensions
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


def find_files_by_extension(directory: Path, *exts) -> Dict[str, List[Path]]:
    """Searches given directory and returns files that have given extensions.

    Args:
        directory: a Path object
        exts: collection of files extensions to look for

    Return:
        dictionary where keys are strings (file extensions) and values are
        lists of Path objects.
    """
    search_dict = {
        ext: [] for ext in exts
    }
    for entry in os.scandir(directory):
        path = Path(entry.path)
        suffix = path.suffix
        if suffix in search_dict and path.is_file():
            search_dict[suffix].append(path)
    return search_dict


def hist(data, col=0, weight_col=None, width=1.0):
    """Format data into slices of given width.

    Python version of Arstila's hist code. This purpose is to format data's
    column at certain widths so the graph won't include all information.

    Args:
        data: List representation of data.
        col: column that contains the values to be histogrammed
        weight_col: column that contains weights for each row of data
        width: width of histogrammed bins.

    Return:
        Returns formatted list to use in graphs.
    """
    if not data:
        return []
    data_sliced = tuple(
        (float(row[col]), float(row[weight_col])
         if weight_col is not None else 1)
        for row in data)
    data_spliced = sorted(data_sliced, key=lambda x: x[0], reverse=False)
    data_length = len(data_sliced)

    a = int(data_spliced[0][0] / width) * width
    i = 0
    hist_list = []
    while i < data_length:
        b = 0.0
        while i < data_length and data_sliced[i][0] < a:
            b += data_spliced[i][1]
            i += 1
        hist_list.append((a - (width / 2.0), b))
        a += width

    return hist_list


def copy_file_to_temp(file: Path) -> Path:
    """Copy file into temp directory.

    Args:
        file: path to the file to copy.

    Return:
        Path to the file in temp directory.
    """
    fname = Path(file).name

    # OS specific directory where temporary MCERD files will be stored.
    # In case of Linux and Mac this will be /tmp and in Windows this will
    # be the C:\Users\<username>\AppData\Local\Temp.
    tmp_file = Path(tempfile.gettempdir(), fname)
    shutil.copyfile(file, tmp_file)
    return tmp_file


def convert_mev_to_joule(energy_in_MeV: float) -> float:
    """Converts MeV (mega electron volts) to joules.
    
    Args:
        energy_in_MeV: Value to be converted (float)
    
    Returns:
        Returns energy in MeVs (float)
    """
    # joule = 6.24150934 * pow(10, 18)  # 1 J = 6.24150934 * 10^18 eV
    joule = 6.24150934e18
    return float(energy_in_MeV) * 1000000.0 / joule


def convert_amu_to_kg(mass_in_amus: float) -> float:
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


def uniform_espe_lists(espe1, espe2, channel_width=0.025):
    """Modify given energy spectra lists to have the same amount of items.

    Return:
        Modified lists.
    """
    first = espe1
    second = espe2
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
    """Returns the number of lines in given file.

    Args:
        file_path: absolute path to a file
        check_file_exists: if True, function checks if the file exists before
                           counting lines. Returns 0 if the file does not exist.

    Return:
        number of lines in a file
    """
    if check_file_exists and not os.path.isfile(file_path):
        return 0

    # Start counting from -1 so we can return 0 if there are no lines in the
    # file
    counter = -1

    # https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a \
    # -large-file-cheaply-in-python
    with open(file_path) as f:
        # Set value of counter to the index of each line
        for counter, _ in enumerate(f):
            pass

    # Add +1 to get the total number of lines
    return counter + 1


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
    return _get_external_dir() / "share"
