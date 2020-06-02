SET CUR_DIR=%cd%
SET EXT_DIR=%CUR_DIR%\external

@REM TODO take cmake options (-G and -DCMAKE_TOOLCHAIN_FILE) as command line
@REM parameters.

cd external

make clean
make

cd submodules\jibal\

rmdir /s /q build
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=%EXT_DIR% ..
msbuild INSTALL.vcxproj /property:Configuration=Release

cd ..\..\mcerd
rmdir /s /q build
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=%EXT_DIR% ..
msbuild INSTALL.vcxproj /property:Configuration=Release

cd %CUR_DIR%
