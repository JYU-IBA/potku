# -*- mode: python -*-

block_cipher = None


a = Analysis(['potku.py'],
             pathex=[],
             binaries=[('external/bin/', 'external/bin')],
             datas=[('external/lib', 'external/lib'),
                    ('external/share', 'external/share'),
                    ('ui_files', 'ui_files'),
                    ('ui_icons', 'ui_icons'),
                    ('images', 'images')
					],
             hiddenimports=['scipy._lib.messagestream', 'pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['tkagg'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='potku',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon='ui_icons/potku/potku_logo_icons/potku_icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='potku')