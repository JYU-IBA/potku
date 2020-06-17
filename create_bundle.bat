@echo off
set cur_dir=%cd%

echo(
echo [92mCompiling external programs[0m
echo(
call build.bat || (echo [91mCompiling failed[0m && goto :error)

cd %cur_dir%
echo(
echo [92mInstalling and updating Python dependencies[0m
echo(
pip install pipenv
pipenv install || (echo [91mInstalling dependencies failed[0m && goto :error)

cd %cur_dir%
echo(
echo [92mRunning tests[0m
echo(
python -m unittest discover || (echo [91mTests failed[0m && goto :error)

cd %cur_dir%
echo(
echo [92mInstalling and running PyInstaller[0m
echo(
pip install pyinstaller
pyinstaller -y --clean potku.spec || (echo [91mPyInstaller failed[0m && goto :error)

cd dist
echo(
echo [92mCreating a .zip archive[0m
echo(
rem Assuming here that 7-zip is installed at this location. If not, you have
rem to create the zip file manually.
set zip="C:\Program Files\7-Zip\7z.exe"
set archive=potku_win.zip
rem TODO add version number to bundle
del /q %archive%
%zip% a -r %archive% potku || (echo [91mFailed to create an archive[0m)

echo(
echo [92mBundle created[0m
cd %cur_dir%
exit /b 0

:error
echo [91mFailed to bundle a binary package. Error code: %errorlevel%[0m
cd %cur_dir%
exit /b %errorlevel%