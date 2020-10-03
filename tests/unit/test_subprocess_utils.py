# coding=utf-8
"""
Created on 02.10.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = ""  # TODO
__version__ = ""  # TODO

import unittest
import tempfile
import subprocess
from pathlib import Path
import tests.utils as utils

from modules.subprocess_utils import StdoutStream
import modules.subprocess_utils as sutils


class TestStdoutStream(unittest.TestCase):
    def setUp(self) -> None:
        # set stderr to DEVNULL to suppress error messages
        self.default_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.DEVNULL,
            "universal_newlines": True,
        }

    def test_basic_case(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:

            stream = StdoutStream(proc)
            self.assertEqual(["hello\n"], list(stream))

    def test_stream_as_context_manager(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:
            with StdoutStream(proc) as stream:
                self.assertIsInstance(stream, StdoutStream)
                self.assertEqual(["hello\n"], list(stream))

    def test_closing_stream_closes_the_stdout(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:

            stream = StdoutStream(proc)
            self.assertFalse(proc.stdout.closed)
            stream.close()
            self.assertTrue(proc.stdout.closed)

    def test_stream_closed_equals_stdout_close(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:

            stream = StdoutStream(proc)
            self.assertEqual(proc.stdout.closed, stream.closed)
            stream.close()
            self.assertEqual(proc.stdout.closed, stream.closed)

    def test_stream_cannot_be_processed_after_closing(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:

            stream = StdoutStream(proc)
            stream.close()
            self.assertRaises(ValueError, lambda: list(stream))

    def test_closing_twice_is_a_noop(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:

            stream = StdoutStream(proc)
            stream.close()
            stream.close()
            self.assertTrue(stream.closed)

    def test_error_raised_when_stdout_is_none(self):
        kwargs = dict(self.default_kwargs)
        # Using DEVNULL so the output is not printed to console when
        # running the test. The outcome of the test is the same if
        # stdout is set to None.
        kwargs["stdout"] = subprocess.DEVNULL
        with subprocess.Popen(["echo", "hello"], **kwargs) as proc:
            self.assertRaises(AttributeError, lambda: StdoutStream(proc))


class TestWriteToFile(unittest.TestCase):
    def test_file_is_not_written_until_iterable_is_processed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            sutils.write_to_file(["kissa"], file)
            self.assertFalse(file.exists())

    def test_iterable_is_written_to_file_when_processed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            # call list to exhaust the iterable
            list(sutils.write_to_file(["kissa"], file))
            with file.open("r") as f:
                self.assertEqual(["kissa"], f.readlines())

    def test_write_to_file_does_not_add_newlines(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            list(sutils.write_to_file(["kissa", "istuu"], file))
            with file.open("r") as f:
                self.assertEqual(["kissaistuu"], f.readlines())

    def test_partial_exhaustion_leaves_file_handle_open(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            xs = sutils.write_to_file(["kissa", "istuu"], file)

            next(xs)
            # unlinking raises error as the file handle is still open
            self.assertRaises(OSError, file.unlink)

            # after exhausting the iterable, file can be removed
            list(xs)
            file.unlink()
            self.assertFalse(file.exists())

    def test_text_func(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")

            list(sutils.write_to_file(
                ["kissa"], file, text_func=lambda x: x[::-1]))

            with file.open("r") as f:
                self.assertEqual(["assik"], f.readlines())

    def test_text_func_does_not_change_output(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")

            xs = list(sutils.write_to_file(
                ["kissa"], file, text_func=lambda x: x[::-1]))

            self.assertEqual(["kissa"], xs)

    def test_existing_file_is_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            with file.open("w") as f:
                f.write("istuu")

            list(sutils.write_to_file(["kissa"], file))
            with file.open("r") as f:
                self.assertEqual(["kissa"], f.readlines())

    def test_writing_to_non_existing_folder_raises_exception(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "baz", "foo.bar")

            lines = sutils.write_to_file(["kissa"], file)
            self.assertRaises(OSError, lambda: list(lines))

    def test_giving_a_folder_as_input_raises_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir)

            lines = sutils.write_to_file(["kissa"], file)
            self.assertRaises(OSError, lambda: list(lines))

    def test_no_text_func_raises_an_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")

            lines = sutils.write_to_file([], file, text_func=None)
            self.assertRaises(ValueError, lambda: list(lines))


class TestProcessOutput(unittest.TestCase):
    def setUp(self) -> None:
        self.default_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.DEVNULL,
            "universal_newlines": True,
        }

    def test_basic_case(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:
            xs = sutils.process_output(proc)
            self.assertEqual(["hello\n"], xs)

    def test_set_as_output_func(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:
            xs = sutils.process_output(proc, output_func=set)
            self.assertEqual({"hello\n"}, xs)

    def test_tuple_as_output_func(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:
            xs = sutils.process_output(proc, output_func=tuple)
            self.assertEqual(("hello\n",), xs)

    def test_none_as_output_func_raises_exception(self):
        with subprocess.Popen(
                ["echo", "hello"], **self.default_kwargs) as proc:
            self.assertRaises(
                TypeError,
                lambda: sutils.process_output(proc, output_func=None))

    def test_parse_func(self):
        def parse_func(line):
            line = line.split(",")
            return tuple(int(x) for x in line)

        with subprocess.Popen(
                ["echo", "1,2,3"], **self.default_kwargs) as proc:
            xs = sutils.process_output(proc, parse_func=parse_func)
            self.assertEqual([(1, 2, 3)], xs)

    def test_processed_output_is_written_to_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            with subprocess.Popen(
                    ["echo", "1,2,3"], **self.default_kwargs) as proc:
                sutils.process_output(proc, file=file)
                with file.open("r") as f:
                    self.assertEqual(["1,2,3\n"], f.readlines())

    def test_parse_func_is_applied_before_text_func(self):
        def parse_func(line):
            xs = line.split(",")
            return tuple(int(x)**2 for x in xs)

        def text_func(tpl):
            x, y, z = tpl
            return f"{z}-{y}-{x}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            with subprocess.Popen(
                    ["echo", "1,2,3"], **self.default_kwargs) as proc:
                xs = sutils.process_output(
                    proc, file=file, text_func=text_func, parse_func=parse_func)

                self.assertEqual([(1, 4, 9)], xs)
                with file.open("r") as f:
                    self.assertEqual(["9-4-1"], f.readlines())

    def test_multiline(self):
        input_file = utils.get_resource_dir() / "foils_file.txt"

        with tempfile.TemporaryDirectory() as tmp_dir:
            file = Path(tmp_dir, "foo.bar")
            with subprocess.Popen(
                    ["cat", str(input_file)], **self.default_kwargs) as proc:
                xs = sutils.process_output(proc, file=file)

                self.assertTrue(1 < len(xs))
                with input_file.open("r") as f0, file.open("r") as f1:
                    f0_contents = f0.readlines()
                    f1_contents = f1.readlines()
                    utils.assert_all_equal(xs, f0_contents, f1_contents)


if __name__ == '__main__':
    unittest.main()
