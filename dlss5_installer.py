"""
DLSS 5 Streamlined One-Click Installer
======================================
High-speed automated deployment for DLSS 5, RenoDX, and ReShade runtime.
"""

import os
import sys
import shutil
import queue
import urllib.request
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict

GITHUB_REPO = "ablach-dev/DLSS5-Streamlined"
RELEASE_TAG = "v0.1"
BASE_DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}"

CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "DLSS5_Cache"

CORE_ASSETS = [
    "dxgi.dll",
    "nvngx_dlss.dll",
    "nvngx_dlssnr.dll",
    "renodx-dlss5.addon64"
]
DX11_ASSET = "dlss5-dx11-bridge.addon64"
ALL_MANAGED_FILES = CORE_ASSETS + [
    DX11_ASSET,
    "ReShade.ini",
    "ReShade.log",
    "ReShadePreset.ini"
]

DEFAULT_RESHADE_INI = """\
[GENERAL]
EffectSearchPaths=.\\reshade-shaders\\Shaders\\**\\**
PreprocessorDefinitions=RESHADE_DEPTH_LINEARIZATION_FAR_PLANE=1000.0,RESHADE_DEPTH_INPUT_IS_UPSIDE_DOWN=0,RESHADE_DEPTH_INPUT_IS_REVERSED=0,RESHADE_DEPTH_INPUT_IS_LOGARITHMIC=0
TextureSearchPaths=.\\reshade-shaders\\Textures\\**\\**

[INPUT]
GamepadNavigation=0
KeyOverlay=36,0,0,0

[PROXY]
EnableProxyLibrary=0
ProxyLibrary=
"""

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def get_local_assets_dir() -> Optional[Path]:
    base = get_base_dir()
    if (base / "Assets").exists():
        return base / "Assets"
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent / "Assets"
        if exe_dir.exists():
            return exe_dir
    return None

