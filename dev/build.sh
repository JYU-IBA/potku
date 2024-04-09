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
gsl_libdir="$(pkg-config --variable=libdir gsl)"
potku_libdir="$EXT_DIR/lib"
gsl_version="$(pkg-config --modversion gsl|sed 's/^\(.*\)\.\(.*\)\.\(.*\)/\1\2/')" #E.g. 27 for 2.7.1
if [ "$os_name" = "Linux" ]; then
    cp "${gsl_libdir}/libgsl.so.${gsl_version}" "${gsl_libdir}/libgslcblas.so.0" "${potku_libdir}"
fi

if [ "$os_name" = "Darwin" ]; then
    cp "${gsl_libdir}/libgsl.${gsl_version}.dylib" "${gsl_libdir}/libgslcblas.0.dylib" "${potku_libdir}"
fi
