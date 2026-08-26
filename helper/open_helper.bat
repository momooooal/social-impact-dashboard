@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Social Impact Helper

if not exist "app.py" goto :missing_app
if not exist ".venv\Scripts\pythonw.exe" goto :not_installed

start "" ".venv\Scripts\pythonw.exe" "%~dp0app.py"
exit /b 0

:not_installed
echo Social Impact Helper is not installed yet.
echo Please double-click install.bat first.
pause
exit /b 2

:missing_app
echo app.py was not found in this folder.
echo Please replace the whole helper folder with the v3.2 package.
pause
exit /b 3
