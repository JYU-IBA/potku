# coding=utf-8
"""
Created on 15.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell

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
__version__ = "2.0"


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
    __slots__ = "_converters", "_filter_functions"
    # parsing options
    ROW = "row"
    COLUMN = "col"

    # ignore options
    EMPTY = "e"
    WHITESPACE = "w"

    def __init__(self, *args):
        """Initializes a CSVParser.

        Args:
            args: each argument must be a tuple whose first element
                  is an integer corresponding to a column index and last
                  element is a callable that is used to convert values
                  at that column index
        """
        # Converters are used to convert values within strings
        self._converters = tuple(_get_conversion_function(*arg)
                                 for arg in args)

        # These are functions given to a filter function, when parsing multiple
        # strings:
        # if ignore mode is None, use a function that always returns True.
        # if the mode is 'e', return the string itself to check if it is empty
        # if the mode is 'w', strip leading and trailing whitespace to check
        # if the remaining string is empty.
        self._filter_functions = {
            None: lambda _: True,
            "e": lambda x: x,
            "w": lambda x: x.strip()
        }

    def parse_file(self, file_path, separator=None, skip=0,
                   ignore=None, method=COLUMN):
        """Parses lines from text file.

        Args:
            file_path: path to a file
            separator: string that separates values in the file. Default is
                       None, which splits each line by whitespace
            skip: number of lines to skip at the beginning of the file
            ignore: ignore mode. Determines which lines are ignored if any.
                    Valid values are None for none, 'e' for empty lines and 'w'
                    for lines containing only whitespace characters.
            method: either 'col' to generate a collection of columns, or
                    'row' to generate a collection of rows

        Yield:
            values parsed from given text file
        """
        with open(file_path) as file:
            # Yield from generator to avoid IO operation on closed file
            # when parsing rows.
            yield from self.parse_strs(file,
                                       separator=separator,
                                       skip=skip,
                                       ignore=ignore,
                                       method=method)

    def parse_strs(self, strs, separator=None, skip=0, ignore=None,
                   method=COLUMN):
        """Takes a collections of strings and returns a generator that
        parses the strings.

        Args:
            strs: collection of strings
            separator: string that separates values in data
            skip: number of strings to skip from the beginning
            ignore: ignore mode. Determines which strings are ignored if any.
                    Valid values are None for none, 'e' for empty strings and
                    'w' for strings containing only whitespace characters.
            method: either 'col' to generate a collection of columns, or
                    'row' to generate a collection of rows

        Return:
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
        if method == CSVParser.COLUMN:
            return self._parse_as_columns(it, separator=separator,
                                          ignore=ignore)
        elif method == CSVParser.ROW:
            return self._parse_as_rows(it, separator=separator,
                                       ignore=ignore)
        else:
            raise ValueError(
                f"Unknown parse method '{method}' given to CSVParser")

    def _parse_as_rows(self, strs, separator=None, ignore=None):
        """Generates a parsed tuple for each string in the
        given collection.

        Args:
            strs: iterable of strings
            separator: string that separates values in data
            ignore: ignore mode. None for none, 'e' for empty strings and 'w'
                    for whitespace characters.

        Yield:
            tuple of parsed values in each string
        """
        if ignore not in self._filter_functions:
            raise ValueError("Unknown ignore mode '{0}' given to "
                             "CSVParser".format(ignore))

        for s in filter(self._filter_functions[ignore], strs):
            yield self.parse_str(s, separator=separator)

    def _parse_as_columns(self, strs, **kwargs):
        """Generates an iterator where each item is a tuple
        of values in one column.

        Args:
            strs: iterable of strings
            kwargs: keyword arguments to be passed down to __parse_rows

        Return:
            generator that zips column values together
        """
        # Unpack rows generated by __parse_as_rows and zip the them into
        # columns. From https://stackoverflow.com/questions/7558908/unpacking-
        # a-list-tuple-of-pairs-into-two-lists-tuples
        return zip(*self._parse_as_rows(strs, **kwargs))

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
        return tuple(convert(lst) for convert in self._converters)


class ToFListParser(CSVParser):
    """Default parser for reading data in the format produced by tofe_list"""
    __slots__ = ()

    def __init__(self):
        """Initializes a ToFListParses.
        """
        # tofe_list produces 8 columns and n rows of data.
        super().__init__((0, float),
                         (1, float),
                         (2, float),
                         (3, int),
                         (4, float),
                         (5, str),
                         (6, float),
                         (7, int))


def _get_conversion_function(idx, func):
    """Returns a function that will be applied to a list element
    at a given index.

    Args:
        idx: index of the element in a list
        func: function to be applied to the element

    Return:
        callable that takes a list and applies a function to a single element.
    """
    if not isinstance(idx, int):
        raise TypeError("List index must be an integer")
    if not callable(func):
        raise TypeError("Converter must be callable")

    return lambda lst: func(lst[idx])
