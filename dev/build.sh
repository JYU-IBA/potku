#!/bin/bash

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$CUR_DIR/.."
ROOT_DIR="$PWD"
EXT_DIR="$ROOT_DIR/external"

if [ -z "$1" ]; then
    echo "Using default toolchain file."
    toolchainargument=""
else
    echo "Using toolchain file at: \"$1\""
    toolchainargument="-DCMAKE_TOOLCHAIN_FILE=\"$1\""
fi

cd "external/submodules"

for submodule in jibal erd_depth mcerd coinc; do
    cd "${submodule}"
    rm build/CMakeCache.txt && echo Removed $submodule CMakeCache.txt
    mkdir -p build
    cd build
    cmake $toolchainargument -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$EXT_DIR" -DCMAKE_INSTALL_PREFIX="$EXT_DIR" -DCMAKE_INSTALL_RPATH="$EXT_DIR/lib" ../
    make && make install
    cd ../..
done

os_name=$(uname -s)
gsl_libdir="$(pkg-config --variable=libdir gsl)"
potku_libdir="$EXT_DIR/lib"
gsl_version="$(pkg-config --modversion gsl|sed 's/^\(.*\)\.\(.*\)\.\(.*\)/\1\2/')" #E.g. 27 for 2.7.1

mkdir -p "${potku_libdir}"

if [ "$os_name" = "Linux" ]; then
    gsl_files="${gsl_libdir}/libgsl.so.${gsl_version} ${gsl_libdir}/libgslcblas.so.0"
    chmod u+rw ${potku_libdir}/*.so
fi

if [ "$os_name" = "Darwin" ]; then
    gsl_files="${gsl_libdir}/libgsl.${gsl_version}.dylib ${gsl_libdir}/libgslcblas.0.dylib"
    chmod u+rw ${potku_libdir}/*.dylib
fi


cp $gsl_files "${potku_libdir}"
