SET CUR_DIR=%cd%
SET JIBAL_DIR=%CUR_DIR%\external\submodules\jibal\build\jibal
SET BIN_DIR=%CUR_DIR%\external\Potku-bin
SET DATA_DIR=%CUR_DIR%\external\Potku-data

cd external

make clean
make

mkdir submodules\include
mkdir submodules\include\jibal

cd submodules\jibal\
cp data\abundances.dat %DATA_DIR%
cp data\masses.dat %DATA_DIR%\masses2.dat

rm -r build || echo Creating new build directory
mkdir build
cd build
cmake ..
msbuild ALL_BUILD.vcxproj /property:Configuration=Release
cp jibal\Release\Jibal.dll %BIN_DIR%

cd ..\..\mcerd
rm -r build || echo Creating new build directory
mkdir build
cd build
cmake -DCMAKE_PREFIX_PATH=%JIBAL_DIR% ..
msbuild ALL_BUILD.vcxproj /property:Configuration=Release

cp Release\mcerd.exe %BIN_DIR%
cp get_espe\Release\get_espe.exe %BIN_DIR%

cd %CUR_DIR%