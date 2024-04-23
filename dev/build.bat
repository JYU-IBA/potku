set CUR_DIR=%cd%
cd ..
set ROOT_DIR=%cd%
set EXT_DIR=%ROOT_DIR%\external
set BIN_DIR=%EXT_DIR%\bin

@REM TODO take cmake option -G as command line parameter.

if "%1"=="" (
	echo Using default toolchain file
) else (
	echo Using toolchain file at: %1
)

cd %EXT_DIR%
cd submodules

for %%G in (jibal erd_depth mcerd coinc) DO @(
cd %%G
mkdir build
cd build
echo "Building %%G"
cd
del /q CMakeCache.txt

if "%1"=="" (
	cmake -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%EXT_DIR% -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
) else (
	cmake -A x64 -DCMAKE_TOOLCHAIN_FILE=%1 -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%EXT_DIR% -DCMAKE_INSTALL_PREFIX=%EXT_DIR% .. || EXIT /b 1
)
msbuild INSTALL.vcxproj /property:Configuration=Release || EXIT /b 1
cd ..
)


setlocal enabledelayedexpansion

if "%1"=="" (
	set "VCPKG_SEARCH_PATH=%VCPKG_ROOT%"
) else (
	for %%A in ("%1") do set "TOOLCHAIN_DIR=%%~dpA"
	echo !TOOLCHAIN_DIR!
	cd /d !TOOLCHAIN_DIR!
	cd ..\..\
	set "VCPKG_SEARCH_PATH=!cd!"
)
cd /d %VCPKG_SEARCH_PATH%

for /f "tokens=*" %%A in ('dir /s /b "*gsl.dll" ^| findstr /i "x64"') do (
    set "GSL_PATH=%%A"
)

for /f "tokens=*" %%A in ('dir /s /b "*gslcblas.dll" ^| findstr /i "x64"') do (
    set "GSLCBLAS_PATH=%%A"
)
@echo on
echo !VCPKG_SEARCH_PATH!
echo !GSL_PATH!
echo !GSLCBLAS_PATH!

copy !GSL_PATH! %BIN_DIR%
copy !GSLCBLAS_PATH! %BIN_DIR%

cd /d %CUR_DIR%
