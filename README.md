# DLSS 5 One-Click Installer

An automated utility designed to streamline the installation and deployment of **DLSS 5**, **RenoDX**, and **ReShade Addon** runtime into target game directories.

---

## Overview

The DLSS 5 One-Click Installer automates what is normally a multi-step manual process:
1. Deploying the official ReShade 6.8.0 Addon runtime (`dxgi.dll`) and initial configuration.
2. Deploying core DLSS 5 runtime libraries and RenoDX addons directly to the game executable's folder.
3. Conditionally injecting the DirectX 11 bridge addon for DX11 titles.
4. Preserving original game files via automatic `.bak` backups.

---

## Quick Start

### For End Users (Single-File Standalone App)

1. Download **`DLSS5_Installer.exe`** directly from the [**Releases**](https://github.com/ablach-dev/DLSS5-Streamlined/releases) tab.
2. Open `DLSS5_Installer.exe`.
3. Click **Browse** and select your game's primary executable (`.exe`).
4. If the game runs on DirectX 11, toggle the **DirectX 11 Game** switch ON.
5. Click **Install DLSS 5**.

### Running from Source / Repository

1. Clone or download this repository.
2. Double-click `Launch_Installer.bat` (or run `python dlss5_installer.py`).
3. Select your game's executable (`.exe`), configure options, and click **Install DLSS 5**.

---

## Managed Components

| File | Target API | Description |
| :--- | :--- | :--- |
| `dxgi.dll` | DX10 / DX11 / DX12 | Official ReShade 6.8.0 64-bit Addon runtime. |
| `nvngx_dlss.dll` | All | DLSS core runtime library. |
| `nvngx_dlssnr.dll` | All | DLSS Ray Reconstruction / Neural Rendering runtime library. |
| `renodx-dlss5.addon64` | All | RenoDX DLSS 5 integration addon for ReShade. |
| `dlss5-dx11-bridge.addon64` | DX11 Only | DirectX 11 bridge addon (deployed only when DX11 is enabled). |

---

## Command-Line Interface (CLI)

The installer can also be executed headlessly or via automation scripts:

```bash
# Standard installation (DirectX 12 / Vulkan / DXGI)
DLSS5_Installer.exe "C:\Games\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe"

# DirectX 11 installation (includes DX11 bridge addon)
DLSS5_Installer.exe "C:\Games\The Witcher 3\bin\x64\witcher3.exe" --dx11

# Disable automatic backups
DLSS5_Installer.exe "C:\Games\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe" --no-backup

# Uninstall and restore backups
DLSS5_Installer.exe "C:\Games\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe" --uninstall
```

### CLI Arguments

* `exe`: Absolute or relative path to the target game executable.
* `--dx11`: Deploys the `dlss5-dx11-bridge.addon64` component for DirectX 11 titles.
* `--no-backup`: Skips creating `.bak` files when replacing existing libraries.
* `--uninstall`: Removes deployed DLLs/addons and restores any existing `.bak` backups.

---

## Building from Source

To compile the single-file standalone executable yourself:

```cmd
build_standalone_exe.bat
```
Output will be located at `dist\DLSS5_Installer.exe`.
