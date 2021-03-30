# Potku

Potku is a simulation and analysis software for time-of-flight elastic recoil
detection analysis (ToF-ERDA). The software can be run on Windows, Linux and
macOS.

This repository contains the Python source code for Potku's graphical user
interface (Qt5) as well as the source code for programs that perform most of
the number crunching, written in C. Some of these software are in separate
submodules, please see the instructions below if you want to run the
development version.

Ready to run binary packages are available are available on the 
[official website](https://www.jyu.fi/science/en/physics/research/infrastructures/accelerator-laboratory/pelletron/potku/).

    Copyright (C) 2013-2021 Potku developers

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
Please refer to the [full license](LICENSE) for details.

# Getting started with development

First step is to install Python 3.6 along with pip package installer. Make 
sure the paths of the executables are added to your PATH environment variable. Then install Pipenv:
 
````
$ pip install --user pipenv
````
Next install [Git](https://git-scm.com/downloads) and add it to the PATH too.

Once these prerequisites are met, you can clone the repository.
 
````
$ git clone --recursive https://github.com/JYU-IBA/potku.git
$ cd potku
````

Install and activate the virtual environment in `potku/` root directory with Pipenv:

````
$ pipenv install
$ pipenv shell
````

Once the virtual environment is up and running, Potku GUI can be launched from the 
command line:
 
````
$ python run_potku.py
````

## Compiling the C programs

The graphical user interface won't be of much use without the C programs that 
perform the depth profiling and simulation. In order to compile them, following tools 
must be installed:

- make
- gcc
- Requirements for [Jibal](https://github.com/JYU-IBA/jibal/blob/master/INSTALL.md#minimum-requirements)

### Linux and macOS

Install cmake and gsl using the package manager of your distribution or 
homebrew. Then run

````
$ ./build.sh
````

to compile all programs. Note that this script has no error checking, if you encounter issues please check that all steps of the build have been successful.

### Windows

For installing the requirements for the Jibal, follow the instructions 1 - 4 described in [here](https://github.com/JYU-IBA/jibal/blob/master/INSTALL.md#installation-instructions-for-microsoft-windows-10).

- Note: instead of cloning the vcpkg master branch, download the latest stable release from
[here](https://github.com/microsoft/vcpkg/tags ) and then continue with
````
.\vcpkg\bootstrap-vcpkg.bat
vcpkg.exe install gsl:x64-windows getopt:x64-windows
````
as instructed.

For make and gcc see [c_for_windows_example.md](c_for_windows_example.md) for an example on how to set up the rest of the C environment .

To compile the programs, run

````
$ build.bat
````

in the `potku/` root directory 

If you get errors in the build, try different command prompt ie. x64 Native Tools Command Prompt as an administrator.

Also be sure that make, gcc, cmake and vcpkg are installed and in the PATH

In case of warnings but no errors, try running the build again.


## Data files

Jibal requires additional data files, which can be downloaded from 
[here](http://users.jyu.fi/~jaakjuli/jibal/data/). 
These files need to be extracted to ``external/share/jibal``. You can run the 
following command from the root folder of the repository to download and 
extract the files. (note: `curl` is not installed by default on all windows versions)

````
$ curl http://users.jyu.fi/~jaakjuli/jibal/data/data.tar.gz -o data.tar.gz && \
tar -xvf data.tar.gz -C external/share/jibal
````

Potku requires `srim2013.tot` in `external/share/` for some operations. This 
file can be copied from a 
[binary distribution of Potku](https://www.jyu.fi/science/en/physics/research/infrastructures/accelerator-laboratory/pelletron/potku/release_versions)
or generated with 
[Potku-gsto](https://github.com/JYU-IBA/potku/tree/master/external/Potku-gsto) 
(no instructions available). `srim2013.tot` will be phased out in the future.

## External dependencies

Potku needs a copy of AWK to import data. It is probably installed on Linux 
systems and possibly macOS too. Windows users will need to manually download
it. [GNU AWK](https://www.gnu.org/software/gawk/) is tested and confirmed to be
working on Windows.

Place AWK under `potku/external/bin/`. The executable must be named `awk` or 
(`awk.exe` on Windows) for Potku detect and use it.


## Tests

Tests are located in the `tests` package. They are divided into unit tests 
(tests that cover one or two functions at a time), integration tests 
(tests that cover multiple components) and GUI tests. GUI tests require a running 
`QApplication` instance which is created by adding `import tests.gui` at the top 
of each test module.
  
Tests have been written using unittest framework. With the virtual environment 
activated, they can be run from the root directory of the project with:

````
$ python -m unittest discover
````

## Packaging Potku into a standalone executable (work in progress)

Potku can be packaged into a standalone executable using [PyInstaller](https://www.pyinstaller.org/). 
Make sure you have compiled potku with `build` successfully and added the needed data files and awk before the packaging.
For quick deployment, run these commands:
````
$ pipenv install (if the virtual environment has not already been created)
$ pipenv shell
$ pip install pyinstaller
$ pyinstaller potku.spec
````
This creates a `dist/potku` folder which contains the executable and all 
necessary libraries.

For a more comprehensive packaging process, run the `create_bundle` script. 
This script compiles all external programs, installs and updates Python 
dependencies, runs tests and compresses the `dist/potku` folder into a .zip 
archive.

`````
$ pipenv run create_bundle.bat
`````

or

`````
$ pipenv run ./create_bundle.sh
`````

## Licence

Potku is licensed under GNU General Public License. See [LICENSE](LICENSE) for details.
