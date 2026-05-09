# -*- mode: python ; coding: utf-8 -*-

import os
import shutil
import platform

a = Analysis(
    ['src/craterstatsGUI.py'],
    pathex=[os.path.abspath('src')],
    binaries=[],
    datas = [
        ('src/craterstatsGUI/assets/*','craterstatsGUI/assets'),
        #('scripts/create_desktop_shortcut.bat', '.'),
        ('LICENSE.txt', '.'),
    ],
    hiddenimports=[
                   'matplotlib.backends.backend_svg',
                   'matplotlib.backends.backend_pdf',
                   'scipy.special.erf','scipy.special.factorial',
                   ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='craterstatsGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='craterstatsGUI',
)

shutil.move(r'dist/craterstatsGUI/_internal/LICENSE.txt', r'dist/craterstatsGUI')

