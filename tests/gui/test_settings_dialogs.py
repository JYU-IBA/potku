# coding=utf-8
"""
Created on 12.02.2020

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

from unittest.mock import MagicMock

from dialogs.request_settings import RequestSettingsDialog


class TestRequestSettings(unittest.TestCase):
    @unittest.skip
    def test_update_params(self):
        main = MagicMock()
        request = MagicMock()
        icon_manager = MagicMock()
        dialog = RequestSettingsDialog(main, request, icon_manager)

        self.assertFalse(True)


if __name__ == '__main__':
    unittest.main()