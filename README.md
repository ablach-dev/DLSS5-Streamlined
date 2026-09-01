# DLSS 5 One-Click Streamlined Installer

An automated utility designed to streamline the installation and deployment of **DLSS 5**, **RenoDX**, and **ReShade Addon** runtime into target game directories.

---

## Quick Start

### Windows Setup Wizard (Recommended)

1. Download **`DLSS5_Setup.exe`** from the [**Releases**](https://github.com/ablach-dev/DLSS5-Streamlined/releases) tab.
2. Run `DLSS5_Setup.exe`.
3. Choose your desired destination folder (defaults to `%LOCALAPPDATA%\Programs\DLSS5_Installer`).
4. Click **Install**. The setup wizard will unpack the application and create a **Desktop shortcut**.
5. Launch **DLSS 5 Installer** from your Desktop:
   - Click **Browse** and select your game's main executable (`.exe`).
   - If the game uses DirectX 11, toggle the **DirectX 11 Game** switch ON.
   - Click **Install DLSS 5**.

### Uninstallation

* **From Windows Settings**: Go to **Windows Settings > Apps > Installed apps** (or Add/Remove Programs) and click **Uninstall** on **DLSS 5 Installer**.
* **From Install Directory**: Run `uninstall.bat` inside the installation folder.

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

# Uninstall from game directory and restore original backups
DLSS5_Installer.exe "C:\Games\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe" --uninstall
```

---

## Building from Source

To compile the standalone setup wizard executable:

```cmd
build_setup_installer.bat
```
Output will be located at `dist\DLSS5_Setup.exe`.
