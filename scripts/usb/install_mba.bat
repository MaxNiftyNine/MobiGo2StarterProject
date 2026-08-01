@echo off
setlocal
cd /d "%~dp0\..\.."
py -3 "tools\usb\install_mba.py" %*
if errorlevel 1 pause
