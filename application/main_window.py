"""Main window module for the application"""

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from application.config import ConfigManager
from application.csv_parser import CSVArchiveParser
from application.database import Database
from application.editor import ItemPropertiesEditor
from application.items_dialog import ItemsInfoDialog
from application.file_handlers import InputFileFinder, OutputFileWriter, XTLParser
from application.scenarios_dialog import ScenariosInfoDialog
from application.spreadsheet_parser import Item, SpreadsheetParser
from application.tnc_parser import InboundDocScenario, TOMMMParser
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
        
        # Set window icon
        self._set_window_icon()

        # File paths
        self.spreadsheet_path: Optional[Path] = None
        self.tnc_platform_path: Optional[Path] = None
        self.csv_archive_path: Optional[Path] = None
        self.xtl_path: Optional[Path] = None
        
        # Parsed items list
        self.parsed_items: List[Item] = []
        self.spreadsheet_parse_success: Optional[bool] = None
        self.spreadsheet_parse_error: Optional[str] = None
        
        # Parsed TOMMM scenarios
        self.parsed_scenarios: List[InboundDocScenario] = []
        self.tnc_parse_success: Optional[bool] = None
        self.tnc_parse_error: Optional[str] = None
        self.tnc_company_name: Optional[str] = None
        
        # CSV Archive parsing status
        self.csv_archive_parse_success: Optional[bool] = None
        self.csv_archive_parse_error: Optional[str] = None

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

        # Clear Java Package Name field on startup (after auto-fill to ensure it's always empty)
        self.java_package_field.clear()
        
        # Update Java Package Name label style (should be red and bold since field is empty)
        self._update_java_package_label_style()

        # Update process button state
        self.update_process_button_state()

    def _refresh_all_parsing(self) -> None:
        """Refresh parsing for all three input blocks if files are selected."""
        if self.spreadsheet_path:
            self._refresh_spreadsheet_parsing()
        if self.tnc_platform_path:
            self._refresh_tnc_parsing()
        if self.csv_archive_path:
            self._refresh_csv_archive_parsing()

    def create_ui(self) -> None:
        """Create user interface"""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Language selection, global refresh and Edit Items button at the top
        top_layout = QHBoxLayout()

        # Language selector on the left
        language_layout = QHBoxLayout()
        language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["UA", "EN"])
        self.language_combo.currentTextChanged.connect(self.change_language)  # type: ignore[arg-type]
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        top_layout.addLayout(language_layout)

        # Global refresh parsing button in the center
        t = TRANSLATIONS[self.current_language]
        self.global_refresh_button = QPushButton(f"↻ {t.get('refresh_parsing', 'Refresh parsing')}")
        self.global_refresh_button.setFixedWidth(180)
        self.global_refresh_button.setFixedHeight(28)
        self.global_refresh_button.clicked.connect(self._refresh_all_parsing)  # type: ignore[arg-type]
        self.global_refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        top_layout.addStretch()
        top_layout.addWidget(self.global_refresh_button)
        top_layout.addStretch()

        # Edit Items button on the right
        self.edit_items_button = QPushButton(t.get("edit_items", "Edit Items Properties"))
        self.edit_items_button.setFixedWidth(260)
        self.edit_items_button.setFixedHeight(28)
        self.ui_elements["edit_items_button"] = self.edit_items_button
        self.edit_items_button.clicked.connect(self.open_items_editor)  # type: ignore[arg-type]
        top_layout.addWidget(self.edit_items_button)
        
        layout.addLayout(top_layout)

        # Spreadsheet field (required)
        spreadsheet_group = QGroupBox("Spreadsheet *")
        self.ui_elements["spreadsheet_group"] = spreadsheet_group
        spreadsheet_group.setMinimumHeight(60)
        spreadsheet_layout = QHBoxLayout()
        spreadsheet_layout.setContentsMargins(8, 4, 8, 4)
        spreadsheet_layout.setSpacing(8)
        
        # Status button (clickable, shows parsing success/failure)
        self.spreadsheet_status_button = QPushButton()
        self.spreadsheet_status_button.setFixedWidth(35)
        self.spreadsheet_status_button.setFixedHeight(28)
        self.spreadsheet_status_button.clicked.connect(self._show_spreadsheet_parse_status)  # type: ignore[arg-type]
        self.spreadsheet_status_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.spreadsheet_status_button.hide()
        
        self.spreadsheet_label = QLabel("Not selected")
        # Enable HTML formatting for labels
        self.spreadsheet_label.setTextFormat(Qt.TextFormat.RichText)
        self.spreadsheet_label.setFixedHeight(24)
        self.spreadsheet_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.spreadsheet_button = QPushButton("Select file")
        self.spreadsheet_button.setFixedWidth(110)
        self.spreadsheet_button.setFixedHeight(28)
        self.ui_elements["spreadsheet_button"] = self.spreadsheet_button
        self.spreadsheet_button.clicked.connect(self.select_spreadsheet)  # type: ignore[arg-type]
        spreadsheet_layout.addWidget(self.spreadsheet_status_button)
        spreadsheet_layout.addWidget(self.spreadsheet_label)
        spreadsheet_layout.addWidget(self.spreadsheet_button)
        spreadsheet_group.setLayout(spreadsheet_layout)
        layout.addWidget(spreadsheet_group)

        # T&C Platform page field (required)
        tnc_group = QGroupBox("TnC Platform page")
        self.ui_elements["tnc_group"] = tnc_group
        tnc_group.setMinimumHeight(60)
        tnc_layout = QHBoxLayout()
        tnc_layout.setContentsMargins(8, 4, 8, 4)
        tnc_layout.setSpacing(8)
        
        # Status button for TOMMM parsing
        self.tnc_status_button = QPushButton()
        self.tnc_status_button.setFixedWidth(35)
        self.tnc_status_button.setFixedHeight(28)
        self.tnc_status_button.clicked.connect(self._show_tnc_parse_status)  # type: ignore[arg-type]
        self.tnc_status_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tnc_status_button.hide()
        
        self.tnc_label = QLabel("Not selected")
        self.tnc_label.setTextFormat(Qt.TextFormat.RichText)
        self.tnc_label.setFixedHeight(24)
        self.tnc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.tnc_button = QPushButton("Select file")
        self.tnc_button.setFixedWidth(110)
        self.tnc_button.setFixedHeight(28)
        self.ui_elements["tnc_button"] = self.tnc_button
        self.tnc_button.clicked.connect(self.select_tnc_platform)  # type: ignore[arg-type]
        tnc_layout.addWidget(self.tnc_status_button)
        tnc_layout.addWidget(self.tnc_label)
        tnc_layout.addWidget(self.tnc_button)
        tnc_group.setLayout(tnc_layout)
        layout.addWidget(tnc_group)

        # CSV Archive field (required)
        csv_archive_group = QGroupBox("CSV Archive")
        self.ui_elements["csv_archive_group"] = csv_archive_group
        csv_archive_group.setMinimumHeight(60)
        csv_archive_layout = QHBoxLayout()
        csv_archive_layout.setContentsMargins(8, 4, 8, 4)
        csv_archive_layout.setSpacing(8)
        
        # Status button for CSV archive parsing
        self.csv_archive_status_button = QPushButton()
        self.csv_archive_status_button.setFixedWidth(35)
        self.csv_archive_status_button.setFixedHeight(28)
        self.csv_archive_status_button.clicked.connect(self._show_csv_archive_parse_status)  # type: ignore[arg-type]
        self.csv_archive_status_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.csv_archive_status_button.hide()
        
        self.csv_archive_label = QLabel("Not selected")
        self.csv_archive_label.setTextFormat(Qt.TextFormat.RichText)
        self.csv_archive_label.setFixedHeight(24)
        self.csv_archive_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.csv_archive_button = QPushButton("Select file")
        self.csv_archive_button.setFixedWidth(110)
        self.csv_archive_button.setFixedHeight(28)
        self.ui_elements["csv_archive_button"] = self.csv_archive_button
        self.csv_archive_button.clicked.connect(self.select_csv_archive)  # type: ignore[arg-type]
        csv_archive_layout.addWidget(self.csv_archive_status_button)
        csv_archive_layout.addWidget(self.csv_archive_label)
        csv_archive_layout.addWidget(self.csv_archive_button)
        csv_archive_group.setLayout(csv_archive_layout)
        layout.addWidget(csv_archive_group)
        
        # Buttons to show parsed data (always visible, styled, left-aligned)
        t = TRANSLATIONS[self.current_language]

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Button to show Item information
        self.show_items_button = QPushButton(t.get("show_items_info", "Показати властивості TLI полів"))
        self.show_items_button.clicked.connect(self._show_items_info)  # type: ignore[arg-type]
        self.show_items_button.setFixedWidth(320)
        self.show_items_button.setStyleSheet(
            "QPushButton {"
            "  text-align: left;"
            "  font-weight: bold;"
            "  background-color: #e0e0e0;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #f0f0f0;"
            "}"
        )
        buttons_layout.addWidget(self.show_items_button)

        # Button to show scenario information
        self.show_scenarios_button = QPushButton(t.get("show_scenarios_info", "Показати інформацію сценаріїв"))
        self.show_scenarios_button.clicked.connect(self._show_scenarios_info)  # type: ignore[arg-type]
        self.show_scenarios_button.setFixedWidth(320)
        self.show_scenarios_button.setStyleSheet(
            "QPushButton {"
            "  text-align: left;"
            "  font-weight: bold;"
            "  background-color: #e0e0e0;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #f0f0f0;"
            "}"
        )
        buttons_layout.addWidget(self.show_scenarios_button)

        layout.addLayout(buttons_layout)

        # Combined block: poRsxRead.xtl properties (only text fields)
        combined_group = QGroupBox("poRsxRead.xtl Properties")
        self.ui_elements["xtl_group"] = combined_group
        combined_layout = QVBoxLayout()

        # Three required fields with same width
        labels_min_width = 190
        spacing_between_label_and_field = 10  # ~5 mm on typical DPI

        # Company Name
        company_layout = QHBoxLayout()
        company_label = QLabel("Company Name:")
        self.ui_elements["company_label"] = company_label
        company_label.setMinimumWidth(labels_min_width)
        self.company_name_field = QLineEdit()
        self.company_name_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        company_layout.addWidget(company_label)
        company_layout.addSpacing(spacing_between_label_and_field)
        company_layout.addWidget(self.company_name_field)
        combined_layout.addLayout(company_layout)

        # Java Package Name
        package_layout = QHBoxLayout()
        package_label = QLabel("Java Package Name:")
        self.ui_elements["package_label"] = package_label
        package_label.setMinimumWidth(labels_min_width)
        self.java_package_field = QLineEdit()
        # Placeholder will be set in update_ui_texts() based on current language
        self.java_package_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        self.java_package_field.textChanged.connect(self._update_java_package_label_style)  # type: ignore[arg-type]
        package_layout.addWidget(package_label)
        package_layout.addSpacing(spacing_between_label_and_field)
        package_layout.addWidget(self.java_package_field)
        combined_layout.addLayout(package_layout)

        # Author
        author_layout = QHBoxLayout()
        author_label = QLabel("Author:")
        self.ui_elements["author_label"] = author_label
        author_label.setMinimumWidth(labels_min_width)
        self.author_field = QLineEdit()
        self.author_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        self.author_field.editingFinished.connect(self.save_last_author)  # type: ignore[arg-type]
        author_layout.addWidget(author_label)
        author_layout.addSpacing(spacing_between_label_and_field)
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
            # Parse spreadsheet automatically
            self._parse_spreadsheet()
            # Enable Items info button when there are parsed items
            self.show_items_button.setEnabled(bool(self.parsed_items))
            self.update_process_button_state()
        else:
            self.spreadsheet_path = None
            self._set_not_selected_label(self.spreadsheet_label, is_required=True)
            self.spreadsheet_status_button.hide()
            self.parsed_items = []
            self.spreadsheet_parse_success = None
            self.spreadsheet_parse_error = None
            self.show_items_button.setEnabled(False)
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
            # Parse TOMMM file automatically
            self._parse_tnc_file()
            # Enable scenarios button when scenarios are parsed successfully
            self.show_scenarios_button.setEnabled(bool(self.parsed_scenarios))
            self.update_process_button_state()
        else:
            self.tnc_platform_path = None
            self._set_not_selected_label(self.tnc_label, is_required=True)
            self.tnc_status_button.hide()
            self.parsed_scenarios = []
            self.tnc_parse_success = None
            self.tnc_parse_error = None
            self.tnc_company_name = None
            self.show_scenarios_button.setEnabled(False)
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
            # Parse CSV archive automatically
            self._parse_csv_archive()
            self.update_process_button_state()
        else:
            self.csv_archive_path = None
            self._set_not_selected_label(self.csv_archive_label, is_required=True)
            self.csv_archive_parse_success = None
            self.csv_archive_parse_error = None
            self._update_csv_archive_status_icon()
            # Do not hide scenarios button; its enabled state is controlled
            # by whether TOMMM scenarios are parsed
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
            # Java Package Name is not filled from .xtl file - it should always be empty on startup
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
            # Parse spreadsheet automatically
            self._parse_spreadsheet()
            if self.parsed_items:
                self.show_items_button.show()
                self.show_items_button.setEnabled(True)

        if tnc_platform_path:
            self.tnc_platform_path = tnc_platform_path
            self.tnc_label.setText(self.tnc_platform_path.name)

        if csv_archive_path:
            self.csv_archive_path = csv_archive_path
            self.csv_archive_label.setText(self.csv_archive_path.name)
            # Parse CSV archive automatically if TNC is already parsed
            # If TNC is not parsed yet, it will be parsed after TNC parsing
            if self.parsed_scenarios:
                self._parse_csv_archive()
            else:
                # Even if TNC is not parsed, show buttons with error state
                self.csv_archive_parse_success = False
                self.csv_archive_parse_error = TRANSLATIONS[self.current_language].get(
                    "csv_no_scenarios", 
                    "Please parse TOMMM file first"
                )
                self._update_csv_archive_status_icon()

        # Auto-fill from .xtl file if found (optional)
        if xtl_path:
            self.xtl_path = xtl_path
            self.parse_xtl_file(xtl_path)

        # Update "Not selected" text for unselected fields
        if self.spreadsheet_path is None:
            self._set_not_selected_label(self.spreadsheet_label, is_required=True)
        else:
            self.spreadsheet_label.setText(self.spreadsheet_path.name)
            # Ensure Items button is visible when items exist
            if self.parsed_items:
                self.show_items_button.show()
                self.show_items_button.setEnabled(True)

        if self.tnc_platform_path is None:
            self._set_not_selected_label(self.tnc_label, is_required=True)
        else:
            self.tnc_label.setText(self.tnc_platform_path.name)
            # Parse TOMMM file automatically
            self._parse_tnc_file()
            # If CSV archive is already selected, parse it after TNC parsing
            if self.csv_archive_path:
                self._parse_csv_archive()

        if self.csv_archive_path is None:
            self._set_not_selected_label(self.csv_archive_label, is_required=True)
        else:
            self.csv_archive_label.setText(self.csv_archive_path.name)

        self.update_process_button_state()

    def _update_java_package_label_style(self) -> None:
        """Update Java Package Name label style based on field content"""
        package_label = self.ui_elements["package_label"]
        has_text = bool(self.java_package_field.text().strip())
        
        if has_text:
            # Normal style when field has text
            package_label.setStyleSheet("color: black;")
            font = package_label.font()
            font.setBold(False)
            package_label.setFont(font)
        else:
            # Red and bold when field is empty
            package_label.setStyleSheet("color: red;")
            font = package_label.font()
            font.setBold(True)
            package_label.setFont(font)
    
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
        error = OutputFileWriter.write_output_file(output_dir, company_name, java_package, author, self.parsed_scenarios)
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
            
            # Re-parse spreadsheet with new language to update error messages
            if self.spreadsheet_path:
                self._parse_spreadsheet()
            
            # Re-parse TOMMM with new language to update error messages
            # Save CSV archive parse status before re-parsing TOMMM
            csv_archive_was_parsed = self.csv_archive_parse_success is True
            csv_archive_path_saved = self.csv_archive_path
            
            if self.tnc_platform_path:
                self._parse_tnc_file()
            
            # Re-parse CSV archive if it was successfully parsed before
            # This preserves CSV data that was added to scenarios
            if csv_archive_was_parsed and csv_archive_path_saved and self.parsed_scenarios:
                self._parse_csv_archive()

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
        self.global_refresh_button.setText(f"↻ {t.get('refresh_parsing', 'Refresh parsing')}")
        self.ui_elements["process_button"].setText(t["process_data"])

        # Parsed data buttons
        self.show_items_button.setText(t.get("show_items_info", "Show data from inbound items"))
        self.show_scenarios_button.setText(t.get("show_scenarios_info", "Show Scenarios Information"))

        # Labels
        self.ui_elements["company_label"].setText(t["company_name"])
        self.ui_elements["package_label"].setText(t["java_package"])
        self.ui_elements["author_label"].setText(t["author"])
        
        # Update Java Package Name placeholder
        self.java_package_field.setPlaceholderText(t["java_package_placeholder"])
        
        # Update Java Package Name label style (preserve style based on field content)
        self._update_java_package_label_style()

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

    def _parse_spreadsheet(self) -> None:
        """Parse selected spreadsheet file"""
        if not self.spreadsheet_path:
            return
        
        parser = SpreadsheetParser(self.database, self.current_language)
        items, success, error_message = parser.parse(self.spreadsheet_path)
        
        self.parsed_items = items
        self.spreadsheet_parse_success = success
        self.spreadsheet_parse_error = error_message
        
        # Update status icon
        self._update_spreadsheet_status_icon()
        # Enable Items button only when parsing is successful and items exist
        self.show_items_button.setEnabled(bool(self.parsed_items) and bool(self.spreadsheet_parse_success))
    
    def _update_spreadsheet_status_icon(self) -> None:
        """Update spreadsheet parsing status button"""
        t = TRANSLATIONS[self.current_language]
        
        if self.spreadsheet_parse_success is None:
            self.spreadsheet_status_button.hide()
            return
        
        self.spreadsheet_status_button.show()
        
        if self.spreadsheet_parse_success:
            # Subtle green button with checkmark (success)
            self.spreadsheet_status_button.setText("✓")
            self.spreadsheet_status_button.setToolTip(t["tooltip_parse_success"])
            self.spreadsheet_status_button.setStyleSheet(
                "QPushButton {"
                "  background-color: #e8f5e9; "
                "  color: #2e7d32; "
                "  font-weight: bold; "
                "  font-size: 16px; "
                "  border: none; "
                "  border-radius: 3px; "
                "  padding: 2px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #c8e6c9; "
                "}"
                "QPushButton:pressed {"
                "  background-color: #a5d6a7; "
                "}"
            )
        else:
            # Subtle red button with X (error)
            self.spreadsheet_status_button.setText("✗")
            self.spreadsheet_status_button.setToolTip(t["tooltip_parse_error"])
            self.spreadsheet_status_button.setStyleSheet(
                "QPushButton {"
                "  background-color: #ffebee; "
                "  color: #c62828; "
                "  font-weight: bold; "
                "  font-size: 16px; "
                "  border: none; "
                "  border-radius: 3px; "
                "  padding: 2px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #ffcdd2; "
                "}"
                "QPushButton:pressed {"
                "  background-color: #ef9a9a; "
                "}"
            )
    
    def _show_spreadsheet_parse_status(self) -> None:
        """Show spreadsheet parsing status message"""
        t = TRANSLATIONS[self.current_language]
        
        if self.spreadsheet_parse_success is None:
            return
        
        if self.spreadsheet_parse_success:
            QMessageBox.information(
                self,
                t.get("parsing_status", "Статус парсингу"),
                t.get("spreadsheet_parse_success", "Парсинг Spreadsheet завершено успішно")
            )
        else:
            error_msg = self.spreadsheet_parse_error or t.get("spreadsheet_parse_error", "Помилка парсингу")
            QMessageBox.warning(
                self,
                t.get("parsing_status", "Статус парсингу"),
                error_msg
            )
    
    def _refresh_spreadsheet_parsing(self) -> None:
        """Refresh spreadsheet parsing data"""
        if self.spreadsheet_path:
            self._parse_spreadsheet()
            # If CSV archive and TNC were parsed successfully, regenerate CSV test files
            if (self.csv_archive_parse_success and self.tnc_parse_success and 
                self.spreadsheet_parse_success and self.csv_archive_path):
                self._regenerate_csv_test_files()
    
    def _parse_csv_archive(self) -> None:
        """Parse selected CSV archive file"""
        if not self.csv_archive_path:
            return
        
        # Check if TNC scenarios are parsed
        if not self.parsed_scenarios:
            self.csv_archive_parse_success = False
            self.csv_archive_parse_error = TRANSLATIONS[self.current_language].get(
                "csv_no_scenarios", 
                "Please parse TOMMM file first"
            )
            self._update_csv_archive_status_icon()
            return
        
        parser = CSVArchiveParser(self.current_language)
        success, error_message = parser.parse(
            self.csv_archive_path,
            self.parsed_scenarios,
            self.parsed_items if self.spreadsheet_parse_success else []
        )
        
        self.csv_archive_parse_success = success
        self.csv_archive_parse_error = error_message
        
        # Update status icon
        self._update_csv_archive_status_icon()
    
    def _update_csv_archive_status_icon(self) -> None:
        """Update CSV archive parsing status button"""
        t = TRANSLATIONS[self.current_language]
        
        if self.csv_archive_parse_success is None:
            self.csv_archive_status_button.hide()
            # Even without CSV parsing, enable scenarios button if scenarios are parsed
            self.show_scenarios_button.setEnabled(bool(self.parsed_scenarios))
            return
        
        self.csv_archive_status_button.show()
        
        if self.csv_archive_parse_success:
            # Subtle green button with checkmark (success)
            self.csv_archive_status_button.setText("✓")
            self.csv_archive_status_button.setToolTip(t["tooltip_parse_success"])
            self.csv_archive_status_button.setStyleSheet(
                "QPushButton {"
                "  background-color: #e8f5e9; "
                "  color: #2e7d32; "
                "  font-weight: bold; "
                "  font-size: 16px; "
                "  border: none; "
                "  border-radius: 3px; "
                "  padding: 2px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #c8e6c9; "
                "}"
                "QPushButton:pressed {"
                "  background-color: #a5d6a7; "
                "}"
            )
            # CSV parsed successfully; enable scenarios button when scenarios are parsed
            self.show_scenarios_button.setEnabled(bool(self.parsed_scenarios))
        else:
            # Subtle red button with X (error)
            self.csv_archive_status_button.setText("✗")
            self.csv_archive_status_button.setToolTip(t["tooltip_parse_error"])
            self.csv_archive_status_button.setStyleSheet(
                "QPushButton {"
                "  background-color: #ffebee; "
                "  color: #c62828; "
                "  font-weight: bold; "
                "  font-size: 16px; "
                "  border: none; "
                "  border-radius: 3px; "
                "  padding: 2px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #ffcdd2; "
                "}"
                "QPushButton:pressed {"
                "  background-color: #ef9a9a; "
                "}"
            )
            # Even if CSV parsing failed, enable scenarios button when scenarios are parsed
            self.show_scenarios_button.setEnabled(bool(self.parsed_scenarios))
    
    def _show_csv_archive_parse_status(self) -> None:
        """Show CSV archive parsing status message"""
        t = TRANSLATIONS[self.current_language]
        
        if self.csv_archive_parse_success is None:
            return
        
        if self.csv_archive_parse_success:
            QMessageBox.information(
                self,
                t.get("parsing_status", "Статус парсингу"),
                t.get("csv_archive_parse_success", "Парсинг CSV дизайнів для сценаріїв завершено успішно")
            )
        else:
            error_msg = self.csv_archive_parse_error or t.get("csv_archive_parse_error", "Помилка парсингу")
            QMessageBox.warning(
                self,
                t.get("parsing_status", "Статус парсингу"),
                error_msg
            )
    
    def _refresh_csv_archive_parsing(self) -> None:
        """Refresh CSV archive parsing data"""
        if self.csv_archive_path:
            self._parse_csv_archive()
    
    def _regenerate_csv_test_files(self) -> None:
        """Regenerate CSV test files for all scenarios"""
        if not self.parsed_scenarios or not self.parsed_items:
            return
        
        parser = CSVArchiveParser(self.current_language)
        errors = []
        
        for scenario in self.parsed_scenarios:
            if not scenario.csv_design:
                continue
            
            try:
                import csv
                import io
                csv_reader = csv.reader(io.StringIO(scenario.csv_design))
                csv_rows = list(csv_reader)
                
                csv_test_content = parser._generate_csv_test_file(csv_rows, self.parsed_items, errors)
                scenario.csv_test_file = csv_test_content
            except Exception as e:
                errors.append(f"Error regenerating test file for scenario {scenario.key}: {str(e)}")
        
        # Update status if there were errors
        if errors:
            self.csv_archive_parse_error = "\n".join(errors)
            self.csv_archive_parse_success = False
            self._update_csv_archive_status_icon()
    
    def _show_scenarios_info(self) -> None:
        """Show scenarios information dialog"""
        if not self.parsed_scenarios:
            return
        
        # Pass CSV parse success status to dialog
        csv_success = self.csv_archive_parse_success is True
        dialog = ScenariosInfoDialog(
            self.parsed_scenarios, 
            self.current_language, 
            csv_parse_success=csv_success,
            parent=self
        )
        dialog.exec()

    def _show_items_info(self) -> None:
        """Show information about parsed Item instances"""
        if not self.parsed_items:
            return
        dialog = ItemsInfoDialog(self.parsed_items, self.current_language, parent=self)
        dialog.exec()
    
    def _parse_tnc_file(self) -> None:
        """Parse selected TOMMM file"""
        if not self.tnc_platform_path:
            return
        
        parser = TOMMMParser(self.current_language)
        scenarios, company_name, error_message = parser.parse(self.tnc_platform_path)
        
        self.parsed_scenarios = scenarios
        self.tnc_company_name = company_name
        self.tnc_parse_success = (error_message is None and len(scenarios) > 0)
        self.tnc_parse_error = error_message
        
        # Update status icon
        self._update_tnc_status_icon()
        
        # Always update company name if parsed (both on auto-parse and refresh)
        if company_name:
            self.company_name_field.setText(company_name)
    
    def _update_tnc_status_icon(self) -> None:
        """Update TOMMM parsing status button"""
        t = TRANSLATIONS[self.current_language]
        
        if self.tnc_parse_success is None:
            self.tnc_status_button.hide()
            return
        
        self.tnc_status_button.show()
        
        if self.tnc_parse_success:
            # Subtle green button with checkmark (success)
            self.tnc_status_button.setText("✓")
            self.tnc_status_button.setToolTip(t["tooltip_parse_success"])
            self.tnc_status_button.setStyleSheet(
                "QPushButton {"
                "  background-color: #e8f5e9; "
                "  color: #2e7d32; "
                "  font-weight: bold; "
                "  font-size: 16px; "
                "  border: none; "
                "  border-radius: 3px; "
                "  padding: 2px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #c8e6c9; "
                "}"
                "QPushButton:pressed {"
                "  background-color: #a5d6a7; "
                "}"
            )
            # Show scenarios button if there are parsed scenarios
            if self.parsed_scenarios:
                self.show_scenarios_button.show()
                self.show_scenarios_button.setEnabled(True)
        else:
            # Subtle red button with X (error)
            self.tnc_status_button.setText("✗")
            self.tnc_status_button.setToolTip(t["tooltip_parse_error"])
            self.tnc_status_button.setStyleSheet(
                "QPushButton {"
                "  background-color: #ffebee; "
                "  color: #c62828; "
                "  font-weight: bold; "
                "  font-size: 16px; "
                "  border: none; "
                "  border-radius: 3px; "
                "  padding: 2px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #ffcdd2; "
                "}"
                "QPushButton:pressed {"
                "  background-color: #ef9a9a; "
                "}"
            )
            # On TNC parse error, disable (but do not hide) scenarios button
            self.show_scenarios_button.setEnabled(False)
    
    def _show_tnc_parse_status(self) -> None:
        """Show TOMMM parsing status message"""
        t = TRANSLATIONS[self.current_language]
        
        if self.tnc_parse_success is None:
            return
        
        if self.tnc_parse_success:
            QMessageBox.information(
                self,
                t.get("parsing_status", "Статус парсингу"),
                t.get("tnc_parse_success", "Парсинг ключів та назв сценаріїв завершено успішно")
            )
        else:
            error_msg = self.tnc_parse_error or t.get("tnc_parse_error", "Помилка парсингу")
            QMessageBox.warning(
                self,
                t.get("parsing_status", "Статус парсингу"),
                error_msg
            )
    
    def _refresh_tnc_parsing(self) -> None:
        """Refresh TOMMM parsing data"""
        if self.tnc_platform_path:
            self._parse_tnc_file()
    
    def _set_window_icon(self) -> None:
        """Set window icon from file or use default"""
        # Try to load icon from application folder
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            # Try PNG as fallback
            icon_path = Path(__file__).parent / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # Create a simple default icon if no file exists
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.transparent)
                # Draw a simple "T" letter as default icon
                from PyQt6.QtGui import QPainter, QColor
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.fillRect(0, 0, 32, 32, QColor(33, 150, 243))  # Blue background
                painter.setPen(QColor(255, 255, 255))  # White text
                font = QFont()
                font.setPointSize(20)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(0, 0, 32, 32, Qt.AlignmentFlag.AlignCenter, "T")
                painter.end()
                self.setWindowIcon(QIcon(pixmap))
    
    def open_items_editor(self) -> None:
        """Open Items Properties Editor"""
        editor = ItemPropertiesEditor(self.database, self.current_language, self)
        editor.exec()

