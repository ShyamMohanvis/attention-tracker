# -*- mode: python ; coding: utf-8 -*-
# attention.spec — PyInstaller build specification for Attention Tracker
#
# Build:  pyinstaller attention.spec
# Output: dist/AttentionTracker/AttentionTracker.exe

from pathlib import Path
import mediapipe

SRC = Path("src")
mediapipe_dir = str(Path(mediapipe.__file__).parent)

a = Analysis(
    [str(SRC / "app.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[
        # Settings, icons, and assets bundled into the exe
        (str(SRC / "settings.json"),        "."),
        (str(SRC / "ui" / "icons"),         "ui/icons"),
        (str(SRC / "assets"),               "assets"),
        # MediaPipe model files
        (mediapipe_dir,                     "mediapipe"),
    ],
    hiddenimports=[
        # MediaPipe / OpenCV internals
        "mediapipe.python._framework_bindings",
        "cv2",
        # PySide6
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        # Windows APIs
        "winsdk.windows.media.control",
        "win32api",
        "win32gui",
        "win32con",
        "pyautogui",
        # Project modules
        "camera",
        "gaze",
        "monitor",
        "controller",
        "ui",
        "utils",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AttentionTracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(SRC / "ui" / "icons" / "tray_icon.png"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AttentionTracker",
)
