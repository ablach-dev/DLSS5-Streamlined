"""
DLSS 5 Streamlined Setup Wizard
===============================
Standard Windows Setup installer that unpacks the application, creates Desktop shortcuts,
and registers in Windows Add/Remove Programs.
"""

import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path

# Installation target directory
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "Programs" / "DLSS5_Installer"

def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def create_shortcut(target_exe: Path, shortcut_path: Path, description: str = "DLSS 5 Installer"):
    """Creates a Windows .lnk shortcut using PowerShell WScript.Shell."""
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{str(shortcut_path)}')
    $Shortcut.TargetPath = '{str(target_exe)}'
    $Shortcut.WorkingDirectory = '{str(target_exe.parent)}'
    $Shortcut.Description = '{description}'
    $Shortcut.IconLocation = '{str(target_exe)},0'
    $Shortcut.Save()
    """
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)

def register_uninstaller(install_dir: Path, exe_path: Path):
    """Registers the application in Windows Add/Remove Programs (Apps & Features)."""
    uninst_bat = install_dir / "uninstall.bat"
    uninst_content = f"""@echo off
title Uninstall DLSS 5 Installer
echo Removing DLSS 5 Installer...
set /p confirm=Are you sure you want to uninstall DLSS 5 Installer? (Y/N): 
if /i "%confirm%" neq "Y" exit /b 0

:: Remove shortcuts
del "%USERPROFILE%\\Desktop\\DLSS 5 Installer.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\DLSS 5 Installer.lnk" 2>nul

:: Remove registry entry
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DLSS5_Installer" /f 2>nul