class InstallerEngine:
    @staticmethod
    def ensure_asset(
        filename: str,
        log: Callable[[str, str], None],
        progress_cb: Optional[Callable[[float], None]] = None
    ) -> Optional[Path]:
        local_dir = get_local_assets_dir()
        if local_dir:
            local_file = local_dir / filename
            if local_file.exists() and local_file.stat().st_size > 0:
                return local_file

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cached_file = CACHE_DIR / filename
        if cached_file.exists() and cached_file.stat().st_size > 0:
            return cached_file

        url = f"{BASE_DOWNLOAD_URL}/{filename}"
        log(f"Downloading {filename} from GitHub...", "info")
        temp_file = CACHE_DIR / f"{filename}.part"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DLSS5-Installer/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_file, "wb") as f:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 1024 * 64

                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_cb:
                        progress_cb(downloaded / total_size)

            if temp_file.exists():
                temp_file.replace(cached_file)
                log(f"Successfully downloaded {filename}", "success")
                return cached_file
        except Exception as e:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            log(f"Failed to download {filename}: {e}", "error")

        return None

    @staticmethod
    def install(
        exe_path: str,
        is_dx11: bool = False,
        backup_existing: bool = True,
        log_callback: Optional[Callable[[str, str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        def log(msg: str, tag: str = "info"):
            if log_callback:
                log_callback(msg, tag)
            else:
                print(f"[{tag.upper()}] {msg}")

        def set_progress(val: float):
            if progress_callback:
                progress_callback(val)

        cleaned_path = exe_path.strip().strip('"').strip("'")
        game_exe = Path(cleaned_path).resolve()

        set_progress(0.05)
        if not game_exe.exists() or not game_exe.is_file():
            log(f"Game executable not found: {cleaned_path}", "error")
            return False

        game_dir = game_exe.parent
        log(f"Target Executable: {game_exe.name}", "info")
        log(f"Target Directory: {game_dir}", "info")

        required_assets = list(CORE_ASSETS)
        if is_dx11:
            required_assets.append(DX11_ASSET)
            log("DirectX 11 Bridge enabled -> Including dlss5-dx11-bridge.addon64", "info")
        else:
            old_dx11 = game_dir / DX11_ASSET
            if old_dx11.exists():
                try:
                    old_dx11.unlink()
                    log("Removed previous DX11 bridge addon.", "info")
                except Exception:
                    pass

        resolved_files: Dict[str, Path] = {}
        for idx, filename in enumerate(required_assets):
            log(f"Verifying asset ({idx+1}/{len(required_assets)}): {filename}...", "info")
            resolved = InstallerEngine.ensure_asset(
                filename,
                log,
                lambda p: set_progress(0.05 + 0.5 * ((idx + p) / len(required_assets)))
            )
            if not resolved or not resolved.exists():
                log(f"Could not prepare {filename}. Aborting installation.", "error")
                return False
            resolved_files[filename] = resolved

        set_progress(0.6)
        log("Deploying DLSS 5 and ReShade runtime to game directory...", "info")

        for idx, (filename, src_path) in enumerate(resolved_files.items()):
            dst_path = game_dir / filename

            if backup_existing and dst_path.exists():
                bak_path = dst_path.with_suffix(dst_path.suffix + ".bak")
                try:
                    if not bak_path.exists():
                        shutil.copy2(dst_path, bak_path)
                        log(f"Backed up: {filename} -> {bak_path.name}", "info")
                except Exception as ex:
                    log(f"Notice during backup ({filename}): {ex}", "warn")

            try:
                shutil.copy2(src_path, dst_path)
                log(f"Installed: {filename}", "success")
            except PermissionError:
                log(f"Permission denied writing {filename}. Please run installer as Administrator!", "error")
                return False
            except Exception as ex:
                log(f"Error copying {filename}: {ex}", "error")
                return False

            set_progress(0.6 + 0.35 * ((idx + 1) / len(resolved_files)))

        target_ini = game_dir / "ReShade.ini"
        if not target_ini.exists():
            try:
                target_ini.write_text(DEFAULT_RESHADE_INI, encoding="utf-8")
                log("Initialized default ReShade.ini configuration.", "info")
            except Exception as ex:
                log(f"Notice creating ReShade.ini: {ex}", "warn")

        set_progress(1.0)
        log("Installation complete! You can now launch your game.", "success")
        return True

    @staticmethod
    def uninstall(
        exe_path: str,
        log_callback: Optional[Callable[[str, str], None]] = None
    ) -> bool:
        def log(msg: str, tag: str = "info"):
            if log_callback:
                log_callback(msg, tag)
            else:
                print(f"[{tag.upper()}] {msg}")

        cleaned_path = exe_path.strip().strip('"').strip("'")
        game_exe = Path(cleaned_path).resolve()
        if not game_exe.exists() or not game_exe.is_file():
            log(f"Game executable not found: {cleaned_path}", "error")
            return False

        game_dir = game_exe.parent
        log(f"Uninstalling from: {game_dir}", "info")

        removed_count = 0
        for filename in ALL_MANAGED_FILES:
            target_file = game_dir / filename
            if target_file.exists():
                try:
                    target_file.unlink()
                    log(f"Removed: {filename}", "info")
                    removed_count += 1
                except PermissionError:
                    log(f"Permission denied removing {filename}. Run as Administrator!", "error")
                    return False
                except Exception as ex:
                    log(f"Failed to remove {filename}: {ex}", "warn")

            bak_file = target_file.with_suffix(target_file.suffix + ".bak")
            if bak_file.exists():
                try:
                    shutil.move(bak_file, target_file)
                    log(f"Restored backup: {filename}", "success")
                except Exception as ex:
                    log(f"Could not restore {bak_file.name}: {ex}", "warn")

        log(f"Uninstallation finished ({removed_count} files removed).", "success")
        return True


def launch_gui():
    try:
        import customtkinter as ctk
        from tkinter import filedialog
    except Exception:
        launch_fallback_tkinter_gui()
        return

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    BG_COLOR = "#0F1117"
    PANEL_BG = "#181B22"
    PANEL_BORDER = "#282D37"
    ACCENT_COLOR = "#2563EB"
    ACCENT_HOVER = "#1D4ED8"
    TEXT_COLOR = "#F1F5F9"
    TEXT_MUTED = "#94A3B8"
    INPUT_BG = "#0B0D12"

    class DLSS5App(ctk.CTk):
        def __init__(self):
            super().__init__()

            self.title("DLSS 5 Installer")
            self.geometry("640x600")
            self.minsize(580, 560)
            self.configure(fg_color=BG_COLOR)

            # Set icon
            ico = get_base_dir() / "icon.ico"
            if ico.exists():
                try:
                    self.iconbitmap(str(ico))
                except Exception:
                    pass

            self.ui_queue = queue.Queue()
            self.is_busy = False

            self._center_window(640, 600)
            self._init_ui()
            self._process_queue()

        def _center_window(self, width: int, height: int):
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = max(0, int((sw - width) / 2))
            y = max(0, int((sh - height) / 2))
            self.geometry(f"{width}x{height}+{x}+{y}")

        def _init_ui(self):
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=24, pady=(20, 14))

            title = ctk.CTkLabel(
                header,
                text="⚡ DLSS 5 Installer",
                font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                text_color=TEXT_COLOR
            )
            title.pack(anchor="w")

            subtitle = ctk.CTkLabel(
                header,
                text="Automated deployment of DLSS 5, RenoDX, and ReShade runtime.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=TEXT_MUTED
            )
            subtitle.pack(anchor="w", pady=(2, 0))

            card = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=10, border_width=1, border_color=PANEL_BORDER)
            card.pack(fill="x", padx=24, pady=(0, 12))

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="x", padx=16, pady=16)

            exe_label = ctk.CTkLabel(
                card_inner,
                text="Game Executable",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=TEXT_COLOR
            )
            exe_label.pack(anchor="w", pady=(0, 6))

            input_row = ctk.CTkFrame(card_inner, fg_color="transparent")
            input_row.pack(fill="x")

            self.path_entry = ctk.CTkEntry(
                input_row,
                placeholder_text="Browse or paste path to game .exe...",
                height=36,
                fg_color=INPUT_BG,
                border_color=PANEL_BORDER,
                font=ctk.CTkFont(family="Segoe UI", size=12)
            )
            self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.path_entry.bind("<KeyRelease>", self._on_path_change)

            browse_btn = ctk.CTkButton(
                input_row,
                text="Browse",
                width=80,
                height=36,
                fg_color="#2E3440",
                hover_color="#3B4252",
                text_color=TEXT_COLOR,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                command=self._browse
            )
            browse_btn.pack(side="right")

            self.folder_preview = ctk.CTkLabel(
                card_inner,
                text="Target folder will appear here",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=TEXT_MUTED,
                anchor="w"
            )
            self.folder_preview.pack(fill="x", pady=(6, 0))

            opts_card = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=10, border_width=1, border_color=PANEL_BORDER)
            opts_card.pack(fill="x", padx=24, pady=(0, 14))

            opts_inner = ctk.CTkFrame(opts_card, fg_color="transparent")
            opts_inner.pack(fill="x", padx=16, pady=14)

            self.dx11_switch = ctk.CTkSwitch(
                opts_inner,
                text="DirectX 11 Game",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                progress_color=ACCENT_COLOR
            )
            self.dx11_switch.pack(anchor="w")

            dx11_hint = ctk.CTkLabel(
                opts_inner,
                text="Enable if game uses DirectX 11 (adds DX11 bridge addon). Leave off for DX12 / Vulkan.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=TEXT_MUTED
            )
            dx11_hint.pack(anchor="w", padx=(46, 0), pady=(1, 10))

            self.backup_check = ctk.CTkCheckBox(
                opts_inner,
                text="Create backups of existing files (.bak)",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color=ACCENT_COLOR,
                hover_color=ACCENT_HOVER
            )
            self.backup_check.select()
            self.backup_check.pack(anchor="w")

            btn_row = ctk.CTkFrame(self, fg_color="transparent")
            btn_row.pack(fill="x", padx=24, pady=(0, 10))

            self.install_btn = ctk.CTkButton(
                btn_row,
                text="Install DLSS 5",
                height=40,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                fg_color=ACCENT_COLOR,
                hover_color=ACCENT_HOVER,
                text_color="#FFFFFF",
                command=self._start_install
            )
            self.install_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

            self.uninstall_btn = ctk.CTkButton(
                btn_row,
                text="Uninstall",
                height=40,
                width=110,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color="#2E3440",
                hover_color="#3B4252",
                text_color=TEXT_MUTED,
                command=self._start_uninstall
            )
            self.uninstall_btn.pack(side="right")

            self.progress_bar = ctk.CTkProgressBar(self, height=4, progress_color=ACCENT_COLOR, fg_color="#1E232E")
            self.progress_bar.set(0)
            self.progress_bar.pack(fill="x", padx=24, pady=(0, 8))

            log_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=10, border_width=1, border_color=PANEL_BORDER)
            log_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

            self.log_text = ctk.CTkTextbox(
                log_frame,
                font=ctk.CTkFont(family="Consolas", size=11),
                fg_color="transparent",
                text_color="#CBD5E1",
                wrap="word"
            )
            self.log_text.pack(fill="both", expand=True, padx=12, pady=10)

        def _process_queue(self):
            try:
                while True:
                    action, data = self.ui_queue.get_nowait()
                    if action == "log":
                        msg = data
                        t = time.strftime("%H:%M:%S")
                        self.log_text.insert("end", f"[{t}] {msg}\n")
                        self.log_text.see("end")
                    elif action == "progress":
                        self.progress_bar.set(data)
                    elif action == "busy":
                        st = "disabled" if data else "normal"
                        self.install_btn.configure(state=st)
                        self.uninstall_btn.configure(state=st)
                        self.dx11_switch.configure(state=st)
                        self.path_entry.configure(state=st)
            except queue.Empty:
                pass
            self.after(50, self._process_queue)

        def _log(self, msg: str, tag: str = "info"):
            self.ui_queue.put(("log", msg))

        def _set_progress(self, val: float):
            self.ui_queue.put(("progress", val))

        def _on_path_change(self, event=None):
            p = self.path_entry.get().strip().strip('"').strip("'")
            if p and os.path.isfile(p):
                self.folder_preview.configure(text=f"Target: {os.path.dirname(p)}")
            else:
                self.folder_preview.configure(text="Target folder will appear here")

        def _browse(self):
            f = filedialog.askopenfilename(
                title="Select Game Executable",
                filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
            )
            if f:
                path = os.path.normpath(f)
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, path)
                self.folder_preview.configure(text=f"Target: {os.path.dirname(path)}")
                self._log(f"Selected: {os.path.basename(path)}", "info")

        def _start_install(self):
            if self.is_busy:
                return
            p = self.path_entry.get().strip().strip('"').strip("'")
            if not p or not os.path.isfile(p):
                self._log("Please select a valid game executable (.exe) first.", "error")
                return

            self.is_busy = True
            self.ui_queue.put(("busy", True))
            self.ui_queue.put(("progress", 0.0))
            self._log("Starting installation...", "info")

            is_dx11 = bool(self.dx11_switch.get())
            backup = bool(self.backup_check.get())

            def worker():
                try:
                    ok = InstallerEngine.install(
                        exe_path=p,
                        is_dx11=is_dx11,
                        backup_existing=backup,
                        log_callback=self._log,
                        progress_callback=self._set_progress
                    )
                    if not ok:
                        self._log("Installation did not finish cleanly. Check errors above.", "error")
                except Exception as ex:
                    self._log(f"Unexpected error: {ex}", "error")
                finally:
                    self.is_busy = False
                    self.ui_queue.put(("busy", False))

            threading.Thread(target=worker, daemon=True).start()

        def _start_uninstall(self):
            if self.is_busy:
                return
            p = self.path_entry.get().strip().strip('"').strip("'")
            if not p or not os.path.isfile(p):
                self._log("Please select a valid game executable (.exe) first.", "error")
                return

            self.is_busy = True
            self.ui_queue.put(("busy", True))
            self._log("Starting uninstallation...", "info")

            def worker():
                try:
                    InstallerEngine.uninstall(p, log_callback=self._log)
                except Exception as ex:
                    self._log(f"Uninstall error: {ex}", "error")
                finally:
                    self.is_busy = False
                    self.ui_queue.put(("busy", False))

            threading.Thread(target=worker, daemon=True).start()

    app = DLSS5App()
    app.mainloop()


