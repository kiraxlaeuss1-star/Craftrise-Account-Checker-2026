@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title CraftRise Checker - t.me/xlaeussx

cls
echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║                                                            ║
echo  ║              CRAFTRISE ACCOUNT CHECKER                     ║
echo  ║                    t.me/xlaeussx                          ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.

:: Gerekli dosyaları kontrol et
if not exist "checker.py" (
    echo  [X] checker.py bulunamadi!
    pause
    exit /b 1
)

if not exist "warp_token.py" (
    echo  [X] warp_token.py bulunamadi!
    pause
    exit /b 1
)

if not exist "account-checker-1.0.0-jar-with-dependencies.jar" (
    echo  [X] Java checker JAR dosyasi bulunamadi!
    pause
    exit /b 1
)

if not exist "hesaplar.txt" (
    echo  [!] hesaplar.txt bulunamadi, olusturuluyor...
    echo username:password > hesaplar.txt
    echo  [√] hesaplar.txt olusturuldu
    echo  [!] Lutfen hesaplar.txt dosyasina hesaplari ekleyin
    pause
    exit /b 0
)

:: Python kontrolü
echo  [*] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] Python bulunamadi!
    echo  [!] Lutfen Python 3.13+ yukleyin: https://www.python.org/
    pause
    exit /b 1
)
echo  [√] Python bulundu
echo.

:: Gerekli kutuphane kurulumu
echo  [*] Gerekli kutuphaneler kuruluyor...
pip install requests beautifulsoup4 rich flask DrissionPage -q
echo  [√] Kutuphaneler hazir
echo.

:: Java kontrolü
echo  [*] Java kontrol ediliyor...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] Java bulunamadi!
    echo  [!] Lutfen Java 17+ yukleyin: https://adoptium.net/
    pause
    exit /b 1
)
echo  [√] Java bulundu
echo.
if not exist "hits" mkdir hits

:: WARP Token API'yi başlat
echo  [*] WARP Token API baslatiliyor...
start "WARP Token API" python warp_token.py
timeout /t 8 /nobreak >nul
echo  [√] WARP Token API baslatildi
echo.

:: Python Checker API'yi başlat
echo  [*] Python Checker API baslatiliyor...
start "t.me/xlaeussx v3.0" python checker.py
echo  [!] Python API hazirlanirken bekleyin...

:: Python API'nin hazır olmasını bekle (akıllı bekleme)
set /a counter=0
set /a max_wait=30

:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:8080/stats >nul 2>&1
if %errorlevel% equ 0 (
    echo  [√] Python API hazir!
    goto api_ready
)

set /a counter+=2
if %counter% geq %max_wait% (
    echo  [X] Python API baslatilmadi! ^(%max_wait% saniye^)
    echo  [!] Lutfen checker.py penceresini kontrol edin
    pause
    exit /b 1
)

echo  [*] Bekleniyor... ^(%counter%/%max_wait% saniye^)
goto wait_loop

:api_ready
echo.

:: Java Checker'ı başlat
echo  [*] Java Checker baslatiliyor...
echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║                                                            ║
echo  ║                  CHECKER BASLATILDI!                       ║
echo  ║                                                            ║
echo  ║  Tum pencereler acildi, kontrol basliyor...               ║
echo  ║  Sonuclar hits/ klasorune kaydedilecek                    ║
echo  ║                                                            ║
echo  ║  Durdurmak icin tum pencereleri kapatin                   ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.

java -jar account-checker-1.0.0-jar-with-dependencies.jar

echo.
echo  [!] Java Checker kapandi
pause
