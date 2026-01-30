# T&C Map Helper

Automated tool for generating T&C mapping artifacts including XTL files, test data.

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
git clone https://github.com/vkovalchuk-sps/tnc_map_helper.git
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

Last Updated: January 30, 2026
