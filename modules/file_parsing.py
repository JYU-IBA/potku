# coding=utf-8
"""
Created on 15.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 TODO

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

DepthFiles.py creates the files necessary for generating depth files.
Also handles several tasks necessary for operating with depth files.
"""
__author__ = ""     # TODO
__version__ = ""


def parse_file(file_path, col_idxs, converters, separator=None, skip_lines=0):
    """Parses file into columns.

    Any column index that is outside the column range raises exception.
    Any exceptions in conversions should be handled by converter functions.

    Args:
        file_path: absolute path to a file
        col_idxs: collection of column indexes that will be parsed
        from the file
        converters: collection of converter functions that are used
        to convert column values
        separator: string that separates columns in file
        skip_lines: number of lines to skip from the beginning of the
        file

    Returns:
        tuple of lists that contain the values parsed from given columns
    """
    # TODO possibly parse headers if they exist
    skip_lines = skip_lines if skip_lines >= 0 else 0
    with open(file_path) as file:
        for _ in range(skip_lines):
            next(file)
        lines = parse_strs(
            file, col_idxs, converters, separator=separator)

    return lines


def parse_strs(strs, col_idxs, converters, separator=None):
    """Parses strings into columns.

    Args:
        strs: iterable of strings to parse
        col_idxs: collection of column indexes to parse from
        strings
        converters: collection of converter functions
        separator: string that separates columns in data

    Returns:
        tuple of lists that contains the values of each
        parsed column
    """
    parsed_lines = tuple([] for _ in col_idxs)
    for s in strs:
        cols = parse_str(s, col_idxs, converters, separator=separator)
        for i in range(len(cols)):
            parsed_lines[i].append(cols[i])
    return parsed_lines


def parse_str(s, col_idxs, converters, separator=None):
    """Parses columns from a string and converts the values with
    given conversion functions.

    Args:
        s: string to be parsed
        col_idxs: collection of column indexes that will be parsed from string
        converters: collection of converter functions to convert
        column values
        separator: string that separates columns in the file

    Returns:
        tuple of parsed columns
    """
    if len(col_idxs) != len(converters):
        raise ValueError("Number of column indexes must match the number of "
                         "converter functions.")

    lst = s.split(separator)

    return tuple(converters[i](lst[col_idxs[i]]) for i in range(len(col_idxs)))
