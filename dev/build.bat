@echo off
set CUR_DIR=%cd%
cd ..\
set ROOT_DIR=%cd%
set EXT_DIR=%ROOT_DIR%\external

@REM TODO take cmake option -G as command line parameter.

if "%1"=="" (
	echo Using default toolchain file
) else (
	echo Using toolchain file at: %1
)

cd external

make clean
make

cd submodules\jibal\
del /q build\CMakeCache.txt
mkdir build
cd build

if "%1"=="" (
	cmake -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
) else (
	cmake -A x64 -DCMAKE_TOOLCHAIN_FILE=%1 -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
)
msbuild INSTALL.vcxproj /property:Configuration=Release || EXIT /b 1

cd ..\..\mcerd
del /q build\CMakeCache.txt
mkdir build
cd build

if "%1"=="" (
	cmake -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%EXT_DIR% -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
) else (
	cmake -A x64 -DCMAKE_TOOLCHAIN_FILE=%1 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%EXT_DIR% -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
)
msbuild INSTALL.vcxproj /property:Configuration=Release || EXIT /b 1

cd %CUR_DIR%
