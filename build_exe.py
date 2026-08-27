import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EXCLUDED_MODULES = [
    # GUI & Graphics
    "PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.sip",
    "tkinter", "turtle", "tcl",
    "pygame",
    "PIL", "pillow",
    "matplotlib",
    "cv2", "opencv_python", "opencv_contrib_python",
    "mediapipe",
    "fitz", "pymupdf",
    
    # Scientific & Numerical
    "numpy", "scipy", "pandas",
    
    # Automation & System Hooks
    "dxcam", "sounddevice", "pyautogui", "mouseinfo", "pygetwindow",
    "pymsgbox", "pyscreeze", "pytweening",
    
    # Unneeded Python Standard Tooling
    "unittest", "test", "doctest", "pydoc", "distutils", "email",
    "lib2to3", "sqlite3", "xmlrpc", "multiprocessing",
]

def build():
    print("=" * 60)
    print("🚀 MP4 Downloader - Ultra Hızlı EXE Derleyici")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--clean",
        "--name", "orkunfb",
        "--console",
        "--collect-all", "rich",
        "--collect-submodules", "yt_dlp",
        "--collect-submodules", "curl_cffi",
    ]
    
    for mod in EXCLUDED_MODULES:
        cmd.extend(["--exclude-module", mod])
        
    cmd.append(str(BASE_DIR / "downloader.py"))
    
    print("\n📦 PyInstaller derleme işlemi başlatılıyor...")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    
    if res.returncode != 0:
        print("\n❌ Derleme başarısız oldu!")
        sys.exit(res.returncode)
        
    dist_exe = BASE_DIR / "dist" / "orkunfb.exe"
    target_exe = BASE_DIR / "orkunfb.exe"
    
    if dist_exe.exists():
        if target_exe.exists():
            target_exe.unlink()
        shutil.move(str(dist_exe), str(target_exe))
        print(f"\n✓ Başarılı! Yeni exe oluşturuldu: {target_exe} ({target_exe.stat().st_size / (1024*1024):.2f} MB)")
        
    # Temizlik
    for p in [BASE_DIR / "build", BASE_DIR / "dist", BASE_DIR / "orkunfb.spec"]:
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)
            
    print("🧹 Geçici derleme dosyaları temizlendi.")
    print("=" * 60)

if __name__ == "__main__":
    build()
