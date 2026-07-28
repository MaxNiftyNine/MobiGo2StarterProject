@echo off
setlocal
cd /d "%~dp0"
py -3 "%~dp0tools\mobigo_usb\storage.py" %*
if errorlevel 1 pause
