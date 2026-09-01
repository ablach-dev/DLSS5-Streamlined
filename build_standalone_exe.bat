@echo off
title Build Standalone DLSS 5 Installer Executable
cd /d "%~dp0"

echo ===================================================
echo  Building Standalone Single-File DLSS5_Installer.exe
echo ===================================================
echo.

where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

echo Packaging everything into single standalone EXE...
pyinstaller --noconfirm --onefile --windowed --name "DLSS5_Installer" --add-data "Assets;Assets" --collect-all customtkinter dlss5_installer.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo  Build Completed Successfully!
echo  Output Location: dist\DLSS5_Installer.exe
echo ===================================================
echo.
pause
