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
- **Link Objects/Collections**: Link objects or collections from one .blend file to another
- **Preview Mode**: See all changes before applying them (dry-run mode)
- **Progress Tracking**: Visual progress bars for long-running operations

### Safety Features
- **Trash Integration**: Files moved to system trash instead of permanent deletion
- **Validation**: Pre-flight checks before operations
- **Error Recovery**: Detailed error reporting and safe failure handling

## Installation

### Requirements

- Python 3.13 or above
- Blender 5.0 installed (tested with Blender 5.0, compatibility with earlier versions not guaranteed)
- pip (Python package manager)

### Installation Steps

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd blender_project_manager
```

#### 2. Create a Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated and prevents conflicts with other Python projects.

**Important:** This project requires Python 3.13 or above. If you have multiple Python versions installed, ensure you're using Python 3.13+.

**Using a Specific Python Version**

**macOS/Linux:**
```bash
# Create virtual environment with Python 3.13 or above
python3.13 -m venv venv
# Or use a newer version: python3.14 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version  # Should show Python 3.13.x or higher
```

If `python3.13` is not found, you may need to install Python 3.13+ first:
- **macOS**: Use Homebrew: `brew install python@3.13`
- **Linux**: Use your package manager, e.g., `sudo apt install python3.13 python3.13-venv`

**Windows:**
```bash
# If you have Python 3.13+ in PATH as 'python':
python -m venv venv

# Or specify the full path to Python 3.13+:
C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.13.x or higher
```

You should see `(venv)` appear in your terminal prompt when activated.

**Default Method (if Python 3.13+ is your default)**

If Python 3.13 or above is already your default Python version:

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Dependencies

With the virtual environment activated:

**macOS/Linux:**
```bash
pip3 install -r requirements.txt
```

**Windows:**
```bash
pip install -r requirements.txt
```

Or install packages individually:

**macOS/Linux:**
```bash
pip3 install PySide6
```

**Windows:**
```bash
pip install PySide6
```

#### 4. Verify Blender Installation

The application expects Blender to be installed at:

- **macOS**: `/Applications/Blender.app/Contents/MacOS/Blender`
- **Windows**: `C:/Program Files/Blender Foundation/Blender 5.0/blender.exe`
- **Linux**: `/usr/bin/blender`

If your Blender is installed elsewhere, you can update the path in:
`config/default_config.json`

#### 5. Run the Application

Make sure the virtual environment is activated (you should see `(venv)` in your prompt):

```bash
python main.py
```

**Note:** Every time you open a new terminal session, you'll need to activate the virtual environment again before running the application:

**macOS/Linux:**
```bash
cd blender_project_manager
source venv/bin/activate
python main.py
```

**Windows:**
```bash
cd blender_project_manager
venv\Scripts\activate
python main.py
```

## Usage

### Getting Started

1. **Open a Project**: Click "Select Project..." and select your Blender project root directory
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

The application will:
- Move/rename the file on disk
- Update all .blend files that reference it
- Show progress as it works

#### Rename Objects/Collections
1. Select a .blend file
2. Go to the "Rename Objects" tab
3. Click "Load Scenes" to load scene list
4. Click "Load Items" to see all objects/collections/materials
5. Select items to rename
6. Enter find/replace text
7. Click "Preview" then "Execute"

**Tip:** Enable "Auto load scenes and items when file is selected" to automatically load when the tab is visible.

#### Link Objects/Collections
1. Select a target .blend file (where you want to link into)
2. Go to the "Link Objects" tab
3. Click "Load Scenes" for the target file
4. Select the target scene
5. Click "🔒 Lock Target" to lock the target file
6. Select a source .blend file in the file browser
7. Click "Load Scenes" for the source file
8. Click "Load Objects/Collections" to see available items
9. Select items to link
10. Configure options (collection name, suffix, etc.)
11. Click "Execute Link"

**Tip:** Enable "Auto load scenes when file is selected" to automatically load when the tab is visible.

#### Find References
1. Select a .blend file or texture in the file browser
2. Click the "Find References" icon (when file is selected)
3. View all files that link to the selected file

#### Show Linked Files
1. Select a .blend file in the file browser
2. Click the "Show Linked Files" icon (when file is selected)
3. View all libraries, textures, and materials used in the file

### Supported File Types

- `.blend` - Blender scene files
- `.png`, `.jpg`, `.jpeg` - Texture files
- `.hdr`, `.exr` - HDR environment maps

### Configuration

The application stores settings in `~/.blender_project_manager/`:
- `config.json`: Application preferences, UI state, and tab settings
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

### Running in Development Mode
To run with debug output:
```bash
python -v main.py
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
Set your Blender path in `config/default_config.json`:

```json
{
  "blender": {
    "macos_path": "/your/custom/path/to/Blender.app/Contents/MacOS/Blender"
  }
}
```

Or ensure Blender is in your system PATH.

### "pip: command not found" on macOS

On macOS, use `pip3` instead of `pip`:

```bash
pip3 install -r requirements.txt
```

Alternatively, you can use:
```bash
python3 -m pip install -r requirements.txt
```

### Import Errors

Make sure you're running from the `blender_project_manager` directory with the virtual environment activated:

**macOS/Linux:**
```bash
cd blender_project_manager
source venv/bin/activate
python main.py
```

**Windows:**
```bash
cd blender_project_manager
venv\Scripts\activate
python main.py
```

### Permission Errors
Make sure you have write permissions for the project directory and config directory (`~/.blender_project_manager/`).

### Slow Operations
Large projects with many files may take time to process. Use the Preview mode to estimate operation time. The progress dialog will show you which files are being processed.

### UI Stalls When Selecting Files
If you experience brief UI freezes when selecting .blend files:
- This is normal when "Auto load" is enabled on the Rename Objects or Link Objects tabs
- Disable the "Auto load scenes" checkbox on those tabs to eliminate the stall
- Click "Load Scenes" manually when you need the scene list

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with PySide6 for the GUI
- Uses Blender's Python API for .blend file operations
- send2trash for safe file deletion

## Support

For bugs and feature requests, please open an issue on GitHub.
