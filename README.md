# Potku

Potku is an analysis software for time-of-flight elastic recoil detection 
analysis (ToF-ERDA) and simulation. The software is being developed for Windows, 
Linux and Mac.

This repository contains the Python source code for Potku's graphical user 
interface as well as the source code for external C programs that perform 
most of the number crunching. Source code for simulation programs is not 
included.

### Getting started with development

First step is to install Python 3.6 along with pip package installer. Make 
sure they are added to your PATH. Then install Pipenv:
 
````
pip install --user pipenv
````

Once these prerequisites are met, you can clone the repository and 
checkout the development branch to get the most up-to-date version of Potku.
 
````
git clone https://github.com/JYU-IBA/potku.git
cd potku
git checkout development
````

Install and activate the virtual environment with Pipenv:

````
pipenv install
pipenv shell
````

Once the virtual environment is up and running, Potku can be launched from the 
command line:
 
````
python run_potku.py
````

### Compiling the C code

Compilation requires ``make`` and ``gcc``. All programs can be compiled by 
running ``make`` in the ``/external`` directory. This installs the binaries and 
other files into their correct locations.

### Tests

Tests are located in the ``tests`` package. They are divided into unit tests 
(tests that cover one or two functions at a time) and integration tests 
(tests that cover multiple components).
  
Tests have been written using unittest framework. With the virtual environment 
activated, they can be run from the root directory of the project with:

````
python -m unittest discover
````

### Licence

Potku is licensed under GPL-2.0. See 'LICENCE' for details.