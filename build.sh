#!/bin/bash

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
JIBAL_DIR=$CUR_DIR/external/submodules/jibal/build/jibal
BIN_DIR=$CUR_DIR/external/Potku-bin
DATA_DIR=$CUR_DIR/external/Potku-data

cd external

make clean
make

mkdir submodules/include/
mkdir submodules/include/jibal

cd submodules/jibal/
cp data/abundances.dat "$DATA_DIR"
cp data/masses.dat "$DATA_DIR"/masses2.dat

rm -r build/* || mkdir build
cd build
cmake ../
make
cp jibal/libJibal.* "$BIN_DIR"

cd ../../mcerd
rm -r build/* || mkdir build
cd build
cmake -DCMAKE_PREFIX_PATH="$JIBAL_DIR" ../
make

cp mcerd "$BIN_DIR"
cp get_espe/get_espe "$BIN_DIR"