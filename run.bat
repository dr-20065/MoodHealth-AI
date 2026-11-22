@echo off
title HealthMood
echo ========================================================
echo               Starting HealthMood
echo ========================================================
echo.

where py >nul 2>nul
if %errorlevel% neq 0 (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found on your system.
        echo Please install Python from https://www.python.org/
        pause
        exit /b 1
    )
    set PY_CMD=python
) else (
    set PY_CMD=py
)

if not exist .venv (
    echo [INFO] Creating Python virtual environment (.venv)...
    %PY_CMD% -m venv .venv
)

call .venv\Scripts\activate.bat

echo [INFO] Ensuring required packages are installed...
pip install -r requirements.txt --quiet

echo.
echo ========================================================
echo   HealthMood is launching!
echo   URL:         http://127.0.0.1:5000
echo   Live Demo:   http://127.0.0.1:5000/demo
echo   Demo Login:  demo@healthmood.com / demo12345
echo ========================================================
echo.

start http://127.0.0.1:5000/demo

%PY_CMD% app.py
pause