:: Remove install directory on exit
start /b "" cmd /c timeout /t 1 /nobreak ^>nul ^& rmdir /s /q "{str(install_dir)}"
echo Successfully uninstalled DLSS 5 Installer.
pause
exit /b 0
"""
    try:
        uninst_bat.write_text(uninst_content, encoding="utf-8")
    except Exception:
        pass

    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DLSS5_Installer"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "DLSS 5 Installer")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "0.1.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "ablach-dev")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe_path))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c "{str(uninst_bat)}"')
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        print(f"Registry registration notice: {e}")

def run_setup_gui():
    try:
        import customtkinter as ctk
    except Exception:
        run_fallback_setup_gui()
        return

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    class SetupWizard(ctk.CTk):
        def __init__(self):
            super().__init__()

            self.title("DLSS 5 Installer Setup")
            self.geometry("520x460")
            self.resizable(False, False)
            self.configure(fg_color="#0F1117")

            self._center(520, 460)
            self._build_ui()

        def _center(self, w, h):
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{w}x{h}+{int((sw-w)/2)}+{int((sh-h)/2)}")

        def _build_ui(self):
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=24, pady=(24, 16))

            title = ctk.CTkLabel(header, text="DLSS 5 Installer Setup", font=ctk.CTkFont(size=20, weight="bold"), text_color="#F1F5F9")
            title.pack(anchor="w")

            subtitle = ctk.CTkLabel(header, text="Setup will install DLSS 5 Installer onto your computer.", font=ctk.CTkFont(size=12), text_color="#94A3B8")
            subtitle.pack(anchor="w", pady=(2, 0))

            card = ctk.CTkFrame(self, fg_color="#181B22", corner_radius=10, border_width=1, border_color="#282D37")
            card.pack(fill="x", padx=24, pady=(0, 16))

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=16)

            dir_label = ctk.CTkLabel(inner, text="Installation Folder:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#F1F5F9")
            dir_label.pack(anchor="w", pady=(0, 4))

            dir_val = ctk.CTkLabel(inner, text=str(INSTALL_DIR), font=ctk.CTkFont(family="Consolas", size=11), text_color="#94A3B8")
            dir_val.pack(anchor="w", pady=(0, 14))

            self.chk_desktop = ctk.CTkCheckBox(inner, text="Create a Desktop shortcut", font=ctk.CTkFont(size=12), fg_color="#2563EB")
            self.chk_desktop.select()
            self.chk_desktop.pack(anchor="w", pady=(0, 8))

            self.chk_start = ctk.CTkCheckBox(inner, text="Create a Start Menu shortcut", font=ctk.CTkFont(size=12), fg_color="#2563EB")
            self.chk_start.select()
            self.chk_start.pack(anchor="w", pady=(0, 8))

            self.chk_launch = ctk.CTkCheckBox(inner, text="Launch DLSS 5 Installer after setup", font=ctk.CTkFont(size=12), fg_color="#2563EB")
            self.chk_launch.select()
            self.chk_launch.pack(anchor="w")

            self.status_label = ctk.CTkLabel(self, text="Click Install to begin setup.", font=ctk.CTkFont(size=11), text_color="#94A3B8")
            self.status_label.pack(anchor="w", padx=24, pady=(0, 8))

            self.progress = ctk.CTkProgressBar(self, height=4, progress_color="#2563EB", fg_color="#1E232E")
            self.progress.set(0)
            self.progress.pack(fill="x", padx=24, pady=(0, 16))

            btn_row = ctk.CTkFrame(self, fg_color="transparent")
            btn_row.pack(fill="x", padx=24, pady=(0, 20))

            self.btn_install = ctk.CTkButton(btn_row, text="Install", height=40, font=ctk.CTkFont(size=13, weight="bold"), fg_color="#2563EB", hover_color="#1D4ED8", command=self._install)
            self.btn_install.pack(side="right", fill="x", expand=True, padx=(8, 0))

            self.btn_cancel = ctk.CTkButton(btn_row, text="Cancel", height=40, width=90, fg_color="#2E3440", hover_color="#3B4252", text_color="#94A3B8", command=self.destroy)
            self.btn_cancel.pack(side="left")

        def _install(self):
            self.btn_install.configure(state="disabled")
            self.btn_cancel.configure(state="disabled")
            self.status_label.configure(text="Installing application and assets...")
            self.progress.set(0.3)

            import threading
            def work():
                try:
                    bundle_dir = get_bundle_dir()
                    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

                    # Copy executable
                    src_exe = bundle_dir / "DLSS5_Installer.exe"
                    dst_exe = INSTALL_DIR / "DLSS5_Installer.exe"
                    if src_exe.exists():
                        shutil.copy2(src_exe, dst_exe)
                    else:
                        # If script is standalone
                        dst_exe = INSTALL_DIR / "DLSS5_Installer.exe"

                    # Copy assets
                    src_assets = bundle_dir / "Assets"
                    dst_assets = INSTALL_DIR / "Assets"
                    if src_assets.exists():
                        if dst_assets.exists():
                            shutil.rmtree(dst_assets)
                        shutil.copytree(src_assets, dst_assets)

                    self.after(0, lambda: self.progress.set(0.7))

                    # Shortcuts
                    desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
                    if self.chk_desktop.get() and desktop_dir.exists():
                        create_shortcut(dst_exe, desktop_dir / "DLSS 5 Installer.lnk")

                    start_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                    if self.chk_start.get() and start_dir.exists():
                        create_shortcut(dst_exe, start_dir / "DLSS 5 Installer.lnk")

                    # Uninstaller in Add/Remove programs
                    register_uninstaller(INSTALL_DIR, dst_exe)

                    self.after(0, lambda: self.progress.set(1.0))
                    self.after(0, lambda: self.status_label.configure(text="Installation successful!"))

                    if self.chk_launch.get() and dst_exe.exists():
                        subprocess.Popen([str(dst_exe)], cwd=str(INSTALL_DIR))

                    time.sleep(0.5)
                    self.after(0, self.destroy)
                except Exception as ex:
                    self.after(0, lambda: self.status_label.configure(text=f"Error: {ex}"))
                    self.after(0, lambda: self.btn_cancel.configure(state="normal"))

            threading.Thread(target=work, daemon=True).start()

    app = SetupWizard()
    app.mainloop()

def run_fallback_setup_gui():
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("DLSS 5 Installer Setup")
    root.geometry("480x400")
    root.configure(bg="#0F1117")

    chk_desktop = tk.BooleanVar(value=True)
    chk_start = tk.BooleanVar(value=True)
    chk_launch = tk.BooleanVar(value=True)

    header = tk.Label(root, text="DLSS 5 Installer Setup", font=("Segoe UI", 16, "bold"), fg="#F1F5F9", bg="#0F1117")
    header.pack(anchor="w", padx=20, pady=(20, 10))

    frame = tk.LabelFrame(root, text="Settings", padx=12, pady=12, fg="#F1F5F9", bg="#181B22")
    frame.pack(fill="x", padx=20, pady=10)

    tk.Checkbutton(frame, text="Create Desktop shortcut", variable=chk_desktop, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12").pack(anchor="w", pady=4)
    tk.Checkbutton(frame, text="Create Start Menu shortcut", variable=chk_start, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12").pack(anchor="w", pady=4)
    tk.Checkbutton(frame, text="Launch DLSS 5 Installer after setup", variable=chk_launch, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12").pack(anchor="w", pady=4)

    def do_install():
        try:
            bundle_dir = get_bundle_dir()
            INSTALL_DIR.mkdir(parents=True, exist_ok=True)

            src_exe = bundle_dir / "DLSS5_Installer.exe"
            dst_exe = INSTALL_DIR / "DLSS5_Installer.exe"
            if src_exe.exists():
                shutil.copy2(src_exe, dst_exe)

            src_assets = bundle_dir / "Assets"
            dst_assets = INSTALL_DIR / "Assets"
            if src_assets.exists():
                if dst_assets.exists():
                    shutil.rmtree(dst_assets)
                shutil.copytree(src_assets, dst_assets)

            desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
            if chk_desktop.get() and desktop_dir.exists():
                create_shortcut(dst_exe, desktop_dir / "DLSS 5 Installer.lnk")

            start_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            if chk_start.get() and start_dir.exists():
                create_shortcut(dst_exe, start_dir / "DLSS 5 Installer.lnk")

            register_uninstaller(INSTALL_DIR, dst_exe)

            if chk_launch.get() and dst_exe.exists():
                subprocess.Popen([str(dst_exe)], cwd=str(INSTALL_DIR))

            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    btn = tk.Button(root, text="Install Now", command=do_install, bg="#2563EB", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), relief="flat", height=2)
    btn.pack(fill="x", padx=20, pady=20)

    root.mainloop()

if __name__ == "__main__":
    run_setup_gui()
