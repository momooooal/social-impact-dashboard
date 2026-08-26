@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe exit /b 2
.venv\Scripts\python.exe collector_cli.py --collect >> "%LOCALAPPDATA%\SocialImpactCollector\scheduled.log" 2>&1
