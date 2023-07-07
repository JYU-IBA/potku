#!/bin/bash

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ../
ROOT_DIR = "$PWD"
EXT_DIR="$ROOT_DIR/external"

if [ -z "$1" ]; then
    echo "Using default toolchain file."
else
    echo "Using toolchain file at: $1"
fi

cd external

sudo make clean
sudo make

cd submodules/jibal/

rm build/CMakeCache.txt && echo Removed JIBAL cache file
mkdir -p build
cd build
if [ -z "$1" ]; then
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
else
    cmake -DCMAKE_TOOLCHAIN_FILE=$1 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
fi
sudo make
sudo make install

cd ../../mcerd
rm build/CMakeCache.txt && echo Removed MCERD cache file
mkdir -p build
cd build
if [ -z "$1" ]; then
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
else
    cmake -DCMAKE_TOOLCHAIN_FILE=$1 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
fi
sudo make
sudo make install
