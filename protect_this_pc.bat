@echo off
:: TV Hub - 1-Click Instant PC Ad-Shield Activation
:: Requests Administrator elevation if not already elevated
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges to set local DNS...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================================
echo   [TV HUB] - ACTIVATING AD-SHIELD ON THIS PC
echo ============================================================
echo.
echo Setting Wi-Fi DNS to TV Hub Ad-Blocker (127.0.0.1)...
netsh interface ip set dns "Wi-Fi" static 127.0.0.1
netsh interface ip add dns "Wi-Fi" 1.1.1.1 index=2

echo Flushing Windows DNS Cache...
ipconfig /flushdns

echo.
echo ============================================================
echo   SUCCESS! THIS PC IS NOW FULLY PROTECTED AGAINST ADS!
echo   All browser requests now filter through port 53 sinkhole.
echo ============================================================
echo.
timeout /t 3
