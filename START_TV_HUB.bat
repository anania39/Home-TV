@echo off
title TV Hub Server (Homelander)
cd /d "%~dp0"
echo ================================================================
echo   [TV HUB] - HIGH AVAILABILITY HOME SERVER
echo ================================================================
echo   * Local Wi-Fi Address:    http://192.168.50.250:8000
echo   * Permanent mDNS Name:    http://tvhub.local:8000
echo   * TV Browser Receiver:    http://192.168.50.250:8000/tv
echo ================================================================
echo   Starting TV Hub... Keep this window open or minimized.
echo ================================================================
python run.py
pause
