# Folder & Icon Customizer

A polished Windows GUI application for customizing folder icons, built with Python and PySide6. Easily apply custom icons to folders, convert images to ICO format, and manage your icon library.

## ✨ Features

- **🎨 Customize Folders** — Apply `.ico`, `.png`, or `.jpg` icons to folders (batch: many at once, or recursively to all subfolders) using `desktop.ini`. Includes an icon-index slider and a built-in icon suite picker.
- **🔄 Image → ICO Converter** — Batch-convert PNG, JPG, and BMP images into multi-resolution Windows icons (16–256 px) to grow your library.
- **📚 Icon Library** — Browse and preview your icons with a clean gallery view. Double-click for a large preview or apply directly to a folder. Import shared icon packs here too.
- **✨ Icon Studio** — Design icons from scratch: solid/gradient/pattern fills, an optional base image, effects (shadow, glow, border, corner radius, opacity, blur), and a text/emoji overlay with a live preview. Export as PNG/ICO, save as a preset, or export a shareable pack.
- **💾 Presets & Theme Packs** — Save your looks for reuse, load built-in theme packs (Neon, Ocean, Sunset, …), and share them with others via pack import/export (.icp / .zip).

## 🖥️ Requirements

- **Windows** (folder customization relies on the `desktop.ini` mechanism)
- **Python 3.10+**
- **Dependencies:** PySide6 (6.6+), Pillow (10.0+)

## 🚀 Quick Start

```powershell
# Clone the repository
git clone https://github.com/yourusername/folder-icon-customizer.git
cd folder-icon-customizer

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

## 📦 Build Standalone Executable

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "IconCustomizer" --add-data "icons;icons" main.py
```

The executable will be created at `dist\IconCustomizer.exe`.

## 💡 How It Works

Folder customization on Windows uses a `desktop.ini` file placed in the target folder:

```ini
[.ShellClassInfo]
IconResource=path\to\icon.ico,0
```

The app automatically sets the required `System` and `Hidden` attributes on both the folder and the `desktop.ini` file. Windows typically refreshes the icon within seconds; if needed, restart Explorer or refresh the folder manually.

> **Note:** The image converter and icon library work on any OS. Only folder-icon application is Windows-specific (the app warns on startup if run on other platforms).

## 📄 License

[Add your license here]

## 👤 Author

[Your name]
