#!/bin/bash

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
EXT_DIR=$CUR_DIR/external

cd external

make clean
make

cd submodules/jibal/

rm build/CMakeCache.txt && echo Removed Jibal cache file
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$EXT_DIR" ../
make
make install

cd ../../mcerd
rm build/CMakeCache.txt && echo Removed MCERD cache file
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
make
make install
