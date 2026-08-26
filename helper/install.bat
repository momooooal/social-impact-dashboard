@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ==========================================
echo   社群資料小助手 - 首次安裝
echo ==========================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo [需要 Python]
  echo 這台電腦尚未找到 Python Launcher。
  echo 請先安裝 Python 3.11 以上，安裝時勾選 Add Python to PATH。
  echo 官方下載：https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
if not exist .venv (
  echo [1/4] 建立獨立環境...
  py -3 -m venv .venv
  if errorlevel 1 goto :fail
)
echo [2/4] 安裝套件...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :fail
echo [3/4] 安裝小助手專用 Chromium...
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 goto :fail
echo [4/4] 完成。
echo.
echo 之後直接雙擊「開啟小助手.bat」即可。
pause
exit /b 0
:fail
echo.
echo 安裝失敗。請把這個視窗截圖給 ChatGPT。
pause
exit /b 1
