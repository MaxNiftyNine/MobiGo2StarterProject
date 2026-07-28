@echo off
setlocal
cd /d "%~dp0"
py -3 "%~dp0tools\mobigo_usb\install_mba.py" %*
if errorlevel 1 pause
