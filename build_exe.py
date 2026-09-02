import os
import sys
import shutil
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

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
    "unittest", "test", "doctest", "pydoc",
]

def build(onefile=True):
    mode_str = "Tek Dosya (OneFile)" if onefile else "Klasör Modu (Ultra Hızlı - 0.2s)"
    print("=" * 60)
    print(f"🚀 MP4 Downloader - EXE Derleyici [{mode_str}]")
    print("=" * 60)
    
    icon_path = BASE_DIR / "assets" / "icon.ico"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile" if onefile else "--onedir",
        "--clean",
        "--name", "orkunfb",
        "--console",
        "--collect-all", "rich",
        "--collect-all", "yt_dlp",
        "--collect-all", "curl_cffi",
    ]
    
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    for mod in EXCLUDED_MODULES:
        cmd.extend(["--exclude-module", mod])
        
    cmd.append(str(BASE_DIR / "downloader.py"))
    
    print("\n📦 PyInstaller derleme işlemi başlatılıyor...")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    
    if res.returncode != 0:
        print("\n❌ Derleme başarısız oldu!")
        sys.exit(res.returncode)
        
    dist_dir = BASE_DIR / "dist"
    
    if onefile:
        dist_exe = dist_dir / "orkunfb.exe"
        target_exe = BASE_DIR / "orkunfb.exe"
        if dist_exe.exists():
            if target_exe.exists():
                try:
                    target_exe.unlink()
                except Exception:
                    pass
            shutil.move(str(dist_exe), str(target_exe))
            print(f"\n✓ Başarılı! Tek dosya EXE oluşturuldu: {target_exe} ({target_exe.stat().st_size / (1024*1024):.2f} MB)")
    else:
        dist_folder = dist_dir / "orkunfb"
        target_folder = BASE_DIR / "orkunfb_app"
        if dist_folder.exists():
            if target_folder.exists():
                shutil.rmtree(target_folder, ignore_errors=True)
            shutil.move(str(dist_folder), str(target_folder))
            print(f"\n✓ Başarılı! Anında açılan (0.2s) uygulama klasörü oluşturuldu: {target_folder}\\orkunfb.exe")
            
    # Temizlik
    for p in [BASE_DIR / "build", BASE_DIR / "dist", BASE_DIR / "orkunfb.spec"]:
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)
            
    print("🧹 Geçici derleme dosyaları temizlendi.")
    print("=" * 60)

if __name__ == "__main__":
    is_dir = "--dir" in sys.argv or "--fast" in sys.argv
    build(onefile=not is_dir)
