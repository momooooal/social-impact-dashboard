@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "open_helper.bat"
exit /b %errorlevel%
