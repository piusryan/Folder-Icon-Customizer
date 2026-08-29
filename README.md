# Folder & Icon Customizer

A polished Windows GUI for customizing folder icons, built with Python + PySide6.

## Features

- **Customize Folder** — apply any `.ico` / `.png` / `.jpg` to one folder or to
  **many folders at once** (batch), or to all sub-folders recursively, using
  `desktop.ini`. Includes an icon-index slider and a built-in icon suite picker.
- **Copy Style From Folder** — clone an already-customized folder's icon (and its
  icon index) onto many folders at once.
- **Drag & Drop** — drop an image right onto the app to apply it as the icon for
  your queued folders.
- **Image → ICO Converter** — batch-convert PNG / JPG / BMP images into
  multi-resolution Windows icons (16–256 px) so you can grow your library.
- **Icon Library** — browse and preview your icons with a clean gallery view.
  Rename, delete and favourite icons (with a "★ Favorites only" filter), import
  shared packs, and inspect every icon embedded inside a multi-image `.ico` via an
  index preview grid. Double-click for a large preview or apply directly to a folder.
- **Icon Studio** — design icons from scratch: solid/gradient/pattern fills,
  an optional base image, effects (shadow, glow, border, corner radius, opacity,
  blur) and a text/emoji overlay, with a live preview and Undo/Redo. Export as
  PNG / ICO, save as a **preset**, or ship a shareable **pack**.
- **Brand Maker** — type a company/product name, pick a style, and get a polished
  branded icon in seconds (great for demos). Apply it, save it, or export the full
  **multi-platform asset set** (favicon, iOS, macOS, Android, Windows, PWA/web).
- **Presets & Theme Packs** — save your looks for reuse, restart with the built-in
  theme packs (Neon, Ocean, Sunset, …), and share them via pack import/export.
- **Explorer Right-Click Menu** — optionally add a "Customize with Folder Icon
  Studio…" entry to the Windows folder context menu (needs Administrator rights).
- **Remembers your settings** — window size and your last-used folder are restored
  on the next launch.

## Requirements

- Windows (folder customization relies on the `desktop.ini` mechanism)
- Python 3.10+

## Setup & Run

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Building a standalone .exe

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "IconCustomizer" --add-data "icons;icons" main.py
```

The executable appears in `dist\IconCustomizer.exe`.

## How folder customization works

A `desktop.ini` is created inside each target folder:

```
[.ShellClassInfo]
IconResource=path\to\icon.ico,0
```

Windows only honours it when the `System` and `Hidden` attributes are set on both
the folder and the `desktop.ini`, which this app does automatically. After
applying, Explorer usually refreshes within a few seconds; if not, restart
Explorer or refresh the folder.

> The image converter and library work on any OS; only folder-icon application is
> Windows-specific (on non-Windows the app warns on startup).
