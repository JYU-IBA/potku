@echo off
set CUR_DIR=%cd%
set EXT_DIR=%CUR_DIR%\external

@REM TODO take cmake options (-G and -DCMAKE_TOOLCHAIN_FILE) as command line
@REM parameters.

cd external

make clean
make

cd submodules\jibal\

del /q build\CMakeCache.txt
mkdir build
cd build
cmake -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
msbuild INSTALL.vcxproj /property:Configuration=Release || EXIT /b 1

cd ..\..\mcerd
del /q build\CMakeCache.txt
mkdir build
cd build
cmake -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%EXT_DIR% -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
msbuild INSTALL.vcxproj /property:Configuration=Release || EXIT /b 1

cd %CUR_DIR%
