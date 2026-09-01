@echo off
title DLSS 5 Installer
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not found in your PATH.
    echo Please install Python 3.10+ from python.org or download the standalone release EXE.
    pause
    exit /b 1
)

:: Install customtkinter if missing
python -c "import customtkinter" >nul 2>nul
if %errorlevel% neq 0 (
    echo Setting up dependencies...
    python -m pip install --quiet customtkinter
)

start "" pythonw dlss5_installer.py
exit /b 0
