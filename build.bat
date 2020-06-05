SET CUR_DIR=%cd%
SET EXT_DIR=%CUR_DIR%\external

@REM TODO take cmake options (-G and -DCMAKE_TOOLCHAIN_FILE) as command line
@REM parameters.

cd external

make clean
make

cd submodules\jibal\

del /q build\CMakeCache.txt
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=%EXT_DIR% ..
msbuild INSTALL.vcxproj /property:Configuration=Release

cd ..\..\mcerd
del /q build\CMakeCache.txt
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=%EXT_DIR% ..
msbuild INSTALL.vcxproj /property:Configuration=Release

cd %CUR_DIR%
