"""Main entry point for TNC Map Helper application"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from application.main_window import MainWindow


def main() -> None:
    """Main function to start the application"""
    app = QApplication(sys.argv)
    
    # Get base path (directory where main.py is located)
    base_path = Path(__file__).parent
    
    window = MainWindow(base_path)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
