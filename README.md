# Potku

Potku is an analysis software for time-of-flight elastic recoil detection 
analysis (ToF-ERDA) and simulation. The software is being developed for Windows, 
Linux and Mac.

This repository contains the Python source code for Potku's graphical user 
interface as well as the source code for external C programs that perform 
most of the number crunching.

## Getting started with development

First step is to install Python 3.6 along with pip package installer. Make 
sure they are added to your PATH. Then install Pipenv:
 
````
$ pip install --user pipenv
````

Once these prerequisites are met, you can clone the repository and 
checkout the development branch to get the most up-to-date version of Potku.
 
````
$ git clone --recursive https://github.com/JYU-IBA/potku.git
$ cd potku
$ git checkout development
````

Install and activate the virtual environment with Pipenv:

````
$ pipenv install
$ pipenv shell
````

Once the virtual environment is up and running, Potku can be launched from the 
command line:
 
````
$ python run_potku.py
````

## Compiling the external C programs

The graphical user interface won't be of much use without the C programs that 
perform analysis and simulation. In order to compile them, following tools 
must be installed:

- make
- gcc
- Requirements for [Jibal](https://github.com/JYU-IBA/jibal/blob/master/INSTALL.md#minimum-requirements)

#### Linux and MacOS

Install cmake and gsl using the package manager of your distribution or 
homebrew. Then run

````
$ ./build.sh
````

to compile all programs.

#### Windows

Follow the instructions 1 - 4 described in [here](https://github.com/JYU-IBA/jibal/blob/master/INSTALL.md#installation-instructions-for-microsoft-windows-10).

To compile the programs, run

````
$ build.bat
````

#### Data files

Jibal requires additional data files, which can be downloaded from 
[here](http://users.jyu.fi/~jaakjuli/jibal/data/). 
These files need to be extracted to ``external/share/jibal``. You can run the 
following command from the root folder of the repository to download and 
extract the files.

````
$ curl http://users.jyu.fi/~jaakjuli/jibal/data/data.tar.gz -o data.tar.gz && \
tar -xvf data.tar.gz -C external/share/jibal
````

### Tests

Tests are located in the ``tests`` package. They are divided into unit tests 
(tests that cover one or two functions at a time) and integration tests 
(tests that cover multiple components).
  
Tests have been written using unittest framework. With the virtual environment 
activated, they can be run from the root directory of the project with:

````
$ python -m unittest discover
````

## Packaging Potku into an executable (work in progress)

````
$ pipenv shell
$ pip install pyinstaller
$ pyinstaller potku_[win or unix].spec
````


## Licence

Potku is licensed under GPL-2.0. See 'LICENCE' for details.