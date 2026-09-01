@echo off
title Build DLSS 5 Windows Setup Installer
cd /d "%~dp0"

echo ===================================================
echo  Step 1: Building App Binary (DLSS5_Installer.exe)
echo ===================================================
pyinstaller --noconfirm --onefile --windowed --name "DLSS5_Installer" --collect-all customtkinter dlss5_installer.py

echo.
echo ===================================================
echo  Step 2: Building Setup Wizard (DLSS5_Setup.exe)
echo ===================================================
pyinstaller --noconfirm --onefile --windowed --name "DLSS5_Setup" --add-data "dist\DLSS5_Installer.exe;." --add-data "Assets;Assets" --collect-all customtkinter installer_setup.py

echo.
echo ===================================================
echo  Build Completed!
echo  Setup Executable: dist\DLSS5_Setup.exe
echo ===================================================
pause
