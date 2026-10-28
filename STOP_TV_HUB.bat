@echo off
title Stop TV Hub
echo Stopping TV Hub and cloudflared processes...
taskkill /F /IM cloudflared.exe 2>nul
powershell -Command "$p = Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like '*run.py*' }; if ($p) { $p.Terminate() }"
echo TV Hub stopped.
pause
