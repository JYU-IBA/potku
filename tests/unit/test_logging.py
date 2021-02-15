# coding=utf-8
"""
Created on 14.02.2021

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2021 Juhani Sundell

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
__author__ = "Juhani Sundell"
__version__ = "2.0"

import unittest
import tempfile
from logging import FileHandler
from pathlib import Path
from typing import Tuple

from modules.ui_log_handlers import (
    RequestLogger, MeasurementLogger, SimulationLogger, Logger
)


class MockLogger(Logger):
    FILE_NAME = "test.log"

    def _get_handlers(self, directory: Path) -> Tuple[FileHandler, ...]:
        return FileHandler(directory / self.FILE_NAME),


class TestLogger(unittest.TestCase):
    def test_log_file_is_created_after_set_loggers_is_called(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            log_file = tmp_dir / MockLogger.FILE_NAME

            logger = MockLogger()
            logger.set_up_log_files(tmp_dir)
            self.assertTrue(log_file.exists())

            logger.close_log_files()

    def test_close_log_files_releases_resources(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            log_file = tmp_dir / MockLogger.FILE_NAME

            logger = MockLogger()
            logger.set_up_log_files(tmp_dir)

            # log file cannot be removed because logger is keeping its
            # handle open
            self.assertRaises(OSError, lambda: log_file.unlink())

            # after calling close_log_files, we can exit the context manager
            # without exception
            logger.close_log_files()

    def test_log_file_is_not_created_if_logging_is_not_enabled(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            log_file = tmp_dir / MockLogger.FILE_NAME

            logger = MockLogger(enable_logging=False)
            logger.set_up_log_files(tmp_dir)

            self.assertFalse(log_file.exists())

    def test_directory_is_created_if_it_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            new_dir = tmp_dir / "new"

            logger = MockLogger()
            logger.set_up_log_files(new_dir)

            self.assertTrue(new_dir.exists())
            logger.close_log_files()

    def test_previous_handlers_are_closed_when_set_loggers_is_called_again(
            self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            first_dir = Path(tmp_dir, "first")
            first_file = first_dir / MockLogger.FILE_NAME

            logger = MockLogger()
            logger.set_up_log_files(first_dir)

            second_dir = Path(tmp_dir, "second")
            second_file = second_dir / MockLogger.FILE_NAME
            logger.set_up_log_files(second_dir)

            # first file can now be removed
            first_file.unlink()
            self.assertRaises(OSError, lambda: second_file.unlink())

            logger.close_log_files()

    def test_message_is_written_to_log_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            log_file = tmp_dir / MockLogger.FILE_NAME

            logger = MockLogger()
            logger.set_up_log_files(tmp_dir)
            logger.log("foo")

            expected = "foo\n"
            actual = log_file.read_text()
            self.assertEqual(expected, actual)

            logger.close_log_files()

    def test_error_is_written_to_log_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            log_file = tmp_dir / MockLogger.FILE_NAME

            logger = MockLogger()
            logger.set_up_log_files(tmp_dir)
            logger.log_error("bar")

            expected = "bar\n"
            actual = log_file.read_text()
            self.assertEqual(expected, actual)

            logger.close_log_files()

    def test_nothing_is_written_if_logging_is_not_enabled(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            log_file = tmp_dir / MockLogger.FILE_NAME

            logger = MockLogger()
            logger.set_up_log_files(tmp_dir)

            logger.is_logging_enabled = False
            logger.log("foo")
            logger.log_error("bar")

            expected = ""
            actual = log_file.read_text()
            self.assertEqual(expected, actual)

            logger.close_log_files()

    def test_message_is_not_written_if_log_file_is_closed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            log_file = tmp_dir / MockLogger.FILE_NAME

            logger = MockLogger()
            logger.set_up_log_files(tmp_dir)
            logger.close_log_files()
            logger.log("foo")

            expected = ""
            actual = log_file.read_text()
            self.assertEqual(expected, actual)

    def test_child_logger_logs_to_parent_file_too(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            parent_file = tmp_dir / MockLogger.FILE_NAME

            parent = MockLogger()
            parent.set_up_log_files(tmp_dir)

            child_dir = tmp_dir / "child"
            child_file = child_dir / MockLogger.FILE_NAME
            child = MockLogger(parent=parent)
            child.set_up_log_files(child_dir)

            child.log("foo")
            child.log_error("bar")
            parent.log("baz")

            expected_parent = "foo\nbar\nbaz\n"
            expected_child = "foo\nbar\n"
            actual_parent = parent_file.read_text()
            actual_child = child_file.read_text()
            self.assertEqual(expected_parent, actual_parent)
            self.assertEqual(expected_child, actual_child)

            parent.close_log_files()
            child.close_log_files()


class TestRequestLogger(unittest.TestCase):
    def test_log_file_is_created_after_set_loggers_is_called(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            folder = Path(tmp_dir)
            log_file = folder / "request.log"

            logger = RequestLogger()
            logger.set_up_log_files(folder)

            self.assertTrue(log_file.exists())

            logger.close_log_files()

    def test_message_is_written_to_log_file_with_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            folder = Path(tmp_dir)
            log_file = folder / "request.log"

            logger = RequestLogger()
            logger.set_up_log_files(folder)
            logger.log("foo")

            expected = r"\d\d\d\d\-\d\d-\d\d \d\d:\d\d:\d\d - INFO - foo\n"
            actual = log_file.read_text()
            self.assertRegex(actual, expected)

            logger.close_log_files()

    def test_error_message_is_written_to_log_file_with_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            folder = Path(tmp_dir)
            log_file = folder / "request.log"

            logger = RequestLogger(enable_logging=True)
            logger.set_up_log_files(folder)
            logger.log_error("bar")

            expected = r"\d\d\d\d\-\d\d-\d\d \d\d:\d\d:\d\d - ERROR - bar\n"
            actual = log_file.read_text()
            self.assertRegex(actual, expected)

            logger.close_log_files()


class TestCategorizedLoggers(unittest.TestCase):
    def test_measurement_logger_creates_log_files(self):
        logger = MeasurementLogger("mesu")
        self.assert_logger_creates_log_files(logger)

    def test_simulation_logger_creates_log_files(self):
        logger = SimulationLogger("simu")
        self.assert_logger_creates_log_files(logger)

    def assert_logger_creates_log_files(self, logger: Logger):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            info_log = tmp_dir / "default.log"
            error_log = tmp_dir / "errors.log"

            logger.set_up_log_files(tmp_dir)

            self.assertTrue(info_log.exists())
            self.assertTrue(error_log.exists())

            logger.close_log_files()

    def test_measurement_logs_are_correctly_formatted(self):
        request_logger = RequestLogger()
        measurement_logger = MeasurementLogger("mesu", parent=request_logger)
        self.assert_formatting_is_correct(
            request_logger, measurement_logger, measurement_logger.category,
            measurement_logger.display_name
        )

    def test_simulation_logs_are_correctly_formatted(self):
        request_logger = RequestLogger()
        measurement_logger = SimulationLogger("simu", parent=request_logger)
        self.assert_formatting_is_correct(
            request_logger, measurement_logger, measurement_logger.category,
            measurement_logger.display_name
        )

    def assert_formatting_is_correct(
            self, parent: Logger, child: Logger, category, display_name):
        with tempfile.TemporaryDirectory() as tmp_dir:
            parent_folder = Path(tmp_dir) / "parent"
            child_folder = Path(tmp_dir) / "child"
            request_log = parent_folder / "request.log"
            info_log = child_folder / "default.log"
            error_log = child_folder / "errors.log"

            parent.set_up_log_files(parent_folder)
            child.set_up_log_files(child_folder)
            child.log("foo")
            child.log_error("bar")

            def_regex = r"\d\d\d\d\-\d\d-\d\d \d\d:\d\d:\d\d - INFO - foo\n" \
                        r"\d\d\d\d\-\d\d-\d\d \d\d:\d\d:\d\d - ERROR - bar\n"
            err_regex = r"\d\d\d\d\-\d\d-\d\d \d\d:\d\d:\d\d - ERROR - bar\n"
            req_regex = r"\d\d\d\d\-\d\d-\d\d \d\d:\d\d:\d\d - INFO - " \
                        fr"\[{category} : {display_name}\] - foo\n" \
                        r"\d\d\d\d\-\d\d-\d\d \d\d:\d\d:\d\d - ERROR - " \
                        fr"\[{category} : {display_name}\] - bar\n"

            actual_mesu = info_log.read_text()
            self.assertRegex(actual_mesu, def_regex)

            actual_errors = error_log.read_text()
            self.assertRegex(actual_errors, err_regex)

            actual_request = request_log.read_text()
            self.assertRegex(actual_request, req_regex)

            parent.close_log_files()
            child.close_log_files()


if __name__ == '__main__':
    unittest.main()
