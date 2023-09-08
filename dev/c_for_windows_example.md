# Installing MSYS2 for C compilation

This is a guide for setting up an MSYS2 + MinGW64 environment on Windows. This enables compiling C programs that don't use CMake (see the main [README.md](README.md) for instructions on CMake programs).

There are several ways to set up a C environment on Windows. The approach in this guide is a relatively straightforward one.

## Installing MSYS2

Install [MSYS2](https://www.msys2.org/)

Open `MSYS2 MinGW 64-bit` (not `MSYS2 MSYS`).

Update MSYS2:
```sh
pacman -Syu
# restart MSYS if needed
pacman -Su
```

## Installing packages

Install gcc:
```sh
pacman -S mingw-w64-x86_64-gcc
```

Install other development packages (at least make is needed from this, maybe others too):
```sh
pacman -S base-devel
```

Install optional packages:
```sh
pacman -S vim nano tree git
```

## Updating PATH

Add these two bin folders to PATH (in Windows) and make sure that `mingw64` is before (higher than) `usr`. This assumes that MSYS is installed in the default location. Restart all terminals to reload changes.

- C:\msys64\mingw64\bin
- C:\msys64\usr\bin

Note that `C:\msys64\usr\bin` contains a lot of programs, some of which may conflict with currently installed programs. To minimize the risk of conflicts, place the folder last in the PATH.

## Verifying the installation

Running the command `make` in the folder `external` should now compile the programs in `Potku-coinc, Potku-erd_depth, Potku-gsto, Potku-tof_list` and copy them over to `bin`. This should work on all terminals (CMD, MSYS2 MinGW 64-bit, PowerShell etc.).
