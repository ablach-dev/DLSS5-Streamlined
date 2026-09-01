"""
DLSS 5 Streamlined Setup Wizard
===============================
Standard Windows Setup installer that allows choosing the installation path,
creates Desktop shortcuts, and provides a dedicated uninstaller.
"""

import os
import sys
import shutil
import subprocess
import winreg
import time
from pathlib import Path
from typing import Optional

DEFAULT_INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "Programs" / "DLSS5_Installer"

def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def create_shortcut(target_exe: Path, shortcut_path: Path, description: str = "DLSS 5 Installer", icon_path: Optional[Path] = None):
    """Creates a Windows .lnk shortcut using PowerShell WScript.Shell."""
    icon = str(icon_path or target_exe)
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{str(shortcut_path)}')
    $Shortcut.TargetPath = '{str(target_exe)}'
    $Shortcut.WorkingDirectory = '{str(target_exe.parent)}'
    $Shortcut.Description = '{description}'
    $Shortcut.IconLocation = '{icon},0'
    $Shortcut.Save()
    """
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)

def create_uninstaller_script(install_dir: Path, exe_path: Path):
    """Creates uninstaller script and registers in Windows Add/Remove Programs."""
    uninst_bat = install_dir / "uninstall.bat"
    uninst_content = f"""@echo off
title Uninstall DLSS 5 Installer
echo ===================================================
echo        Uninstall DLSS 5 Installer
echo ===================================================
echo.
set /p confirm=Are you sure you want to completely remove DLSS 5 Installer? (Y/N): 
if /i "%confirm%" neq "Y" exit /b 0

echo.
echo Removing shortcuts...
del "%USERPROFILE%\\Desktop\\DLSS 5 Installer.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\DLSS 5 Installer.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Uninstall DLSS 5 Installer.lnk" 2>nul

echo Removing Windows registry entries...
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DLSS5_Installer" /f 2>nul

echo Cleaning up installation files...
start /b "" cmd /c timeout /t 1 /nobreak ^>nul ^& rmdir /s /q "{str(install_dir)}"

