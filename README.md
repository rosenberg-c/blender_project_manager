# Blender Project Manager

A desktop GUI application for managing Blender projects with automatic reference tracking and path updating.

## Features

### File Management
- **Visual File Browser**: Browse your Blender project files with an intuitive tree view
- **Pin Important Files**: Pin files/directories to keep them visible when collapsing the tree
- **Smart Search**: Filter files with instant search feedback

### Blender Integration
- **Move/Rename with Auto-Update**: Move or rename .blend files and automatically update all internal references
- **Texture Path Rebasing**: Automatically update texture paths when moving files
- **Reference Tracking**: Find all files that reference a specific .blend file or texture
- **Link Inspection**: View all linked libraries, textures, and materials in a .blend file

### Batch Operations
- **Rename Objects/Collections**: Batch rename objects and collections across multiple .blend files
- **Preview Mode**: See all changes before applying them (dry-run mode)
- **Progress Tracking**: Visual progress bars for long-running operations

### Safety Features
- **Trash Integration**: Files moved to system trash instead of permanent deletion
- **Validation**: Pre-flight checks before operations
- **Error Recovery**: Detailed error reporting and safe failure handling

## Installation

### Prerequisites
- Python 3.13 (not above)
- Blender 5.0 installed on your system (tested on Blender 5.0, compatibility with earlier versions not guaranteed)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/blender_project_manager.git
cd blender_project_manager
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python main.py
```

## Usage

### Getting Started

1. **Open a Project**: Click "Open Project" and select your Blender project root directory
2. **Browse Files**: Use the file browser on the left to navigate your project
3. **Select Files**: Click on any .blend file to enable operations
4. **Pin Files**: Click the checkbox next to important files to keep them visible

### Operations

#### Move/Rename Files
1. Select a .blend file in the file browser
2. Go to the "Move/Rename" tab
3. Enter the new path or name
4. Click "Preview" to see what will change
5. Click "Execute" to apply changes

#### Rename Objects/Collections
1. Select a .blend file
2. Go to the "Rename Objects" tab
3. Click "Load Items" to see all objects/collections/materials
4. Select items to rename
5. Enter find/replace text
6. Click "Preview" then "Execute"

#### Find References
1. Right-click on any .blend file or texture in the file browser
2. Select "Find References"
3. View all files that link to the selected file

#### Show Linked Files
1. Right-click on a .blend file
2. Select "Show Linked Files"
3. View all libraries, textures, and materials used in the file

### Configuration

The application stores settings in `~/.blender_project_manager/`:
- `config.json`: Application preferences and UI state
- Recent projects and pinned files are saved automatically

## Project Structure

```
blender_project_manager/
├── blender_lib/          # Blender interaction scripts
│   ├── list_links.py     # List linked files
│   ├── list_objects.py   # List objects/collections
│   ├── rename_objects.py # Rename operations
│   └── script_utils.py   # Shared utilities
├── controllers/          # Application controllers
│   ├── project_controller.py
│   └── file_operations_controller.py
├── core/                 # Core business logic
│   ├── file_scanner.py   # File discovery
│   └── path_rebaser.py   # Path rebasing logic
├── gui/                  # PySide6 GUI components
│   ├── main_window.py
│   ├── file_browser.py
│   ├── operations_panel.py
│   └── operations/       # Operation tabs
├── services/             # Service layer
│   └── blender_service.py
├── config/               # Configuration schemas
├── tests/                # Test suite
└── main.py              # Application entry point
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
This project follows PEP 8 with some modifications as documented in `agent_instructions.md`.

## Platform Support

- **macOS**: Fully supported (tested on macOS 14+ with Blender 5.0)
- **Linux**: Supported (requires Blender 5.0 in PATH or manual configuration)
- **Windows**: Supported (requires Blender 5.0 installation path configuration)

**Note**: This application is developed and tested with Blender 5.0. Compatibility with earlier versions of Blender is not tested or guaranteed.

## Troubleshooting

### Blender Not Found
Set your Blender path in the application settings or ensure Blender is in your system PATH.

### Permission Errors
Make sure you have write permissions for the project directory and config directory.

### Slow Operations
Large projects with many files may take time to process. Use the Preview mode to estimate operation time.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with PySide6 for the GUI
- Uses Blender's Python API for .blend file operations
- Icon handling via send2trash for safe file deletion

## Support

For bugs and feature requests, please open an issue on GitHub.
