# This is an example for creating a Potku bundle on Mac.

########################################

# Setting up a development environment:

# Install xcode by typing `git` into terminal and following instructions
git --version

# Install homebrew
# https://brew.sh/
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# Install tools needed for compilation
brew install python
brew install cmake
brew install gsl

# Install pipenv for virtual environment management
pip install --user pipenv

# Editing PATH may be necessary for pipenv to work, I'm not completely sure.
# Substitute "3.7" with your installed Python 3+ version.
# Also substitute "potku" with your username.
PATH="/Library/Frameworks/Python.framework/Versions/3.7/bin:${PATH}"
export PATH
PATH="/Users/potku/Library/Python/3.7/bin:${PATH}"
export PATH

# Install pyenv for installing Python 3.6 (brew does not ship Python 3.6 anymore)
# https://github.com/pyenv/pyenv/
brew install pyenv
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.zshrc

# Restart shell:
exec "$SHELL"

# Install Python 3.6.10 with shared-library for use with PyInstaller
# https://stackoverflow.com/questions/58548730/how-to-use-pyinstaller-with-pipenv-pyenv
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.6.14
eval "$(pyenv init -)"

# Set Python version
pyenv global 3.6.14

# Clone Potku
git clone --recursive https://github.com/JYU-IBA/potku.git
cd potku

# Add data files required by JIBAL.
# The target directory doesn't exist before compiling JIBAL, so it needs to be created manually.
mkdir external/share/jibal
curl http://users.jyu.fi/~jaakjuli/jibal/data/data.tar.gz -o data.tar.gz && tar -xvf data.tar.gz -C external/share/jibal

# (Copy other required files, see [README.md](README.md))

# Create the Potku bundle
# If dependencies don't get installed, try running the command again.
pipenv run ./create_bundle.sh

########################################

# Bundling Tcl and Tk to distribution:

# Find PyInstaller location
pipenv shell
which pyinstaller

# edit: <virtualenv>/lib/python3.6/site-packages/PyInstaller/hooks/hoot-_tkinter.py
# if 'Library/Frameworks' in path_to_tcl:
# ->
# if 'Library/Frameworks' in path_to_tcl and 'Python' not in path_to_tcl:

########################################

# How to uninstall Python that was installed "the wrong way"
# https://stackoverflow.com/questions/3819449/how-to-uninstall-python-2-7-on-a-mac-os-x-10-6-4/3819829#3819829
# https://superuser.com/questions/276840/uninstalling-python-3-on-a-mac

########################################

