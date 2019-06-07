# -*- mode: python -*-

block_cipher = None


a = Analysis(['potku.py'],
             pathex=['C:\\Users\\drums\\potku\\potku', 
			 'C:\\Users\\drums\\.virtualenvs\\potku-qnFr4du5\\Lib\\site-packages\\scipy\\extra-dll', 
             'C:\\Users\\drums\\.virtualenvs\\potku-qnFr4du5\\Lib\\site-packages'],
             binaries=[('external\\Potku-bin\\*', 'external\\Potku-bin')],
             datas=[('external\\Potku-data\\*', 'external\\Potku-data'),
                    ('ui_files\\*', 'ui_files'),
                    ('ui_icons\\reinhardt\\*', 'ui_icons\\reinhardt'),
                    ('ui_icons\\potku\\*', 'ui_icons\\potku'),
                    ('images\\*', 'images')
					],
             hiddenimports=['scipy', 'scipy._lib.messagestream', 'PyQt5'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='potku')
