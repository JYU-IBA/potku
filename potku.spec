# -*- mode: python -*-

import platform
if platform.system() == "Darwin":
    import os
    # FIXME there are few issues when bundling an app on Mac
    #   - pyinstaller does not bundle tk/tcl, but the executable still requires
    #     them.
    #       - Solution: either make changes to hook-_tkinter.py file
    #       (https://github.com/pyinstaller/pyinstaller/issues/3753)
    #       or uncomment the contents in the extras list below.
    #  - when bundled with --windowed parameter and console=False,
    #    potku.app starts and exits briefly after. Possibly an issue
    #    with file paths (for example .ui files)
    #    https://github.com/pyinstaller/pyinstaller/issues/1804
    extras = [
        #("tcl", "tcl"),
        #("tk", "tk")
    ]
    for folder, _ in extras:
        os.makedirs(folder, exist_ok=True)
        open(os.path.join(folder, ".ignore"), "w").close()
else:
    extras = []

block_cipher = None

a = Analysis(
    ['potku.py'],
     pathex=[],
     binaries=[
        ('external/bin/[!jibal.conf]*', 'external/bin/')
     ],
     datas=[
        ("external/lib", "external/lib"),
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