echo.
echo ===================================================
echo  DLSS 5 Installer has been successfully uninstalled.
echo ===================================================
pause
exit /b 0
"""
    try:
        uninst_bat.write_text(uninst_content, encoding="utf-8")
    except Exception as e:
        print(f"Could not write uninstall.bat: {e}")

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
        from tkinter import filedialog
    except Exception:
        run_fallback_setup_gui()
        return

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    class SetupWizard(ctk.CTk):
        def __init__(self):
            super().__init__()

            self.title("DLSS 5 Installer Setup")
            self.geometry("560x520")
            self.minsize(520, 480)
            self.configure(fg_color="#0F1117")

            self._center(560, 520)
            self._build_ui()

        def _center(self, w, h):
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{w}x{h}+{int((sw-w)/2)}+{int((sh-h)/2)}")

        def _build_ui(self):
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=24, pady=(20, 14))

            title = ctk.CTkLabel(header, text="DLSS 5 Installer Setup", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color="#F1F5F9")
            title.pack(anchor="w")

            subtitle = ctk.CTkLabel(header, text="Select destination location and setup options.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#94A3B8")
            subtitle.pack(anchor="w", pady=(2, 0))

            card_dir = ctk.CTkFrame(self, fg_color="#181B22", corner_radius=10, border_width=1, border_color="#282D37")
            card_dir.pack(fill="x", padx=24, pady=(0, 12))

            inner_dir = ctk.CTkFrame(card_dir, fg_color="transparent")
            inner_dir.pack(fill="x", padx=16, pady=14)

            dir_label = ctk.CTkLabel(inner_dir, text="Destination Folder", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#F1F5F9")
            dir_label.pack(anchor="w", pady=(0, 6))

            dir_row = ctk.CTkFrame(inner_dir, fg_color="transparent")
            dir_row.pack(fill="x")

            self.dir_entry = ctk.CTkEntry(
                dir_row,
                height=36,
                fg_color="#0B0D12",
                border_color="#282D37",
                font=ctk.CTkFont(family="Segoe UI", size=11)
            )
            self.dir_entry.insert(0, str(DEFAULT_INSTALL_DIR))
            self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            browse_btn = ctk.CTkButton(
                dir_row,
                text="Browse...",
                width=80,
                height=36,
                fg_color="#2E3440",
                hover_color="#3B4252",
                text_color="#F1F5F9",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                command=self._browse_dir
            )
            browse_btn.pack(side="right")

            card_opts = ctk.CTkFrame(self, fg_color="#181B22", corner_radius=10, border_width=1, border_color="#282D37")
            card_opts.pack(fill="x", padx=24, pady=(0, 14))

            inner_opts = ctk.CTkFrame(card_opts, fg_color="transparent")
            inner_opts.pack(fill="x", padx=16, pady=14)

            opts_label = ctk.CTkLabel(inner_opts, text="Setup Shortcuts & Options", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#F1F5F9")
            opts_label.pack(anchor="w", pady=(0, 8))

            self.chk_desktop = ctk.CTkCheckBox(inner_opts, text="Create a Desktop shortcut", font=ctk.CTkFont(family="Segoe UI", size=12), fg_color="#2563EB")
            self.chk_desktop.select()
            self.chk_desktop.pack(anchor="w", pady=(0, 6))

            self.chk_start = ctk.CTkCheckBox(inner_opts, text="Create a Start Menu shortcut", font=ctk.CTkFont(family="Segoe UI", size=12), fg_color="#2563EB")
            self.chk_start.select()
            self.chk_start.pack(anchor="w", pady=(0, 6))

            self.chk_launch = ctk.CTkCheckBox(inner_opts, text="Launch DLSS 5 Installer after setup", font=ctk.CTkFont(family="Segoe UI", size=12), fg_color="#2563EB")
            self.chk_launch.select()
            self.chk_launch.pack(anchor="w")

            self.status_label = ctk.CTkLabel(self, text="Ready to install.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#94A3B8")
            self.status_label.pack(anchor="w", padx=24, pady=(0, 6))

            self.progress = ctk.CTkProgressBar(self, height=4, progress_color="#2563EB", fg_color="#1E232E")
            self.progress.set(0)
            self.progress.pack(fill="x", padx=24, pady=(0, 14))

            btn_row = ctk.CTkFrame(self, fg_color="transparent")
            btn_row.pack(fill="x", padx=24, pady=(0, 18))

            self.btn_install = ctk.CTkButton(
                btn_row,
                text="Install",
                height=40,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                fg_color="#2563EB",
                hover_color="#1D4ED8",
                text_color="#FFFFFF",
                command=self._start_install
            )
            self.btn_install.pack(side="right", fill="x", expand=True, padx=(8, 0))

            self.btn_cancel = ctk.CTkButton(
                btn_row,
                text="Cancel",
                height=40,
                width=90,
                fg_color="#2E3440",
                hover_color="#3B4252",
                text_color="#94A3B8",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                command=self.destroy
            )
            self.btn_cancel.pack(side="left")

        def _browse_dir(self):
            d = filedialog.askdirectory(title="Select Destination Folder", initialdir=self.dir_entry.get())
            if d:
                self.dir_entry.delete(0, "end")
                self.dir_entry.insert(0, os.path.normpath(d))

        def _start_install(self):
            target_path_str = self.dir_entry.get().strip()
            if not target_path_str:
                self.status_label.configure(text="Please specify an installation folder.")
                return

            install_path = Path(target_path_str).resolve()

            self.btn_install.configure(state="disabled")
            self.btn_cancel.configure(state="disabled")
            self.status_label.configure(text="Copying application files and assets...")
            self.progress.set(0.2)

            import threading
            def work():
                try:
                    bundle_dir = get_bundle_dir()
                    install_path.mkdir(parents=True, exist_ok=True)

                    src_exe = bundle_dir / "DLSS5_Installer.exe"
                    dst_exe = install_path / "DLSS5_Installer.exe"
                    if src_exe.exists():
                        shutil.copy2(src_exe, dst_exe)

                    src_assets = bundle_dir / "Assets"
                    dst_assets = install_path / "Assets"
                    if src_assets.exists():
                        if dst_assets.exists():
                            shutil.rmtree(dst_assets)
                        shutil.copytree(src_assets, dst_assets)

                    self.after(0, lambda: self.progress.set(0.6))

                    desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
                    if self.chk_desktop.get() and desktop_dir.exists():
                        create_shortcut(dst_exe, desktop_dir / "DLSS 5 Installer.lnk", "DLSS 5 Installer")

                    start_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                    if self.chk_start.get() and start_dir.exists():
                        create_shortcut(dst_exe, start_dir / "DLSS 5 Installer.lnk", "DLSS 5 Installer")

                    create_uninstaller_script(install_path, dst_exe)

                    self.after(0, lambda: self.progress.set(1.0))
                    self.after(0, lambda: self.status_label.configure(text="Installation completed successfully!"))

                    if self.chk_launch.get() and dst_exe.exists():
                        subprocess.Popen([str(dst_exe)], cwd=str(install_path))

                    time.sleep(0.6)
                    self.after(0, self.destroy)
                except Exception as ex:
                    self.after(0, lambda: self.status_label.configure(text=f"Error during installation: {ex}"))
                    self.after(0, lambda: self.btn_cancel.configure(state="normal"))

            threading.Thread(target=work, daemon=True).start()

    app = SetupWizard()
    app.mainloop()

def run_fallback_setup_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title("DLSS 5 Installer Setup")
    root.geometry("520x460")
    root.configure(bg="#0F1117")

    dir_var = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
    chk_desktop = tk.BooleanVar(value=True)
    chk_start = tk.BooleanVar(value=True)
    chk_launch = tk.BooleanVar(value=True)

    header = tk.Label(root, text="DLSS 5 Installer Setup", font=("Segoe UI", 16, "bold"), fg="#F1F5F9", bg="#0F1117")
    header.pack(anchor="w", padx=20, pady=(20, 10))

    frame_dir = tk.LabelFrame(root, text="Destination Folder", padx=12, pady=12, fg="#F1F5F9", bg="#181B22")
    frame_dir.pack(fill="x", padx=20, pady=10)

    entry = tk.Entry(frame_dir, textvariable=dir_var, font=("Segoe UI", 10), bg="#0B0D12", fg="#F1F5F9")
    entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def browse():
        d = filedialog.askdirectory(initialdir=dir_var.get())
        if d:
            dir_var.set(os.path.normpath(d))

    tk.Button(frame_dir, text="Browse...", command=browse, bg="#2E3440", fg="#F1F5F9", relief="flat").pack(side="right")

    frame_opts = tk.LabelFrame(root, text="Options", padx=12, pady=12, fg="#F1F5F9", bg="#181B22")
    frame_opts.pack(fill="x", padx=20, pady=10)

    tk.Checkbutton(frame_opts, text="Create Desktop shortcut", variable=chk_desktop, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12").pack(anchor="w", pady=2)
    tk.Checkbutton(frame_opts, text="Create Start Menu shortcut", variable=chk_start, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12").pack(anchor="w", pady=2)
    tk.Checkbutton(frame_opts, text="Launch DLSS 5 Installer after setup", variable=chk_launch, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12").pack(anchor="w", pady=2)

    def do_install():
        p = Path(dir_var.get().strip()).resolve()
        try:
            bundle_dir = get_bundle_dir()
            p.mkdir(parents=True, exist_ok=True)

            src_exe = bundle_dir / "DLSS5_Installer.exe"
            dst_exe = p / "DLSS5_Installer.exe"
            if src_exe.exists():
                shutil.copy2(src_exe, dst_exe)

            src_assets = bundle_dir / "Assets"
            dst_assets = p / "Assets"
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

            create_uninstaller_script(p, dst_exe)

            if chk_launch.get() and dst_exe.exists():
                subprocess.Popen([str(dst_exe)], cwd=str(p))

            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(root, text="Install Now", command=do_install, bg="#2563EB", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), relief="flat", height=2).pack(fill="x", padx=20, pady=15)
    root.mainloop()

if __name__ == "__main__":
    run_setup_gui()
