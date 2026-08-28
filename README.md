# Folder & Icon Customizer

A polished Windows GUI for customizing folder icons, built with Python + PySide6.

## Features

- **Customize Folder** — apply any `.ico` / `.png` / `.jpg` to a folder (or all its
  sub-folders recursively) using `desktop.ini`. Includes an icon-index slider and
  a built-in icon suite picker.
- **Image → ICO Converter** — batch-convert PNG / JPG / BMP images into
  multi-resolution Windows icons (16–256 px) so you can grow your library.
- **Icon Library** — browse and preview the icons you added. Double-click an icon
  for a large preview and to apply it to a folder directly.

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
