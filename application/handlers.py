"""Event handlers for the main window"""

from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from application.file_handlers import InputFileFinder, OutputFileWriter, XTLParser
from application.translations import TRANSLATIONS


class FileSelectionHandler:
    """Handles file selection events"""

    def __init__(
        self,
        window,
        spreadsheet_label,
        tnc_label,
        xtl_label,
        company_name_field,
        java_package_field,
        author_field,
        update_button_state_callback: Callable[[], None],
    ):
        self.window = window
        self.spreadsheet_label = spreadsheet_label
        self.tnc_label = tnc_label
        self.xtl_label = xtl_label
        self.company_name_field = company_name_field
        self.java_package_field = java_package_field
        self.author_field = author_field
        self.update_button_state = update_button_state_callback

    def select_spreadsheet(self, current_language: str) -> Optional[Path]:
        """Handle spreadsheet file selection"""
        t = TRANSLATIONS[current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            t["select_spreadsheet"],
            "",
            "Excel Files (*.xls *.xlsx)",
        )
        if file_path:
            path = Path(file_path)
            self.spreadsheet_label.setText(path.name)
            self.update_button_state()
            return path
        return None

    def select_tnc_platform(self, current_language: str) -> Optional[Path]:
        """Handle T&C Platform file selection"""
        t = TRANSLATIONS[current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            t["select_tnc"],
            "",
            "Web Files (*.mhtml *.html *.htm)",
        )
        if file_path:
            path = Path(file_path)
            self.tnc_label.setText(path.name)
            return path
        else:
            self.tnc_label.setText(t["not_selected"])
            return None

    def select_xtl(self, current_language: str) -> Optional[Path]:
        """Handle XTL file selection"""
        t = TRANSLATIONS[current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            t["select_xtl"],
            "",
            "XTL Files (*.xtl)",
        )
        if file_path:
            path = Path(file_path)
            self.xtl_label.setText(path.name)
            self.parse_xtl_file(path, current_language)
            return path
        else:
            self.xtl_label.setText(t["not_selected"])
            return None

    def parse_xtl_file(self, file_path: Path, current_language: str) -> None:
        """Parse .xtl file and fill fields from DOCUMENTDEF attributes"""
        t = TRANSLATIONS[current_language]
        try:
            parsed_data = XTLParser.parse(file_path)

            if parsed_data["owner"]:
                self.company_name_field.setText(parsed_data["owner"])
            if parsed_data["javaPackageName"]:
                self.java_package_field.setText(parsed_data["javaPackageName"])
            if parsed_data["lastModifiedBy"]:
                self.author_field.setText(parsed_data["lastModifiedBy"])
        except Exception as exc:
            QMessageBox.warning(
                self.window,
                t["error"],
                f"{t['read_xtl_error']}:\n{exc}",
            )


class DataProcessingHandler:
    """Handles data processing events"""

    def __init__(
        self,
        window,
        base_path: Path,
        get_fields_callback: Callable[[], tuple[str, str, str]],
    ):
        self.window = window
        self.base_path = base_path
        self.get_fields = get_fields_callback

    def process_data(
        self,
        spreadsheet_path: Optional[Path],
        current_language: str,
    ) -> None:
        """Process data and save result to output folder"""
        t = TRANSLATIONS[current_language]

        # Validate required fields
        if not spreadsheet_path:
            QMessageBox.warning(self.window, t["error"], t["select_spreadsheet_file"])
            return

        company_name, java_package, author = self.get_fields()

        if not all([company_name, java_package, author]):
            QMessageBox.warning(self.window, t["error"], t["fill_all_fields"])
            return

        # Create output directory
        output_dir = self.base_path / "output"

        # Clear output directory
        error = OutputFileWriter.clear_output_directory(output_dir)
        if error:
            QMessageBox.warning(
                self.window,
                t["warning"],
                f"{t['delete_files_warning']}:\n{error}",
            )

        # Write output file
        error = OutputFileWriter.write_output_file(
            output_dir, company_name, java_package, author
        )
        if error:
            QMessageBox.critical(
                self.window,
                t["error"],
                f"{t['save_error']}:\n{error}",
            )
        else:
            output_file = output_dir / "output.txt"
            QMessageBox.information(
                self.window,
                t["success"],
                f"{t['data_saved']}:\n{output_file}",
            )


class AutoFillHandler:
    """Handles auto-fill from input directory"""

    @staticmethod
    def find_files_in_input(input_dir: Path) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
        """Find files in input directory"""
        return InputFileFinder.find_files(input_dir)

