#!/bin/sh
rm external/Potku-bin/* external/Potku-include/*.h external/Potku-lib/*.a
rm -rf __pycache__ Dialogs/__pycache__ Modules/__pycache__ Widgets/__pycache__
cd external/Potku-gsto
make clean
cd ../..
cd external/Potku-erd_depth
make clean
cd ../..
cd external/Potku-tof_list
make clean
cd ../..
cd external/Potku-coinc
make clean
cd ../..
