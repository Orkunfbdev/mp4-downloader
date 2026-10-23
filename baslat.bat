@echo off
chcp 65001 >nul
title MP4 Downloader - Otomatik Baslatici

:: Python kurulu mu kontrol et
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo ❌ HATA: Bilgisayarinizda Python kurulu bulunamadi!
    echo ========================================================
    echo.
    echo Lutfen asagidaki adimlari izleyin:
    echo 1. https://www.python.org/downloads/ adresine gidin.
    echo 2. Python'i indirin ve kurulumu baslatin.
    echo 3. Kurulum ekraninin EN ALTINDAKI:
    echo    "[X] Add python.exe to PATH"
    echo    kutusunu MUTLAKA isaretleyin!
    echo 4. Kurulum bitince bu dosyaya tekrar cift tiklayin.
    echo.
    echo ========================================================
    pause
    exit /b
)

echo [1/2] Gerekli kutuphaneler yukleniyor / kontrol ediliyor...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] Program baslatiliyor...
cls
python downloader.py
if %errorlevel% neq 0 (
    echo.
    pause
)
