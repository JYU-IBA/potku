# -*- mode: python -*-

block_cipher = None


a = Analysis(['potku.py'],
             pathex=[
			 'C:\\Users\\localadmin\\.virtualenvs\\potku-s0gTnhB1\\Lib\\site-packages\\scipy\\extra-dll'],
             binaries=[('external\\bin\\*', 'external\\bin')],
             datas=[('external\\Potku-data\\*', 'external\\Potku-data'),
                    ('external\\share\\jibal\\*', 'external\\share\\jibal'),
                    ('ui_files\\*', 'ui_files'),
                    ('ui_icons\\reinhardt\\*', 'ui_icons\\reinhardt'),
                    ('ui_icons\\potku\\*', 'ui_icons\\potku'),
                    ('images\\*', 'images')
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
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='potku')