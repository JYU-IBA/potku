#!/bin/bash

CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
GREEN="\033[0;92m"
RED="\033[0;91m"
NC="\033[0m"
cd ../
ROOT_DIR = "$PWD"

if [[ "${PIPENV_ACTIVE}" -ne 1 ]]; then
  echo -e "${RED}create_bundle must be run within pipenv shell ('pipenv run <script>')${NC}"
  exit 1
fi

cd ${CUR_DIR}
echo
echo -e "${GREEN}Compiling external programs${NC}"
echo
./build.sh || exit 1

cd ${ROOT_DIR}
echo
echo -e "${GREEN}Installing and updating Python dependencies${NC}"
echo
pip install pipenv
pipenv install || exit 1

echo
echo -e "${GREEN}Python libraries used:${NC}"
echo
pip freeze
mkdir -p dist
pip freeze > dist/python_libs.txt

echo -e "${GREEN}List of libraries written to dist/python_libs.txt${NC}"

cd ${ROOT_DIR}
echo
echo -e "${GREEN}Running tests${NC}"
echo
python -m unittest discover || exit 1

cd ${ROOT_DIR}
echo
echo -e "${GREEN}Installing and running PyInstaller${NC}"
echo

pip install pyinstaller
pyinstaller -y --clean --windowed potku.spec || exit 1

cd dist
echo
echo -e "${GREEN}Creating a .zip archive${NC}"
echo

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS="mac"
elif [[ "$OSTYPE" == "cygwin" ]]; then
  OS="win"
elif [[ "$OSTYPE" == "msys" ]]; then
  OS="win"
elif [[ "$OSTYPE" == "win32" ]]; then
  OS="win"
else
  echo "${RED}Could not recognize operating system${NC}"
  exit 1
fi

ARCHIVE="potku_${OS}.zip"
# TODO add version number to bundle
rm ${ARCHIVE}
zip -r ${ARCHIVE} potku || echo -e "${RED}Failed to create an archive${NC}"

echo
echo -e "${GREEN}Bundle created${NC}"
cd ${CUR_DIR}
exit 0
