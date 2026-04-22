# build.spec
from PyInstaller.building.build_main import Analysis, PYZ, EXE

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['plyer.platforms.win.notification', 'sv_ttk'],
    hookspath=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='WaterTracker',
    debug=False,
    console=False,      # No console window
    icon=None,          # Add icon path if available
    onefile=True,       # Single .exe
)
