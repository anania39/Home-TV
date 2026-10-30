@echo off
title TV Hub Server
cd /d "%~dp0"
echo ================================================================
echo   [TV HUB] - HIGH AVAILABILITY NETWORK SERVER
echo ================================================================
echo   * Permanent mDNS Name:    http://tvhub.local:8000
echo   * Local Network Hub:      http://localhost:8000
echo   * TV Browser Receiver:    http://tvhub.local:8000/tv
echo ================================================================
echo   Starting TV Hub... Keep this window open or minimized.
echo ================================================================
python run.py
pause
