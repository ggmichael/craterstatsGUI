#  Copyright (c) 2026, Greg Michael
#  Licensed under BSD 3-Clause License. See LICENSE.txt for details.

import os
import shutil

datas = [
    ('src/craterstatsGUI/assets/*', 'craterstatsGUI/assets'),
    ('LICENSE.txt', '.'),
    ('scripts/add_cs_path.bat', '.'),
    ('scripts/create_desktop_cli_shortcut.bat', '.'),
]

hiddenimports = [
    'matplotlib.backends.backend_svg',
    'matplotlib.backends.backend_pdf',
    'scipy.special.erf',
    'scipy.special.factorial',
]

a = Analysis(
    ['src/entry.py'],
    pathex=[os.path.abspath('src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='craterstats',
    console=True,
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

exedir = r'dist/craterstatsGUI/'
shutil.move(exedir + r'_internal/LICENSE.txt', exedir)
if os.name == 'nt':
    shutil.move(exedir + r'_internal/create_desktop_cli_shortcut.bat', exedir)