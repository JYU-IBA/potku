#!/bin/bash

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
EXT_DIR=$CUR_DIR/external

cd external

make clean
make

cd submodules/jibal/

rm -r build || echo Creating new build directory
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX="$EXT_DIR" ../
make
make install

cd ../../mcerd
rm -r build || echo Creating new build directory
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
make
make install
