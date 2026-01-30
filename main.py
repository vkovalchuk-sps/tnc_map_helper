"""Main entry point for TNC Map Helper application"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from application.main_window import MainWindow


def main() -> None:
    """Main function to start the application"""
    app = QApplication(sys.argv)
    
    # Get base path
    # When running as standalone exe, use the directory where the exe is located
    # When running as Python script, use the directory where main.py is located
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundled exe
        base_path = Path(sys.executable).parent
    else:
        # Running as Python script
        base_path = Path(__file__).parent
    
    window = MainWindow(base_path)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
