@echo off
rem Start Novi on this computer (http://127.0.0.1:8765). Needs Python 3.11+ from python.org.
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or newer from https://www.python.org/downloads/ and tick "Add to PATH", then run this again.
  pause
  exit /b 1
)
py -3 -X utf8 app\run.py %*
if errorlevel 1 pause
