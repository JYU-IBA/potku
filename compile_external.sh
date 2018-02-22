#!/bin/sh
ORIGIN=$(pwd)
cd "$ORIGIN"
cd external/Potku-gsto
make
cd "$ORIGIN"
cd external/Potku-tof_list
make clean
make
make install
cd "$ORIGIN"
cd external/Potku-erd_depth
make clean
make
make install
cd "$ORIGIN"
cd external/Potku-coinc
make clean
make
make install
cd "$ORIGIN"
