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
Sinikka Siironen, 2020 Juhani Sundell

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
import pathlib
import platform
import shutil
import subprocess
import tempfile
import time
import functools
import sys

from timeit import default_timer as timer
from pathlib import Path
from decimal import Decimal
from typing import Dict
from typing import List
from typing import Set
from typing import Callable
from typing import Optional
from typing import Union
from typing import Iterable
from typing import Tuple
from typing import TypeVar

from . import subprocess_utils as sutils

T = TypeVar("T")


# TODO this could still be organized into smaller modules

def stopwatch(log_file: Optional[Path] = None):
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
                with log_file.open("a") as file:
                    file.write(msg)
            return res
        return inner
    return outer


def profile(func):
    """Decorator that prints cProfiler information about a decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import cProfile
        import pstats

        pr = cProfile.Profile()
        pr.enable()

        res = func(*args, **kwargs)

        pr.disable()
        ps = pstats.Stats(pr)
        ps.sort_stats("time")
        ps.print_stats(10)
        return res
    return wrapper


def rename_file(old_path: Path, new_name: Union[str, Path]) -> Path:
    """Renames file or directory and returns new path.

    Args:
        old_path: Path of file or directory to rename.
        new_name: New name for the file or directory.
    """
    if not new_name:
        return
    dir_path = old_path.parent
    new_file = Path(dir_path, new_name)
    old_path.rename(new_file)
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


def remove_matching_files(directory: Path, exts: Optional[Set[str]] = None,
                          filter_func: Optional[Callable] = None):
    """Removes all files in a directory that match given conditions.

    Args:
        directory: directory where the files are located
        exts: collection of file extensions. Files with these extensions will
            be deleted.
        filter_func: additional filter function applied to the file name.
    """
    # TODO change the filter function so that it takes the Path as an argument,
    #   not just file name.
    def _filter_func(fp: Path):
        if exts is not None and filter_func is None:
            return fp.suffix in exts
        if exts is None:
            return filter_func(fp.name)
        return fp.suffix in exts and filter_func(fp.name)

    try:
        with os.scandir(directory) as sdir:
            for entry in sdir:
                path = Path(entry.path)
                if _filter_func(path):
                    remove_files(path)
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
    with os.scandir(directory) as scdir:
        for entry in scdir:
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
    data_sliced = sorted(data_sliced, key=lambda x: x[0], reverse=False)
    data_length = len(data_sliced)

    a = int(data_sliced[0][0] / width) * width
    i = 0
    hist_list = []
    while i < data_length:
        b = 0.0
        while i < data_length and data_sliced[i][0] < a:
            b += data_sliced[i][1]
            i += 1
        hist_list.append((a - width, b))
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


def coinc(input_file: Path, skip_lines: int, tablesize: int,
          trigger: int, adc_count: int, timing: Dict[str, Tuple[int, int]],
          output_file: Optional[Path] = None, columns: str = "$3,$5",
          nevents: int = 0, timediff: bool = True, verbose: bool = True) -> \
        List[str]:
    """Calculate coincidences of file.

    Args:
        input_file: Path to input file.
        skip_lines: An integer representing how many lines from the beginning
                    of the file is skipped.
        tablesize: An integer representing how large table is used to calculate
                   coincidences.
        trigger: An integer representing trigger ADC.
        adc_count: An integer representing the count of ADCs.
        timing: A dict consisting of (min, max) representing different ADC
                timings.
        output_file: Path to destination file. If None, the results will not
            be written to file.
        columns: Columns to parse from output.
        nevents: An integer representing limit of how many events will the
                 program look for. 0 means no limit.
        timediff: A boolean representing whether timediff is output or not.
        verbose: Whether errors are printed to console or not.

    Return:
        The output of coinc as a list
    """
    # TODO consider replacing awk with something else so there is no need to
    #   rely on an external dependency. Parsing individual lines with CSVParser
    #   is too slow.
    timings = (
        (f"--low={key},{low}", f"--high={key},{high}")
        for key, (low, high) in timing.items()
    )
    timings = [s for tpl in timings for s in tpl]

    col_split = columns.split(',')
    if not (all(col_split) and timings):
        return []

    if timediff:
        timediff_str = "--timediff"
    else:
        timediff_str = ""

    bin_dir = get_bin_dir()

    if platform.system() != "Windows":
        executable = "./coinc"
        awk_cmd = "awk", f"{{print {columns}}}"
    else:
        executable = bin_dir / "coinc.exe"
        awk_cmd = str(get_bin_dir() / "awk.exe"), f"{{print {columns}}}"

    coinc_cmd = (
        str(executable),
        "--silent",
        f"--skip={skip_lines}",
        f"--tablesize={tablesize}",
        f"--trigger={trigger}",
        f"--nadc={adc_count}",
        timediff_str,
        *timings,
        f"--nevents={nevents}",
        str(input_file),
    )

    kwargs = {
        "cwd": bin_dir,
        "stdout": subprocess.PIPE,
        "stderr": None if verbose else subprocess.DEVNULL,
        "universal_newlines": True,
    }

    try:
        with subprocess.Popen(coinc_cmd, **kwargs) as coinc_proc:
            with subprocess.Popen(
                    awk_cmd, stdin=coinc_proc.stdout, **kwargs) as awk_proc:
                data = sutils.process_output(awk_proc, file=output_file)
                return data
    except OSError:
        return []


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


_SUPERSCRIPTED_DIGITS = {
    "0": "\u2070",
    "1": "\xb9",
    "2": "\xb2",
    "3": "\xb3",
    "4": "\u2074",
    "5": "\u2075",
    "6": "\u2076",
    "7": "\u2077",
    "8": "\u2078",
    "9": "\u2079",
}


def digits_to_superscript(string: str) -> str:
    """Changes all digits in given string to superscript,
    i.e. 'cm3' => 'cm³'.
    """
    return "".join(_SUPERSCRIPTED_DIGITS.get(char, char) for char in string)


def lower_case_first(s: str) -> str:
    """Returns a string where the first character is lower cased.
    """
    return s[0].lower() + s[1:] if s else ""


def find_nearest(x, lst):
    """Find given list's nearest point's x coordinate from x.

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
    """Format given integer into binary of a certain length.

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


def count_lines_in_file(file_path: Path, check_file_exists=False):
    """Returns the number of lines in given file.

    Args:
        file_path: absolute path to a file
        check_file_exists: if True, function checks if the file exists before
            counting lines. Returns 0 if the file does not exist.

    Return:
        number of lines in a file
    """
    # Start counting from -1 so we can return 0 if there are no lines in the
    # file
    counter = -1

    # https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a \
    # -large-file-cheaply-in-python
    try:
        with file_path.open("r") as f:
            # Set value of counter to the index of each line
            for counter, _ in enumerate(f):
                pass
    except FileNotFoundError:
        if not check_file_exists:
            raise

    # Add +1 to get the total number of lines
    return counter + 1


def combine_files(file_paths: Iterable[Path], destination: Path):
    """Combines an iterable of files into a single file.
    """
    with destination.open("w") as dest:
        for file in file_paths:
            try:
                with file.open("r") as src:
                    for line in src:
                        dest.write(line)
            except OSError:
                pass


def rename_entity(entity: Union["Measurement", "Simulation"], new_name):
    # TODO this method should be in a common base class for Measurement
    #   and Simulation objects
    try:
        new_folder = entity.DIRECTORY_PREFIX + "%02d" % \
            entity.serial_number + "-" + new_name

        # Close and remove logs
        entity.close_log_files()

        new_dir = rename_file(entity.directory, new_folder)
        entity.name = new_name
        entity.update_directory_references(new_dir)
    except OSError as e:
        e.args = f"Failed to rename measurement folder {new_name}",
        raise


def _get_external_dir() -> Path:
    """Returns absolute path to 'external' folder
    """
    return get_root_dir() / "external"


def get_bin_dir() -> Path:
    """Returns absolute path to Potku's bin directory.
    """
    return _get_external_dir() / "bin"


def get_data_dir() -> Path:
    """Returns absolute path to Potku's data directory.
    """
    return _get_external_dir() / "share"


# When running Potku as a bundle created by PyInstaller, the absolute path
# to root folder is stored as the value of sys._MEIPASS attribute:
# https://pyinstaller.readthedocs.io/en/stable/runtime-information.html?
#   highlight=bundle
_ROOT_DIR = Path(
    getattr(sys, "_MEIPASS", Path(__file__).parent.parent)
).resolve()


def get_root_dir() -> Path:
    """Returns the absolute path to Potku's root directory.
    """
    return _ROOT_DIR


def find_next(iterable: Iterable[T], cond: Callable[[T], bool]) -> T:
    """Returns the next item in the iterable that matches given condition.
    """
    try:
        return next(i for i in iterable if cond(i))
    except StopIteration:
        raise ValueError("Value not found in iterable.")


def check_if_sum_in_directory_name(directory):
    """
    Check if a directory name contains "SUM" string.

    Args:
        directory: Directory that is iterated

    Return:
        True if there is at least one directory name contains "SUM" string.
        False if there is not.

    """
    measured_sum_found = False
    simulated_sum_found = False
    with os.scandir(directory) as s_dir:
        for entry in s_dir:
            if entry.name.startswith("MEASURED_SUM"):
                measured_sum_found = True
            if entry.name.startswith("SIMULATED_SUM"):
                simulated_sum_found = True
    return measured_sum_found, simulated_sum_found


def get_version_number_and_date():
    """
    Returns Potku's version number and date of the version from version.txt

    Return:
        version_number: semantic version number
        version_date: dd.mm.yyyy format date of the version
    """
    root_dir = get_root_dir()
    version_file_path = pathlib.Path.joinpath(root_dir, r'version.txt')
    version_number = '2.0'
    version_date = '31.12.2022'
    try:
        version_file = open(version_file_path, 'r')
        version_file_content = version_file.read().splitlines()
        version_number = version_file_content[0]
        version_date = version_file_content[1]
        version_file.close()
    except FileNotFoundError:
        return version_number, version_date
    except IndexError:
        return version_number, version_date

    return version_number, version_date
