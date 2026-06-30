@echo off
cd /d "%~dp0"
title Global TB Burden Dashboard

REM --- skip Streamlit's first-run email prompt (the usual "stuck" cause) ---
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
> "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
>> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""

echo ================================================
echo    Global TB Burden Dashboard  -  launcher
echo ================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [X] Python is not installed or not on PATH.
  echo     Install from https://www.python.org/downloads/ and TICK "Add Python to PATH".
  echo.
  pause
  exit /b
)

echo [1/3] Installing required packages (first run only)...
python -m pip install -r requirements.txt
echo.
echo [2/3] Downloading the full WHO dataset (skips if no internet)...
python prepare_data.py
echo.
echo [3/3] Launching the dashboard...
echo     Your browser should open at http://localhost:8501
echo     If it does not, open a browser yourself and type:  http://localhost:8501
echo     Access code: tb2024
echo     Keep this black window OPEN while presenting. Close it to stop.
echo.
python -m streamlit run app.py --server.port 8501 --server.headless false
echo.
echo (If the dashboard closed or errored, the messages above explain why.)
pause
