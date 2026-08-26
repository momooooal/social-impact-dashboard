@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "install.bat"
exit /b %errorlevel%
