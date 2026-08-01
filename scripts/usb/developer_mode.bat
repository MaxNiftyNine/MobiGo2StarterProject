@echo off
setlocal
cd /d "%~dp0\..\.."
py -3 "tools\usb\developer_mode.py" %*
if errorlevel 1 pause
