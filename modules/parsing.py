# coding=utf-8
"""
Created on 15.1.2020
Updated on 27.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 TODO

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

File parsing is used for parsing files that contain csv-formatted
data.
"""
__author__ = "Juhani Sundell"
__version__ = ""    # TODO


class CSVParser:
    """CSVParser parses csv-formatted strings by splitting rows into columns
    and applying a converter function to individual column values.

    CSVParser can be used to parse a text file, collection of strings
    or a single string.

    Results can either be arranged column wise or row wise. Difference between
    the two formats can be seen by running following code snippet:

    parser = CSVParser((0, int), (1, bool))
    print(*parser.parse_strs(["1 True", "2 True", "3 True"], method="col"))
    # prints '(1, 2, 3) (True, True, True)'

    print(*parser.parse_strs(["4 False", "5 False", "6 False"], method="row"))
    # prints '(4, True) (5, True) (6, True)'
    """
    __slots__ = "converters"

    def __init__(self, *args):
        """Initializes a CSVParser.

        Args:
            args: each argument must be a tuple whose first element
                  is an integer corresponding to a column index and last
                  element is a callable that is used to convert values
                  at that column index
        """
        self.converters = tuple(_Converter(*arg)
                                for arg in args)

    def parse_file(self, file_path, separator=None, skip=0, method="col"):
        """Parses a text file.

        Args:
            file_path: path to a file
            separator: string that separates values in the file. Default is
                       None, which splits each line by whitespace
            skip: number of lines to skip at the beginning of the file
            method: either 'col' to generate a collection of columns, or
                    'row' to generate a collection of rows

        Return:
            generator that produces converted values in the given format.
        """
        with open(file_path) as file:
            # Yield from generator to avoid IO operation on closed file
            # when parsing rows.
            yield from self.parse_strs(file,
                                       separator=separator,
                                       skip=skip,
                                       method=method)

    def parse_strs(self, strs, separator=None, skip=0, method="col"):
        """Takes a collections of strings and returns a generator that
        parses the strings.

        Args:
            strs: collection of strings
            separator: string that separates values in data
            skip: number of strings to skip from the beginning
            method: either 'col' to generate a collection of columns, or
                    'row' to generate a collection of rows

        Yield:
            generator that produces converted values in the given format.
        """
        # Make an iterator out of the string collection and advance it
        # until enough lines have been skipped. If iterator is exhausted
        # its value defaults to None
        # Iterator is used here because 'strs' could either be a collection
        # or a file object. This way we can advance both types of inputs
        # with the same method.
        it = iter(strs)
        for _ in range(skip):
            next(it, None)

        # Depending on the method, pick the right function to return
        if method == "col":
            return self.__parse_as_columns(it, separator=separator)
        elif method == "row":
            return self.__parse_as_rows(it, separator=separator)
        else:
            raise ValueError("Unknown parse method '{0}'".format(str(method)))

    def __parse_as_rows(self, strs, separator=None):
        """Generates a parsed tuple for each string in the
        given collection.

        Args:
            strs: iterable of strings
            separator: string that separates values in data
        """
        for s in strs:
            yield self.parse_str(s, separator=separator)

    def __parse_as_columns(self, strs, separator=None):
        """Generates an iterator where each item is a tuple
        of values in one column.

        Args:
            strs: iterable of strings
            separator: string that separates values in data

        Return:
            generator zips column values together
        """
        # Unpack rows generated by __parse_as_rows and zip the them into
        # columns. From https://stackoverflow.com/questions/7558908/unpacking-
        # a-list-tuple-of-pairs-into-two-lists-tuples
        return zip(*self.__parse_as_rows(strs, separator=separator))

    def parse_str(self, s, separator=None):
        """Splits a string into pieces and converts values from
        it using CSVParsers conversion functions.

        Args:
            s: string to be parsed
            separator: string that separates values in the string

        Return:
            tuple of converted values
        """

        lst = s.split(separator)
        return tuple(convert(lst) for convert in self.converters)


class _Converter:
    """Helper class for CSVParsing. Applies a conversion function to
    list item at certain and returns the result.
    """
    __slots__ = "idx", "func"

    def __init__(self, idx, func):
        """Initializes a new _Converter.

        Args:
            idx: index of the value in a list (must be an integer)
            func: conversion function that will be applied to the
                  value (must be callable)
        """
        if not isinstance(idx, int):
            raise TypeError("List index must be an integer")
        if not callable(func):
            raise TypeError("Converter must be callable")

        self.idx = idx
        self.func = func

    def __call__(self, lst):
        """Applies the conversion function to a list item.

        Args:
            lst: a collection of values

        Returns:
            converted value
        """
        return self.func(lst[self.idx])


if __name__ == "__main__":
    # For testing purposes
    parser = CSVParser((0, int), (1, bool))
    print(*parser.parse_strs(["1 True", "2 True", "3 True"], method="col"))
    print(*parser.parse_strs(["4 False", "5 False", "6 False"], method="row"))
