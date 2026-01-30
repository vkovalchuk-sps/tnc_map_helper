# T&C Map Helper

Automated tool for generating T&C mapping artifacts including XTL files, test data, and configuration files.

## Table of Contents

- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Building Executable](#building-executable)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- **Windows 10/11** (64-bit recommended)
- **Python 3.12+** installed and added to PATH
- **Git** (for version control)

### Step 1: Install Python 3.12

1. Download Python 3.12 from [python.org](https://www.python.org/downloads/)
2. During installation, **IMPORTANT**: Check the box "Add Python to PATH"
3. Choose "Install Now" or customize installation
4. Verify installation:
   ```cmd
   python --version
   ```
   Should output: `Python 3.12.x` or higher

### Step 2: Clone Repository

```cmd
git clone <repository-url>
cd tnc_map_helper
```

### Step 3: Create Virtual Environment

Creating a virtual environment isolates project dependencies:

```cmd
python -m venv .venv
```

### Step 4: Activate Virtual Environment

On Windows:
```cmd
.venv\Scripts\activate
```

You should see `(.venv)` prefix in your command prompt.

### Step 5: Install Dependencies

Install all required libraries listed in `requirements.txt`:

```cmd
pip install -r requirements.txt
```

This will install:
- **PyQt6** (>=6.5.2) - GUI framework
- **openpyxl** (>=3.0.10) - Excel file handling
- **beautifulsoup4** (>=4.12.0) - HTML/XML parsing

Verify installation:
```cmd
pip list
```

---

## Running the Application

### From Command Line

1. **Activate virtual environment** (if not already activated):
   ```cmd
   .venv\Scripts\activate
   ```

2. **Run the application**:
   ```cmd
   python main.py
   ```

   The application window should open with the main interface.

### Application Features

- **Parse Spreadsheet** - Import and parse TOMMM spreadsheets
- **Parse CSV Templates** - Process template archives
- **Parse TOMMM Page** - Extract scenario information
- **View TLI Fields** - Browse TLI field properties
- **View Sourcing Groups** - Inspect sourcing group configuration
- **Generate Artifacts** - Create XTL files and test data
- **Edit Database** - Manage TLI field properties

### Working with Input Files

The application automatically loads files from the `input/` folder:

```
tnc_map_helper/
├── input/                    # Place your input files here
│   ├── *.xlsx               # Spreadsheet files
│   ├── *.zip                # CSV template archives
│   └── *.mhtml              # TOMMM saved pages
└── output/                   # Generated artifacts appear here
```

---

## Building Executable

### Prerequisites for Building

Install PyInstaller (if not in requirements):
```cmd
pip install pyinstaller
```

### Build Process

1. **Activate virtual environment**:
   ```cmd
   .venv\Scripts\activate
   ```

2. **Clean previous builds** (optional but recommended):
   ```cmd
   python -m PyInstaller --clean --noconfirm TNCMapHelper.spec
   ```

   Or without cleaning (faster):
   ```cmd
   python -m PyInstaller --noconfirm TNCMapHelper.spec
   ```

3. **Output**:
   - Executable: `dist/TnCMapHelper/TnCMapHelper.exe`
   - Supporting files: `dist/TnCMapHelper/` (entire folder required)

### Running the Built Executable

```cmd
dist\TnCMapHelper\TnCMapHelper.exe
```

Or simply double-click `TnCMapHelper.exe` in the file explorer.

### Distribution

To distribute the application:

1. Copy the entire `dist/TnCMapHelper/` folder
2. Create installer or share as portable folder
3. Users can run the `.exe` without Python installed

**Note**: The executable includes all dependencies and the database, making it completely self-contained.

### Build Configuration

The build is configured via `TNCMapHelper.spec`:

- **Entry point**: `main.py`
- **Icon**: `application/icon.png`
- **Included data files**:
  - XTL templates
  - Application icon
  - Database file
  - Configuration folder
- **Hidden imports**: BeautifulSoup4, openpyxl submodules (for compatibility)
- **Console window**: Disabled (GUI-only)

---

## Project Structure

```
tnc_map_helper/
├── application/                    # Main application package
│   ├── __init__.py
│   ├── main_window.py             # Main application window
│   ├── config.py                  # Configuration management
│   ├── translations.py            # i18n support (UA/EN)
│   ├── xtl_code_generators.py     # XTL generation logic
│   │
│   ├── database/                  # Database operations
│   │   ├── database_operations.py # Database CRUD operations
│   │   ├── database_editor.py     # Database editor UI
│   │   └── database.db            # SQLite database
│   │
│   ├── parsers/                   # Data parsing modules
│   │   ├── spreadsheet_parser.py  # Excel spreadsheet parsing
│   │   ├── csv_parser.py          # CSV template parsing
│   │   └── tnc_parser.py          # TOMMM page parsing
│   │
│   ├── dialogs/                   # Dialog windows
│   │   ├── about_dialog.py        # About dialog
│   │   ├── scenarios_dialog.py    # Scenarios viewer
│   │   └── ...
│   │
│   ├── templates/                 # XTL template files
│   │   ├── poRsxWrite.xtl        # 850 document template
│   │   ├── pcRsxWrite.xtl        # 860 document template
│   │   └── ...
│   │
│   ├── ui/                        # UI components
│   │   └── components.py
│   │
│   └── icon.png                   # Application icon
│
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
├── TNCMapHelper.spec              # PyInstaller build configuration
├── .gitignore                     # Git ignore patterns
├── README.md                      # This file
│
├── input/                         # User input files (auto-loaded)
├── output/                        # Generated artifacts
│
└── .venv/                         # Virtual environment (local)
```

---

## Requirements

### Python Dependencies

All dependencies are listed in `requirements.txt`:

```
PyQt6>=6.5.2
openpyxl>=3.0.10
beautifulsoup4>=4.12.0
```

### System Requirements

- **OS**: Windows 10/11 (64-bit recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 
  - Python + dependencies: ~500MB
  - Virtual environment: ~200MB
  - Built executable: ~150-200MB
- **Display**: 1024x768 minimum (1920x1080 recommended)

### Database Requirements

- SQLite 3.x (included with Python)
- Database file: `application/database/database.db`
- Contains properties for 100+ TLI fields

---

## Troubleshooting

### Python Not Found

**Error**: `'python' is not recognized as an internal or external command`

**Solution**:
1. Verify Python installation: `python --version`
2. If not found, reinstall Python and check "Add Python to PATH"
3. Restart command prompt after installation
4. Use full path: `C:\Python312\python.exe main.py`

### Virtual Environment Issues

**Error**: `.venv\Scripts\activate not found`

**Solution**:
```cmd
# Recreate virtual environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'PyQt6'`

**Solution**:
1. Verify virtual environment is activated (should see `(.venv)` prefix)
2. Reinstall dependencies:
   ```cmd
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Database Errors

**Error**: `Database file not found` or `Unable to open database`

**Solution**:
1. Check `application/database/database.db` exists
2. Run `python -c "from application.database.database_operations import Database; Database('application/database/database.db')"`
3. Database will be created/initialized automatically

### PyInstaller Build Fails

**Error**: `ModuleNotFoundError during build`

**Solution**:
```cmd
# Clean previous build
rmdir /s /q build dist __pycache__

# Reinstall PyInstaller
pip install --upgrade pyinstaller

# Rebuild
python -m PyInstaller --clean --noconfirm TNCMapHelper.spec
```

### Application Crashes on Startup

**Error**: Application closes immediately

**Solution**:
1. Check Python version: `python --version` (must be 3.12+)
2. Verify all dependencies: `pip list`
3. Check for encoding issues in `.py` files
4. Try running from command line to see error messages:
   ```cmd
   python main.py
   ```

### Port/Database Lock Issues

**Error**: `database is locked` or `cannot open database`

**Solution**:
1. Close all instances of the application
2. Delete temporary database files in `application/.config/`
3. Restart the application

---

## Development Workflow

### Making Code Changes

1. Activate virtual environment:
   ```cmd
   .venv\Scripts\activate
   ```

2. Make changes to Python files

3. Test the application:
   ```cmd
   python main.py
   ```

4. Commit changes:
   ```cmd
   git add .
   git commit -m "Description of changes"
   ```

### Creating a Release Build

```cmd
# Activate environment
.venv\Scripts\activate

# Clean and rebuild
python -m PyInstaller --clean --noconfirm TNCMapHelper.spec

# Test the executable
dist\TnCMapHelper\TnCMapHelper.exe

# Commit build configuration
git add TNCMapHelper.spec
git commit -m "Update build configuration"
```

---

## Version Information

- **Application**: TnC Map Helper v1.0+
- **Python**: 3.12.2
- **PyQt6**: 6.5.2+
- **Database**: SQLite 3.x
- **Build Tool**: PyInstaller 6.x

---

## Support & Documentation

- **Issue Tracker**: [GitHub Issues]
- **Documentation**: See `TnC Map Helper - English.docx` and `TnC Map Helper.docx`
- **Database Structure**: See `DB_VERSION_README.md`
- **Configuration**: See `application/config.py`

---

## License

Internal SPS Commerce tool

---

## Quick Command Reference

```cmd
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py

# Build
python -m PyInstaller --clean --noconfirm TNCMapHelper.spec

# Clean
rmdir /s /q build dist __pycache__

# Check dependencies
pip list
pip show PyQt6 openpyxl beautifulsoup4
```

---

Last Updated: January 30, 2026
