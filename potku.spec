# -*- mode: python -*-

import platform

system = platform.system()

if system == "Darwin":
    ADD_TK_AND_TCL = False
    extras = [("external/lib/*.dylib", ".")]

    if ADD_TK_AND_TCL:
        # PyInstaller has issues with building Mac apps. By default it does not
        # bundle tk and tcl with the app even though those are required.
        # There are two workarounds:
        #     1. it should be enough to just add empty 'tk' and 'tcl' folders
        #        to the bundle. Just set ADD_TK_AND_TCL to true to achieve this.
        #     2. edit the hook-_tkinter.py module of the PyInstaller
        #        installation that is used for bundling. For more info, see
        #        https://github.com/pyinstaller/pyinstaller/issues/3753

        import os
        extras2 = [
            ("tcl", "tcl"),
            ("tk", "tk")
        ]
        for folder, _ in extras2:
            os.makedirs(folder, exist_ok=True)
            open(os.path.join(folder, ".ignore"), "w").close()

        extras += extras2

block_cipher = None

a = Analysis(
    ["potku.py"],
     pathex=[],
     binaries=[
        ("external/bin/[!jibal.conf]*", "external/bin/")
     ],
     datas=[
        ("external/bin/jibal.conf", "external/bin/"),
        ("external/share", "external/share"),
        ("ui_files", "ui_files"),
        ("ui_icons", "ui_icons"),
        ("images", "images"),
        *extras
     ],
     hiddenimports=[
        "scipy._lib.messagestream",
        "pkg_resources.py2_warn"
     ],
     hookspath=[],
     runtime_hooks=[],
     excludes=[
        "tkagg"
     ],
     win_no_prefer_redirects=False,
     win_private_assemblies=False,
     cipher=block_cipher
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="potku",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon="ui_icons/potku/potku_logo_icons/potku_icon.ico"
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="potku"
)

if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name="potku.app",
        icon="ui_icons/potku/potku_logo_icons/potku_logo_icon.icns",
        bundle_identifier=None,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False
        },
    )
