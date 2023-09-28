#!/bin/bash

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$CUR_DIR/.."
ROOT_DIR="$PWD"
EXT_DIR="$ROOT_DIR/external"

if [ -z "$1" ]; then
    echo "Using default toolchain file."
else
    echo "Using toolchain file at: $1"
fi

cd external

make clean
make

cd submodules/jibal/

rm build/CMakeCache.txt && echo Removed JIBAL cache file
mkdir -p build
cd build
if [ -z "$1" ]; then
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
else
    cmake -DCMAKE_TOOLCHAIN_FILE=$1 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
fi
make
make install

cd ../../mcerd
rm build/CMakeCache.txt && echo Removed MCERD cache file
mkdir -p build
cd build
if [ -z "$1" ]; then
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
else
    cmake -DCMAKE_TOOLCHAIN_FILE=$1 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
fi
make
make install

os_name=$(uname -s)
if [ "$os_name" = "Linux" ]; then
    dpkg_gsl=$(dpkg -S libgsl.so.27)
    path_to_gsl=$(echo "$dpkg_gsl" | awk -F: 'NR==1 {print $NF; exit}' | awk '{sub(/^[ \t]+/, "", $0); sub(/[ \t]+$/, "", $0); print}')
    dpkg_gslcblas=$(dpkg -S libgslcblas.so.0)
    path_to_gslcblas=$(echo "$dpkg_gslcblas" | awk -F: 'NR==1 {print $NF; exit}' | awk '{sub(/^[ \t]+/, "", $0); sub(/[ \t]+$/, "", $0); print}')
fi

if [ "$os_name" = "Darwin" ]; then
    find_gsl=$(sudo find /usr/local -name "libgsl.27.dylib")
    path_to_gsl=$(echo "$find_gsl" | awk -F: 'NR==1 {print $NF; exit}' | awk '{sub(/^[ \t]+/, "", $0); sub(/[ \t]+$/, "", $0); print}')
    find_gslcblas=$(sudo find /usr/local -name "libgslcblas.0.dylib")
    path_to_gslcblas=$(echo "$find_gslcblas" | awk -F: 'NR==1 {print $NF; exit}' | awk '{sub(/^[ \t]+/, "", $0); sub(/[ \t]+$/, "", $0); print}')
fi

cp "$path_to_gsl" "$EXT_DIR/lib"
cp "$path_to_gslcblas" "$EXT_DIR/lib"

