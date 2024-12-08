# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['MIPS.py'],
             pathex=['/Users/gordonanderson/GAACE/Products/MIPS/MIPSapp/py/MIPS'],
             binaries=[('/Library/Frameworks/Python.framework/Versions/3.7/lib/libtcl8.6.dylib', 'tcl'), ('/Library/Frameworks/Python.framework/Versions/3.7/lib/libtk8.6.dylib', 'tk')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='MIPS',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='GAACElogo.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='MIPS')
app = BUNDLE(coll,
             name='MIPS.app',
             icon='GAACElogo.icns',
             bundle_identifier='MIPS')
