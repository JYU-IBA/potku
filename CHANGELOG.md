# Changelog

All notable changes to Potku will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Changelog (this file)
- Zooming in and out (with mouse wheel) of ToF-E histograms, moving with arrow keys


### Changed

- Supports Python 3.12 and latest library versions and PyInstaller
- Legacy C codes replaced with elatest versions, all using CMake as build system instead of Makefiles directly.
MSVC is now the preferred compiler on Windows.
- `erd_depth` and `coinc` executables are now obtained via submodules
- `erd_depth` supports parallel processing, libomp dependency added on macOS
- `tof_list` replaced by `tofe_list`, code in `erd_depth` repository and built with it
- Used efficiency files (`tofe_list`) communicated to Potku via standard output, not from a separate file.
- Removed `run_potku.py` script, `potku.py` can be run as a script
- Loading selections file dialog usability improvements
- Build script detects GSL library path more robustly
- Some Python functions are used from math and not scipy
- GitHub actions (packaging) and development scripts slightly improved
- Name sanitization code relaxed, e.g. samples and measurements can have spaces in names

### Fixed

- Average mass calculation code fixed. Masses are now obtained from JIBAL supplied files.
- Depth profiles were not shown if more than one scattered ("RBS") selection was used
- Unnecessary warning was shown if more than one scattered ("RBS)" selection was used
- Energy spectrum saving fixed, now we make one file per spectrum and donot attempt to save files with possibly different energy binning to one file
- Elemental losses forgot which reference cut was used

### Removed

- masses.dat and abundances.dat are removed from external manifest (replacements supplied by JIBAL)
- C code from this repository (all C codes in submodules)
- AWK dependency and packaging of the executable awk.exe on Windows removed
- Unimplemented reporting feature from main menu

## [2.2.5] - 2023-12-18

## [2.2.4] - 2023-11-29

## [2.2.3] - 2023-11-29

## [2.2.2] - 2023-11-23

## [2.2.1] - 2023-11-09

## [2.2.0] - 2023-11-01
