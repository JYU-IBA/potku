# coding=utf-8
"""
Created on 16.05.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2022 Juhani Sundell & Joonas Koponen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell & Joonas Koponen"
__version__ = "2.0"

import tempfile

import unittest
from pathlib import Path
import tests.mock_objects as mo

from modules.request import Request


class ImportFilesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.request_kwargs = {
            "save_on_creation": False,
            "enable_logging": False,
            "global_settings": mo.get_global_settings(),
            "name": "import_test_request",
        }

    @staticmethod
    def create_external_file(folder: Path, file: str = "foo.txt") -> Path:
        contents = """
            foo bar baz
        """
        file_path = folder / file
        with file_path.open("w") as file:
            file.write(contents)
        return file_path


class TestImportingExternalFiles(ImportFilesTestCase):
    def test_import_folder_is_created_when_file_is_imported(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)

            self.assertFalse(request.get_imported_files_folder().exists())
            request.import_external_file(external_file)
            self.assertTrue(request.get_imported_files_folder().exists())

    def test_name_of_the_imported_file_is_returned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)

            expected = Path(
                request.get_imported_files_folder(),
                external_file.name
            )
            actual = request.import_external_file(external_file)
            self.assertEqual(expected, actual)

    def test_imported_file_is_copied_over_to_import_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)

            imported_file = request.import_external_file(external_file)
            self.assertTrue(imported_file.exists())
            self.assertEqual(
                external_file.read_text(), imported_file.read_text()
            )

    def test_error_is_raised_if_external_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = tmp_dir / "foo.txt"

            self.assertRaises(
                OSError, lambda: request.import_external_file(external_file)
            )

    def test_error_is_raised_if_external_file_is_a_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = tmp_dir / "foo.txt"
            external_file.mkdir()

            self.assertRaises(
                OSError, lambda: request.import_external_file(external_file)
            )

    def test_error_is_raised_if_file_with_same_name_has_already_been_imported(
            self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)

            request.import_external_file(external_file)
            self.assertFalse(request.import_external_file(external_file))


class TestRemovingExternalFiles(ImportFilesTestCase):
    def test_file_can_be_removed_by_providing_full_path_to_imported_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)
            imported_file = request.import_external_file(external_file)

            self.assertTrue(imported_file.exists())
            request.remove_external_file(imported_file)
            self.assertFalse(imported_file.exists())

    def test_file_can_be_removed_by_providing_the_name_of_the_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)
            imported_file = request.import_external_file(external_file)

            self.assertTrue(imported_file.exists())
            request.remove_external_file(Path(imported_file.name))
            self.assertFalse(imported_file.exists())

    def test_error_is_raised_if_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)
            imported_file = request.import_external_file(external_file)

            non_existing_file = imported_file.with_name(
                f"{imported_file.name}_that_does_not_exist")

            self.assertFalse(request.remove_external_file(non_existing_file))

    def test_error_is_raised_if_the_file_is_not_in_import_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            external_file = self.create_external_file(tmp_dir)
            request.import_external_file(external_file)

            self.assertFalse(request.remove_external_file(external_file))


class TestListingImportedFiles(ImportFilesTestCase):
    def test_empty_list_is_returned_if_import_folder_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)

            self.assertFalse(request.get_imported_files_folder().exists())
            self.assertEqual([], request.get_imported_files())

    def test_empty_list_is_returned_if_the_folder_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)

            request.get_imported_files_folder().mkdir()
            self.assertEqual([], request.get_imported_files())

    def test_imported_files_are_returned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            imported_files = []
            for i in range(10):
                external_file = self.create_external_file(
                    tmp_dir, f"foo_{i}.txt")
                imported_file = request.import_external_file(external_file)
                imported_files.append(imported_file)

            self.assertEqual(
                imported_files,
                sorted(request.get_imported_files())
            )

    def test_folders_are_not_returned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            request = Request(directory=tmp_dir, **self.request_kwargs)
            folder = request.get_imported_files_folder() / "foo"
            folder.mkdir(parents=True)

            self.assertEqual([], request.get_imported_files())
