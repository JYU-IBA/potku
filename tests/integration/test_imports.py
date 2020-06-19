# coding=utf-8
"""
Created on 03.06.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020

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
import os
import sys
import tests.utils as utils
import modules.general_functions as gf

from pathlib import Path


class TestImports(unittest.TestCase):
    @utils.change_wd_to_root
    @unittest.skipIf(
        gf.get_root_dir().name != "potku",
        reason="In order to run the import test, Potku's root directory must "
               "be called 'potku'")
    @unittest.skipIf(
        gf.get_root_dir().parent == Path("/"),
        reason="Cannot run import test as Potku is located in the root folder "
               "of the file system.")
    def test_importing_modules(self):
        """Tests that modules are not imported twice when they are
        imported from a working directory above Potku's root directory.
        """
        # Remove Potku root from sys.path and add its parent
        potku_root = gf.get_root_dir()
        try:
            sys.path.remove(str(potku_root))
        except ValueError:
            pass
        sys.path.append(str(potku_root.parent))

        os.chdir(potku_root.parent)
        # Import masses using folder. NOTE: Intellisense will flag these as
        # unresolved references, but these should work during runtime
        import potku.modules.masses as m1
        from potku.modules.element import masses as m2
        self.assertIs(m1, m2)

        from potku.modules.base import MCERDParameterContainer as Mpc1
        from potku.modules.element import MCERDParameterContainer as Mpc2
        self.assertIs(Mpc1, Mpc2)


if __name__ == '__main__':
    unittest.main()
