"""Main window module for the application"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from application.config import ConfigManager
from application.database import Database
from application.editor import ItemPropertiesEditor
from application.file_handlers import InputFileFinder, OutputFileWriter, XTLParser
from application.translations import TRANSLATIONS


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, base_path: Path) -> None:
        """
        Initialize MainWindow

        Args:
            base_path: Base path of the application
        """
        super().__init__()
        self.base_path = base_path
        self.setWindowTitle("TNC Map Helper")
        self.setMinimumWidth(600)

        # File paths
        self.spreadsheet_path: Optional[Path] = None
        self.tnc_platform_path: Optional[Path] = None
        self.csv_archive_path: Optional[Path] = None
        self.xtl_path: Optional[Path] = None

        # Configuration manager (config is now in application folder)
        config_dir = Path(__file__).parent / ".config"
        self.config_manager = ConfigManager(config_dir)

        # Database (in application folder)
        db_path = Path(__file__).parent / "database.db"
        self.database = Database(db_path)

        # Current language
        self.current_language = self.config_manager.get_language()

        # UI elements dictionary for translation
        self.ui_elements = {}

        # Create UI
        self.create_ui()

        # Load saved language
        self.load_language()
        self.update_ui_texts()

        # Load last author first (has priority over .xtl file)
        self.load_last_author()

        # Auto-fill from input folder
        self.auto_fill_from_input()

        # Update process button state
        self.update_process_button_state()

    def create_ui(self) -> None:
        """Create user interface"""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Language selection and Edit Items button at the top
        top_layout = QHBoxLayout()
        language_layout = QHBoxLayout()
        language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["UA", "EN"])
        self.language_combo.currentTextChanged.connect(self.change_language)  # type: ignore[arg-type]
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        
        top_layout.addLayout(language_layout)
        top_layout.addStretch()
        
        # Edit Items button
        self.edit_items_button = QPushButton("Edit Items Properties")
        self.ui_elements["edit_items_button"] = self.edit_items_button
        self.edit_items_button.clicked.connect(self.open_items_editor)  # type: ignore[arg-type]
        top_layout.addWidget(self.edit_items_button)
        
        layout.addLayout(top_layout)

        # Spreadsheet field (required)
        spreadsheet_group = QGroupBox("Spreadsheet *")
        self.ui_elements["spreadsheet_group"] = spreadsheet_group
        spreadsheet_layout = QHBoxLayout()
        self.spreadsheet_label = QLabel("Not selected")
        # Enable HTML formatting for labels
        self.spreadsheet_label.setTextFormat(Qt.TextFormat.RichText)
        self.spreadsheet_button = QPushButton("Select file")
        self.ui_elements["spreadsheet_button"] = self.spreadsheet_button
        self.spreadsheet_button.clicked.connect(self.select_spreadsheet)  # type: ignore[arg-type]
        spreadsheet_layout.addWidget(self.spreadsheet_label)
        spreadsheet_layout.addWidget(self.spreadsheet_button)
        spreadsheet_group.setLayout(spreadsheet_layout)
        layout.addWidget(spreadsheet_group)

        # T&C Platform page field (required)
        tnc_group = QGroupBox("TnC Platform page")
        self.ui_elements["tnc_group"] = tnc_group
        tnc_layout = QHBoxLayout()
        self.tnc_label = QLabel("Not selected")
        self.tnc_label.setTextFormat(Qt.TextFormat.RichText)
        self.tnc_button = QPushButton("Select file")
        self.ui_elements["tnc_button"] = self.tnc_button
        self.tnc_button.clicked.connect(self.select_tnc_platform)  # type: ignore[arg-type]
        tnc_layout.addWidget(self.tnc_label)
        tnc_layout.addWidget(self.tnc_button)
        tnc_group.setLayout(tnc_layout)
        layout.addWidget(tnc_group)

        # CSV Archive field (required)
        csv_archive_group = QGroupBox("CSV Archive")
        self.ui_elements["csv_archive_group"] = csv_archive_group
        csv_archive_layout = QHBoxLayout()
        self.csv_archive_label = QLabel("Not selected")
        self.csv_archive_label.setTextFormat(Qt.TextFormat.RichText)
        self.csv_archive_button = QPushButton("Select file")
        self.ui_elements["csv_archive_button"] = self.csv_archive_button
        self.csv_archive_button.clicked.connect(self.select_csv_archive)  # type: ignore[arg-type]
        csv_archive_layout.addWidget(self.csv_archive_label)
        csv_archive_layout.addWidget(self.csv_archive_button)
        csv_archive_group.setLayout(csv_archive_layout)
        layout.addWidget(csv_archive_group)

        # Combined block: poRsxRead.xtl properties (only text fields)
        combined_group = QGroupBox("poRsxRead.xtl Properties")
        self.ui_elements["xtl_group"] = combined_group
        combined_layout = QVBoxLayout()

        # Three required fields with same width
        # Company Name
        company_layout = QHBoxLayout()
        company_label = QLabel("Company Name:")
        self.ui_elements["company_label"] = company_label
        company_label.setMinimumWidth(150)
        self.company_name_field = QLineEdit()
        self.company_name_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        company_layout.addWidget(company_label)
        company_layout.addWidget(self.company_name_field)
        combined_layout.addLayout(company_layout)

        # Java Package Name
        package_layout = QHBoxLayout()
        package_label = QLabel("Java Package Name:")
        self.ui_elements["package_label"] = package_label
        package_label.setMinimumWidth(150)
        self.java_package_field = QLineEdit()
        self.java_package_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        package_layout.addWidget(package_label)
        package_layout.addWidget(self.java_package_field)
        combined_layout.addLayout(package_layout)

        # Author
        author_layout = QHBoxLayout()
        author_label = QLabel("Author:")
        self.ui_elements["author_label"] = author_label
        author_label.setMinimumWidth(150)
        self.author_field = QLineEdit()
        self.author_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        self.author_field.editingFinished.connect(self.save_last_author)  # type: ignore[arg-type]
        author_layout.addWidget(author_label)
        author_layout.addWidget(self.author_field)
        combined_layout.addLayout(author_layout)

        # Set same minimum width for all text fields
        min_field_width = 300
        self.company_name_field.setMinimumWidth(min_field_width)
        self.java_package_field.setMinimumWidth(min_field_width)
        self.author_field.setMinimumWidth(min_field_width)

        combined_group.setLayout(combined_layout)
        layout.addWidget(combined_group)

        # Process Data button
        self.process_button = QPushButton("Process Data")
        self.ui_elements["process_button"] = self.process_button
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_data)  # type: ignore[arg-type]
        layout.addWidget(self.process_button)

        layout.addStretch()
        self.setCentralWidget(container)

        # Styling: bold font for QGroupBox titles
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
            }
        """)

    def select_spreadsheet(self) -> None:
        """Handle spreadsheet file selection"""
        t = TRANSLATIONS[self.current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t["select_spreadsheet"],
            "",
            "Excel Files (*.xls *.xlsx)",
        )
        if file_path:
            self.spreadsheet_path = Path(file_path)
            self.spreadsheet_label.setText(self.spreadsheet_path.name)
            self.update_process_button_state()
        else:
            self.spreadsheet_path = None
            self._set_not_selected_label(self.spreadsheet_label, is_required=True)
            self.update_process_button_state()

    def select_tnc_platform(self) -> None:
        """Handle T&C Platform file selection"""
        t = TRANSLATIONS[self.current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t["select_tnc"],
            "",
            "Web Files (*.mhtml *.html *.htm)",
        )
        if file_path:
            self.tnc_platform_path = Path(file_path)
            self.tnc_label.setText(self.tnc_platform_path.name)
            self.update_process_button_state()
        else:
            self.tnc_platform_path = None
            self._set_not_selected_label(self.tnc_label, is_required=True)
            self.update_process_button_state()

    def select_csv_archive(self) -> None:
        """Handle CSV Archive file selection"""
        t = TRANSLATIONS[self.current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t["select_csv_archive"],
            "",
            "ZIP Files (*.zip)",
        )
        if file_path:
            self.csv_archive_path = Path(file_path)
            self.csv_archive_label.setText(self.csv_archive_path.name)
            self.update_process_button_state()
        else:
            self.csv_archive_path = None
            self._set_not_selected_label(self.csv_archive_label, is_required=True)
            self.update_process_button_state()

    def parse_xtl_file(self, file_path: Path, preserve_author: bool = True) -> None:
        """
        Parse .xtl file and fill fields from DOCUMENTDEF attributes
        
        Args:
            file_path: Path to .xtl file
            preserve_author: If True, don't overwrite author if it's already set
        """
        t = TRANSLATIONS[self.current_language]
        try:
            parsed_data = XTLParser.parse(file_path)

            if parsed_data["owner"]:
                self.company_name_field.setText(parsed_data["owner"])
            if parsed_data["javaPackageName"]:
                self.java_package_field.setText(parsed_data["javaPackageName"])
            if parsed_data["lastModifiedBy"]:
                # Only set author if field is empty or preserve_author is False
                if not preserve_author or not self.author_field.text().strip():
                    self.author_field.setText(parsed_data["lastModifiedBy"])
        except Exception as exc:
            QMessageBox.warning(
                self,
                t["error"],
                f"{t['read_xtl_error']}:\n{exc}",
            )

    def auto_fill_from_input(self) -> None:
        """Auto-fill fields from input folder if there is one matching file"""
        input_dir = self.base_path / "input"
        spreadsheet_path, tnc_platform_path, csv_archive_path, xtl_path = InputFileFinder.find_files(input_dir)

        if spreadsheet_path:
            self.spreadsheet_path = spreadsheet_path
            self.spreadsheet_label.setText(self.spreadsheet_path.name)

        if tnc_platform_path:
            self.tnc_platform_path = tnc_platform_path
            self.tnc_label.setText(self.tnc_platform_path.name)

        if csv_archive_path:
            self.csv_archive_path = csv_archive_path
            self.csv_archive_label.setText(self.csv_archive_path.name)

        # Auto-fill from .xtl file if found (optional)
        if xtl_path:
            self.xtl_path = xtl_path
            self.parse_xtl_file(xtl_path)

        # Update "Not selected" text for unselected fields
        if self.spreadsheet_path is None:
            self._set_not_selected_label(self.spreadsheet_label, is_required=True)
        else:
            self.spreadsheet_label.setText(self.spreadsheet_path.name)

        if self.tnc_platform_path is None:
            self._set_not_selected_label(self.tnc_label, is_required=True)
        else:
            self.tnc_label.setText(self.tnc_platform_path.name)

        if self.csv_archive_path is None:
            self._set_not_selected_label(self.csv_archive_label, is_required=True)
        else:
            self.csv_archive_label.setText(self.csv_archive_path.name)

        self.update_process_button_state()

    def update_process_button_state(self) -> None:
        """Update Process Data button state"""
        has_spreadsheet = self.spreadsheet_path is not None
        has_tnc_platform = self.tnc_platform_path is not None
        has_csv_archive = self.csv_archive_path is not None
        has_company_name = bool(self.company_name_field.text().strip())
        has_java_package = bool(self.java_package_field.text().strip())
        has_author = bool(self.author_field.text().strip())

        self.process_button.setEnabled(
            has_spreadsheet
            and has_tnc_platform
            and has_csv_archive
            and has_company_name
            and has_java_package
            and has_author
        )

    def load_last_author(self) -> None:
        """Load last author value from configuration"""
        author = self.config_manager.get_last_author()
        if author:
            self.author_field.setText(author)

    def save_last_author(self) -> None:
        """Save last author value to configuration"""
        author = self.author_field.text().strip()
        self.config_manager.save_last_author(author)

    def process_data(self) -> None:
        """Process data and save result to output folder"""
        t = TRANSLATIONS[self.current_language]

        # Validate required fields
        if not self.spreadsheet_path:
            QMessageBox.warning(self, t["error"], t["select_spreadsheet_file"])
            return

        if not self.tnc_platform_path:
            QMessageBox.warning(self, t["error"], t["select_tnc_file"])
            return

        if not self.csv_archive_path:
            QMessageBox.warning(self, t["error"], t["select_csv_archive_file"])
            return

        company_name = self.company_name_field.text().strip()
        java_package = self.java_package_field.text().strip()
        author = self.author_field.text().strip()

        if not all([company_name, java_package, author]):
            QMessageBox.warning(self, t["error"], t["fill_all_fields"])
            return

        # Create output directory
        output_dir = self.base_path / "output"

        # Clear output directory
        error = OutputFileWriter.clear_output_directory(output_dir)
        if error:
            QMessageBox.warning(
                self,
                t["warning"],
                f"{t['delete_files_warning']}:\n{error}",
            )

        # Write output file
        error = OutputFileWriter.write_output_file(output_dir, company_name, java_package, author)
        if error:
            QMessageBox.critical(
                self,
                t["error"],
                f"{t['save_error']}:\n{error}",
            )
        else:
            output_file = output_dir / "output.txt"
            QMessageBox.information(
                self,
                t["success"],
                f"{t['data_saved']}:\n{output_file}",
            )

    def change_language(self, language: str) -> None:
        """Change interface language"""
        if language != self.current_language:
            self.current_language = language
            self.update_ui_texts()
            self.config_manager.save_language(language)

    def load_language(self) -> None:
        """Load last selected language from configuration"""
        language = self.config_manager.get_language()
        if language in ["UA", "EN"]:
            self.current_language = language
            # Temporarily disable signal to avoid double call
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentText(language)
            self.language_combo.blockSignals(False)

    def _set_not_selected_label(self, label: QLabel, is_required: bool) -> None:
        """Set 'Not selected' text with red color for required fields"""
        t = TRANSLATIONS[self.current_language]
        if is_required:
            label.setText(f'<span style="color: red;">{t["not_selected"]}</span>')
        else:
            label.setText(t["not_selected"])

    def update_ui_texts(self) -> None:
        """Update all interface texts according to selected language"""
        t = TRANSLATIONS[self.current_language]

        # Window title
        self.setWindowTitle(t["window_title"])

        # Group titles
        self.ui_elements["spreadsheet_group"].setTitle(t["spreadsheet"])
        self.ui_elements["tnc_group"].setTitle(t["tnc_platform"])
        self.ui_elements["csv_archive_group"].setTitle(t["csv_archive"])
        self.ui_elements["xtl_group"].setTitle(t["xtl"])

        # Buttons
        self.ui_elements["spreadsheet_button"].setText(t["select_file"])
        self.ui_elements["tnc_button"].setText(t["select_file"])
        self.ui_elements["csv_archive_button"].setText(t["select_file"])
        self.ui_elements["edit_items_button"].setText(t["edit_items"])
        self.ui_elements["process_button"].setText(t["process_data"])

        # Labels
        self.ui_elements["company_label"].setText(t["company_name"])
        self.ui_elements["package_label"].setText(t["java_package"])
        self.ui_elements["author_label"].setText(t["author"])

        # Update "Not selected" text for unselected fields
        # Required fields: red color
        if self.spreadsheet_path is None:
            self._set_not_selected_label(self.spreadsheet_label, is_required=True)
        else:
            self.spreadsheet_label.setText(self.spreadsheet_path.name)

        if self.tnc_platform_path is None:
            self._set_not_selected_label(self.tnc_label, is_required=True)
        else:
            self.tnc_label.setText(self.tnc_platform_path.name)

        if self.csv_archive_path is None:
            self._set_not_selected_label(self.csv_archive_label, is_required=True)
        else:
            self.csv_archive_label.setText(self.csv_archive_path.name)

    def open_items_editor(self) -> None:
        """Open Items Properties Editor"""
        editor = ItemPropertiesEditor(self.database, self.current_language, self)
        editor.exec()

