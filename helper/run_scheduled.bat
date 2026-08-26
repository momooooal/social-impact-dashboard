@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist "%LOCALAPPDATA%\SocialImpactCollector" mkdir "%LOCALAPPDATA%\SocialImpactCollector" >nul 2>&1
if not exist ".venv\Scripts\python.exe" exit /b 2
".venv\Scripts\python.exe" "collector_cli.py" --collect >> "%LOCALAPPDATA%\SocialImpactCollector\scheduled.log" 2>&1
exit /b %errorlevel%
