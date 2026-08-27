@echo off
chcp 65001 >nul
echo.
echo ==========================================================
echo    🎬 MP4 Downloader - Otomatik Kurulum
echo ==========================================================
echo.
echo [*] Bagimliliklar yukleniyor ve 'orkunfb' komutu kaydediliyor...
python -m pip install -e .
echo.
echo ==========================================================
echo    [✓] Kurulum Basariyla Tamamlandi!
echo    Artik terminali acip 'orkunfb indir' yazabilirsiniz!
echo ==========================================================
echo.
pause
