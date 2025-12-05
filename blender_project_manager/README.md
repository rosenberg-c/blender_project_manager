# Blender Project Manager

A desktop GUI application for managing Blender projects with automatic reference tracking and updating.

## Features

- Visual file browser for Blender projects
- Move/rename files with automatic reference updates
- Preview changes before applying (dry-run mode)
- Progress tracking for long operations
- Support for .blend files, textures, and other assets

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Requirements

- Python 3.10+
- Blender installed (default: /Applications/Blender.app on macOS)
- PySide6

## Project Structure

```
blender_project_manager/
├── blender_lib/      # Core library (refactored from scripts)
├── services/         # Business logic
├── controllers/      # Application state management
├── gui/              # PySide6 GUI components
├── config/           # Configuration files
└── main.py           # Application entry point
```

## License

MIT
