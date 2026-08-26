@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Social Impact Helper - Windows Setup

echo ==========================================
echo   Social Impact Helper - Windows Setup
echo ==========================================
echo.

if not exist "requirements.txt" goto :missing_files
if not exist "app.py" goto :missing_files
if not exist "collector_core.py" goto :missing_files
if not exist "collector_cli.py" goto :missing_files

set "PYEXE="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PYEXE=py -3"

if not defined PYEXE (
  python --version >nul 2>&1
  if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE goto :no_python

echo [1/5] Python found.
if not exist ".venv\Scripts\python.exe" (
  echo [2/5] Creating virtual environment...
  %PYEXE% -m venv ".venv"
  if errorlevel 1 goto :fail
) else (
  echo [2/5] Virtual environment already exists.
)

echo [3/5] Installing Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :fail

echo [4/5] Installing helper browser...
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto :fail

echo [5/5] Verifying installation...
".venv\Scripts\python.exe" -c "import tkinter, openpyxl, playwright; import collector_core; print('Verification OK')"
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo   Setup completed successfully.
echo ==========================================
echo You can now double-click open_helper.bat
echo.
pause
exit /b 0

:missing_files
echo.
echo ==========================================
echo   Setup files are incomplete.
echo ==========================================
echo This helper folder must contain:
echo   requirements.txt
echo   app.py
echo   collector_core.py
echo   collector_cli.py
echo.
echo Please replace the whole helper folder with the v3.2 package.
echo.
pause
exit /b 4

:no_python
echo.
echo Python 3 was not found on this computer.
echo Install Python 3.11 or newer, then run this file again.
echo During Python setup, enable: Add python.exe to PATH
echo https://www.python.org/downloads/windows/
echo.
pause
exit /b 2

:fail
echo.
echo ==========================================
echo   Setup failed.
echo ==========================================
echo Please take a screenshot of this window and send it to ChatGPT.
echo.
pause
exit /b 1
