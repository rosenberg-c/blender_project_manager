# Installation Guide

## Requirements

- Python 3.13 (not above)
- Blender 5.0 installed (tested with Blender 5.0, compatibility with earlier versions not guaranteed)
- pip (Python package manager)

## Installation Steps

### 1. Create a Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated and prevents conflicts with other Python projects.

**Important:** This project requires Python 3.13 specifically. If you have multiple Python versions installed, you need to create the virtual environment with Python 3.13 explicitly.

#### Using a Specific Python Version

**macOS/Linux:**
```bash
cd blender_project_manager

# Create virtual environment with Python 3.13 specifically
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version  # Should show Python 3.13.x
```

If `python3.13` is not found, you may need to install Python 3.13 first:
- **macOS**: Use Homebrew: `brew install python@3.13`
- **Linux**: Use your package manager, e.g., `sudo apt install python3.13 python3.13-venv`

**Windows:**
```bash
cd blender_project_manager

# If you have Python 3.13 in PATH as 'python':
python -m venv venv

# Or specify the full path to Python 3.13:
C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.13.x
```

You should see `(venv)` appear in your terminal prompt when activated.

#### Default Method (if Python 3.13 is your default)

If Python 3.13 is already your default Python version:

**macOS/Linux:**
```bash
cd blender_project_manager
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
cd blender_project_manager
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies

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

### 3. Verify Blender Installation

The application expects Blender to be installed at:

- **macOS**: `/Applications/Blender.app/Contents/MacOS/Blender`
- **Windows**: `C:/Program Files/Blender Foundation/Blender 5.0/blender.exe`
- **Linux**: `/usr/bin/blender`

If your Blender is installed elsewhere, you can update the path in:
`config/default_config.json`

### 4. Run the Application

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

## First Run

1. The application will open and prompt you to select a project directory
2. Navigate to your Blender project root directory (the folder containing your .blend files, textures, etc.)
3. Click "Select Folder"
4. The file browser will populate with your project files

## Usage

### Moving/Renaming Files

1. Select a file in the file browser (left panel)
2. In the operations panel (right), enter the new path
3. Click "Preview Changes" to see what will be updated
4. Click "Execute Move" to perform the operation

The application will:
- Move/rename the file on disk
- Update all .blend files that reference it
- Show progress as it works

### Supported File Types

- `.blend` - Blender scene files
- `.png`, `.jpg`, `.jpeg` - Texture files
- `.hdr`, `.exr` - HDR environment maps

## Troubleshooting

### "Blender not found" Error

Update the Blender path in `config/default_config.json`:

```json
{
  "blender": {
    "macos_path": "/your/custom/path/to/Blender.app/Contents/MacOS/Blender"
  }
}
```

### "pip: command not found" on macOS

On macOS, use `pip3` instead of `pip`:

```bash
pip3 install -r requirements.txt
```

Alternatively, you can create an alias or use:
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

### Operations Taking Too Long

For large projects with many .blend files, operations may take several minutes.
The progress dialog will show you which files are being processed.

## Development

To run in development mode with debug output:

```bash
python -v main.py
```

## Next Steps

Once the MVP is working, planned features include:
- Dependency graph visualization
- Object/collection renaming inside .blend files
- Batch operations (select multiple files)
- Broken reference detection and repair
- Search functionality
