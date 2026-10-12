# -*- mode: python ; coding: utf-8 -*-
import shutil
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

datas = [("organizer/webui", "webui"), ("config.json", ".")]
binaries = []
hiddenimports = []

for pkg in (
    "webview",
    "watchdog",
    "fitz",
    "docx",
    "pytesseract",
    "PIL",
    "faiss",
    "sentence_transformers",
    "transformers",
    "tokenizers",
    "huggingface_hub",
):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

hiddenimports += [
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
    "watchdog.observers.winapi",
    "watchdog.observers",
]

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FileSage",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FileSage",
)

# Ship an editable config.json next to FileSage.exe (a default is also
# bundled under _internal; this copy overrides it).
dist_root = Path("dist") / "FileSage"
try:
    shutil.copy2("config.json", dist_root / "config.json")
except OSError:
    pass
