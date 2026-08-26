@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Social Impact Helper

if not exist ".venv\Scripts\pythonw.exe" goto :not_installed
if not exist "app.py" goto :missing_app

start "" ".venv\Scripts\pythonw.exe" "app.py"
exit /b 0

:not_installed
echo Social Impact Helper is not installed yet.
echo Please double-click install.bat first.
pause
exit /b 2

:missing_app
echo app.py was not found in this folder.
echo Please re-extract the full ZIP package.
pause
exit /b 3
