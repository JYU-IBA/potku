# Potku

Potku is a simulation and analysis software for Time-of-Flight Elastic Recoil
Detection Analysis (ToF-ERDA). The software can be run on Windows, Linux and
macOS.

This repository contains the Python source for the Qt 5 graphical user
interface. Most of the number cruching is done by programs written in C.
The source code of these is separate repositories on GitHub and are included as Git [Submodules](external/submodules),
please see the instructions below on how to acquire the source code and compile the C codes e.g. if you wish to develop Potku. 

For most users it is recommended to download one of the ready to run (all dependencies included) binary packages, which are available on the [releases page](https://github.com/JYU-IBA/potku/releases).
Additionally older binary packages are available on the
[official website](https://www.jyu.fi/science/en/physics/research/infrastructures/accelerator-laboratory/pelletron/potku/).

    Copyright (C) 2013-2024 Potku developers

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
Please refer to the [full license](../LICENSE) for details. 

See the [changelog](CHANGELOG.md) for version history.

# Getting started with development
Install [Git](https://git-scm.com/downloads) and add it to the PATH (on Windows).

Clone the repository and change your current working directory.
 
```shell
$ git clone --recursive https://github.com/JYU-IBA/potku.git
$ cd potku
```

Install the latest version of Python 3.12 along with pip package installer. Make 
sure the paths of the executables are added to your PATH environment variable, i.e. you can run Python by running command `python`.

Install Pipenv:
 
```shell
$ pip install --user pipenv
```

Install and activate the virtual environment with Pipenv:

```shell
$ pipenv install --dev
$ pipenv shell
```

Once the virtual environment is up and running, Potku GUI can be launched from the 
command line:
 
```shell
$ python potku.py
```

## Compiling the C programs

The graphical user interface won't be of much use without the C programs that 
perform the depth profiling and simulation. In order to compile them, requirements for [JIBAL](https://github.com/JYU-IBA/jibal/blob/master/INSTALL.md#minimum-requirements)
should be installed. All programs use CMake build system and are included as [submodules](external/submodules) in this repository.

### Linux and macOS

Install cmake and gsl using the package manager of your distribution or 
homebrew. Then run the following:

```shell
$ cd dev
$ ./build.sh
```

to compile all programs. Note that this script has no error checking, if you encounter issues please check that all steps of the build have been successful.

### Windows

For installing the requirements for JIBAL, follow the [instructions](https://github.com/JYU-IBA/jibal/blob/master/INSTALL.md).
- Note: instead of cloning the vcpkg master branch, you can also download the latest stable release from
[here](https://github.com/microsoft/vcpkg/tags ) and then continue with

```bat
.\vcpkg\bootstrap-vcpkg.bat
vcpkg.exe install gsl:x64-windows getopt:x64-windows
```

as instructed.

To compile the programs, run

```bat
cd dev
build.bat
```

If you get errors in the build, try different command prompt i.e. `x64 Native Tools Command Prompt` as an administrator.

Also be sure that `cmake` and `vcpkg` are installed and in the `PATH`.

## Data files

JIBAL and Potku require additional data files. These can be either downloaded manually from
[here](http://users.jyu.fi/~jaakjuli/jibal/data/) or you can use the ``external_file_manager.py`` in `dev` to download the files.
These files need to be extracted to ``external/share/jibal``. You can run the 
following command from the root folder of the repository to download and 
extract the files. (note: `curl` is not installed by default on all Windows versions)

```shell
$ curl http://users.jyu.fi/~jaakjuli/jibal/data/data.tar.gz -o data.tar.gz && tar -xvf data.tar.gz -C external/share/jibal
```

## Tests

Tests are located in the `tests` package. They are divided into unit tests 
(tests that cover one or two functions at a time), integration tests 
(tests that cover multiple components) and GUI tests. GUI tests require a running 
`QApplication` instance which is created by adding `import tests.gui` at the top 
of each test module.
  
Tests have been written using unittest framework. With the virtual environment 
activated, they can be run from the root directory of the project with:

```shell
python -m unittest discover
```

## Packaging Potku into a standalone executable

Potku can be packaged into a standalone executable using [PyInstaller](https://www.pyinstaller.org/). 
Make sure you have compiled potku with `build` successfully and added the needed data files and awk before the packaging.
For quick deployment, run these commands in the root directory:
```shell
$ pipenv install #(if the virtual environment has not already been created)
$ pipenv shell
$ pip install pyinstaller
$ pyinstaller potku.spec
```
This creates a `dist/potku` folder which contains the executable and all 
necessary libraries.

For a more comprehensive packaging process, run the `create_bundle` script in `dev`. 
This script compiles all external programs, installs and updates Python 
dependencies, runs tests and compresses the `dist/potku` folder into a .zip 
archive. Run on Windows:

```bat
cd dev
pipenv run create_bundle.bat
```

or on other supported operating systems:

```shell
$ cd dev
$ pipenv run ./create_bundle.sh
```

## Automatic packaging and version numbering

Potku can be packaged automatically for Windows, Linux and macOS on GitHub servers by bumping its version. Running [bump_version.py](dev/bump_version.py) interactively (command line) prompts the user for a new version number. The script requires Git and [GitHub CLI](https://cli.github.com/) to use.

Entering a valid version number initiates a chain of GitHub Actions workflows to bump the version number, give master branch a new tag on GitHub and create
a release to which the newly packaged Potku binaries will be uploaded. Potku follows semantic version numbering.
There is more information in the [automatic packaging README](dev/Automatic_packaging_README.md).

## External file manager

A [Python script](dev/external_file_manager.py) paired with a [manifest of external files](dev/external_manifest.txt) can be used to manage Potku's external files.
The script can be used to get external files by fetching any absent and out of sync files or force downloading all files. Additionally, the script can be used to update the manifest
with local out of sync files or all local files. Finally, the script can be used to create an entirely new manifest based on the external files in [external/share](external/share).

## Code style

Potku used to follow [PEP 8](https://www.python.org/dev/peps/pep-0008/). Current maximum line length is 80 in some files, but 120 in some (see issue [#209](https://github.com/JYU-IBA/potku/issues/209) for more information).
### Code style/architecture guidelines

- add typing annotations to new (and old) code. Potku didn't originally use typing annotations.
- add tests for new features and bug fixes, if possible
- try to keep GUI code separate from the backend code as much as possible (for possible use with other frontends, and for ease of testing)

### Development process guidelines

- use pull requests and do code reviews
- create an issue for each pull request, and mention that issue number in the commit message (e.g. #1)
- remember to assign issues and add labels
- run tests before creating a pull request (and after merging it if the code changed in the meantime)
- manually test Potku before creating a pull request (and after merging it if the code changed in the meantime)

## Issues

### Timing-based tests

Some tests are timing-based. They may fail if executed too slowly or quickly.

### Tests using temporary files

Some tests in [test_general_functions.py](tests/unit/test_general_functions.py) or [test_get_espe.py](tests/unit/test_get_espe.py) may fail because of permission issues with the directory returned by `tempfile.TemporaryDirectory()`. See issue [#189](https://github.com/JYU-IBA/potku/issues/189) for more information.