def launch_fallback_tkinter_gui():
    import tkinter as tk
    from tkinter import filedialog, ttk

    root = tk.Tk()
    root.title("DLSS 5 Installer")
    root.geometry("600x540")
    root.configure(bg="#0F1117")

    ico = get_base_dir() / "icon.ico"
    if ico.exists():
        try:
            root.iconbitmap(str(ico))
        except Exception:
            pass

    exe_var = tk.StringVar()
    dx11_var = tk.BooleanVar(value=False)
    backup_var = tk.BooleanVar(value=True)

    header = tk.Label(root, text="⚡ DLSS 5 Installer", font=("Segoe UI", 16, "bold"), fg="#F1F5F9", bg="#0F1117")
    header.pack(anchor="w", padx=20, pady=(16, 2))

    subtitle = tk.Label(root, text="Automated deployment of DLSS 5, RenoDX, and ReShade runtime.", font=("Segoe UI", 10), fg="#94A3B8", bg="#0F1117")
    subtitle.pack(anchor="w", padx=20, pady=(0, 12))

    frame_exe = tk.LabelFrame(root, text="Game Executable", padx=12, pady=12, fg="#F1F5F9", bg="#181B22", font=("Segoe UI", 10, "bold"))
    frame_exe.pack(fill="x", padx=20, pady=(0, 10))

    entry = tk.Entry(frame_exe, textvariable=exe_var, font=("Segoe UI", 10), bg="#0B0D12", fg="#F1F5F9", insertbackground="#F1F5F9")
    entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def browse():
        f = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")])
        if f:
            exe_var.set(os.path.normpath(f))

    tk.Button(frame_exe, text="Browse", command=browse, bg="#2E3440", fg="#F1F5F9", relief="flat", padx=10).pack(side="right")

    frame_opts = tk.LabelFrame(root, text="Options", padx=12, pady=12, fg="#F1F5F9", bg="#181B22", font=("Segoe UI", 10, "bold"))
    frame_opts.pack(fill="x", padx=20, pady=(0, 10))

    tk.Checkbutton(frame_opts, text="DirectX 11 Game (Include DX11 Bridge Addon)", variable=dx11_var, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12", activebackground="#181B22", activeforeground="#F1F5F9").pack(anchor="w")
    tk.Checkbutton(frame_opts, text="Create backups of existing files (.bak)", variable=backup_var, bg="#181B22", fg="#F1F5F9", selectcolor="#0B0D12", activebackground="#181B22", activeforeground="#F1F5F9").pack(anchor="w")

    btn_frame = tk.Frame(root, bg="#0F1117")
    btn_frame.pack(fill="x", padx=20, pady=(0, 10))

    prog = ttk.Progressbar(root, maximum=100)
    prog.pack(fill="x", padx=20, pady=(0, 10))

    log_box = tk.Text(root, height=10, font=("Consolas", 10), bg="#181B22", fg="#CBD5E1", relief="flat", padx=10, pady=8)
    log_box.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def log(msg, tag="info"):
        t = time.strftime("%H:%M:%S")
        log_box.insert("end", f"[{t}] {msg}\n")
        log_box.see("end")

    def do_install():
        p = exe_var.get().strip().strip('"').strip("'")
        if not p or not os.path.isfile(p):
            log("Please select a valid game executable.", "error")
            return
        threading.Thread(target=lambda: InstallerEngine.install(p, dx11_var.get(), backup_var.get(), log, lambda v: prog.configure(value=v*100)), daemon=True).start()

    def do_uninstall():
        p = exe_var.get().strip().strip('"').strip("'")
        if not p or not os.path.isfile(p):
            log("Please select a valid game executable first.", "error")
            return
        threading.Thread(target=lambda: InstallerEngine.uninstall(p, log), daemon=True).start()

    tk.Button(btn_frame, text="Install DLSS 5", command=do_install, bg="#2563EB", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), relief="flat", height=2).pack(side="left", fill="x", expand=True, padx=(0, 6))
    tk.Button(btn_frame, text="Uninstall", command=do_uninstall, bg="#2E3440", fg="#94A3B8", relief="flat", height=2, width=12).pack(side="right")

    root.mainloop()


def run_cli():
    import argparse
    parser = argparse.ArgumentParser(description="DLSS 5 Installer")
    parser.add_argument("exe", nargs="?", help="Path to game executable (.exe)")
    parser.add_argument("--dx11", action="store_true", help="Install DX11 bridge addon")
    parser.add_argument("--no-backup", action="store_true", help="Disable backups")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall components")

    args = parser.parse_args()

    if not args.exe:
        launch_gui()
        return

    if args.uninstall:
        ok = InstallerEngine.uninstall(args.exe)
    else:
        ok = InstallerEngine.install(
            exe_path=args.exe,
            is_dx11=args.dx11,
            backup_existing=not args.no_backup
        )

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    run_cli()
