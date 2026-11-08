# Build from the repo root: pyinstaller packaging/pyinstaller/kartoffelfax.spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).parents[1]

a = Analysis(
    [str(root / "packaging" / "pyinstaller" / "entry.py")],
    pathex=[str(root / "backend")],
    datas=[
        (str(root / "frontend"), "frontend"),
        (str(root / "backend" / "kartoffelfax" / "db" / "schema.sql"), "kartoffelfax/db"),
    ],
    hiddenimports=collect_submodules("uvicorn") + collect_submodules("kartoffelfax"),
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="kartoffelfax",
    console=True,
)
