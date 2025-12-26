"""Main window module for the application"""

from pathlib import Path
from typing import List, Optional

import copy
import csv
import io
import xml.etree.ElementTree as ET

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
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

from application.artifact_settings_dialog import (
    CSVInboundItemsDialog,
    InvoiceSettingsDialog,
    OrderAckSettingsDialog,
    ShipmentSettingsDialog,
    XTLSettingsDialog,
)
from application.config import ConfigManager
from application.csv_parser import CSVArchiveParser
from application.database import Database
from application.database_editor import ItemPropertiesEditor
from application.items_dialog import ItemsInfoDialog
from application.file_handlers import InputFileFinder, OutputFileWriter, XTLParser
from application.scenarios_dialog import ScenariosInfoDialog
from application.spreadsheet_parser import Item, SpreadsheetParser
from application.tommm_parser import InboundDocScenario, TOMMMParser
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

        # Artifact generation settings (checkboxes states)
        self.artifact_settings = {
            "gen_xtl_850": True,
            "gen_xtl_860": True,
            "gen_csv_inbound": True,
            "gen_rsx_855": False,
            "gen_rsx_856": False,
            "gen_rsx_810": False,
            "xtl_850_settings": {},
            "xtl_860_settings": {},
            "csv_inbound_settings": {},
            "rsx_855_settings": {},
            "rsx_856_settings": {},
            "rsx_810_settings": {},
        }
        
        # Initialize artifact checkboxes list (will be populated in create_ui)
        self.artifact_checkboxes: List = []

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

    def _create_gear_icon(self) -> QIcon:
        """Create a simple gear-like icon for settings buttons using text"""
        # Return empty icon, will use text "⚙" in button text
        qicon = QIcon()
        return qicon

    def _create_artifact_checkboxes(self) -> None:
        """Create artifact generation checkboxes with settings buttons"""
        t = TRANSLATIONS[self.current_language]
        self.artifact_checkboxes = []
        
        # Define checkboxes with their properties
        checkbox_defs = [
            {
                "key": "gen_xtl_850",
                "label_key": "gen_xtl_850",
                "has_settings": True,
                "settings_type": "xtl_850",
            },
            {
                "key": "gen_xtl_860",
                "label_key": "gen_xtl_860",
                "has_settings": True,
                "settings_type": "xtl_860",
            },
            {
                "key": "gen_csv_inbound",
                "label_key": "gen_csv_inbound",
                "has_settings": True,
                "settings_type": "csv_inbound",
            },
            {
                "key": "gen_rsx_855",
                "label_key": "gen_rsx_855",
                "has_settings": True,
                "settings_type": "rsx_855",
            },
            {
                "key": "gen_rsx_856",
                "label_key": "gen_rsx_856",
                "has_settings": True,
                "settings_type": "rsx_856",
            },
            {
                "key": "gen_rsx_810",
                "label_key": "gen_rsx_810",
                "has_settings": True,
                "settings_type": "rsx_810",
            },
        ]
        
        for def_item in checkbox_defs:
            cb = QCheckBox(t.get(def_item["label_key"], def_item["label_key"]))
            cb.setChecked(self.artifact_settings.get(def_item["key"], False))
            cb.stateChanged.connect(lambda state, key=def_item["key"]: self._on_artifact_checkbox_changed(key, state))  # type: ignore[arg-type]
            
            checkbox_info = {"checkbox": cb, "key": def_item["key"]}
            
            if def_item.get("has_settings"):
                settings_btn = QPushButton("⚙")
                settings_btn.setMaximumWidth(40)
                settings_btn.setMaximumHeight(28)
                settings_btn.setStyleSheet(
                    "QPushButton {"
                    "  font-size: 16px;"
                    "  font-weight: bold;"
                    "  background-color: #e8f4f8;"
                    "  border: none;"
                    "  border-radius: 4px;"
                    "  padding: 2px;"
                    "}"
                    "QPushButton:hover {"
                    "  background-color: #d0e8f5;"
                    "}"
                    "QPushButton:pressed {"
                    "  background-color: #b8dce8;"
                    "}"
                    "QPushButton:disabled {"
                    "  background-color: #f0f0f0;"
                    "  color: #999999;"
                    "}"
                )
                settings_type = def_item["settings_type"]
                settings_btn.clicked.connect(
                    lambda checked, st=settings_type: self._open_artifact_settings(st)  # type: ignore[arg-type]
                )
                checkbox_info["settings_button"] = settings_btn
                checkbox_info["settings_type"] = settings_type
            
            self.artifact_checkboxes.append(checkbox_info)

    def _on_artifact_checkbox_changed(self, key: str, state: int) -> None:
        """Handle artifact checkbox state change"""
        self.artifact_settings[key] = state != 0

        # Java Package Name becomes required only if at least one XTL artifact is enabled
        if key in {"gen_xtl_850", "gen_xtl_860"}:
            # Update label style and Process Data button availability
            self._update_java_package_label_style()
            self.update_process_button_state()

    def _init_artifact_tli_sources(self) -> None:
        """Initialize TLI sources in artifact_settings from parsed items (only if not already initialized)"""
        if not self.parsed_items:
            return
        
        # Only initialize if tli_sources doesn't exist yet (first time)
        # This prevents overwriting user's changes on refresh
        
        if "rsx_855_settings" not in self.artifact_settings:
            self.artifact_settings["rsx_855_settings"] = {}
        
        if "tli_sources" not in self.artifact_settings["rsx_855_settings"]:
            tli_855 = {}
            for item in self.parsed_items:
                rsx_path_855 = getattr(item, "rsx_path_855", "")
                item_id = getattr(item, "item_properties_id", None)
                if rsx_path_855 and item_id:
                    tli_855[str(item_id)] = getattr(item, "put_in_855", False)
            self.artifact_settings["rsx_855_settings"]["tli_sources"] = tli_855
        
        if "rsx_856_settings" not in self.artifact_settings:
            self.artifact_settings["rsx_856_settings"] = {}
        
        if "tli_sources" not in self.artifact_settings["rsx_856_settings"]:
            tli_856 = {}
            for item in self.parsed_items:
                rsx_path_856 = getattr(item, "rsx_path_856", "")
                item_id = getattr(item, "item_properties_id", None)
                if rsx_path_856 and item_id:
                    tli_856[str(item_id)] = getattr(item, "put_in_856", False)
            self.artifact_settings["rsx_856_settings"]["tli_sources"] = tli_856
        
        if "rsx_810_settings" not in self.artifact_settings:
            self.artifact_settings["rsx_810_settings"] = {}
        
        if "tli_sources" not in self.artifact_settings["rsx_810_settings"]:
            tli_810 = {}
            for item in self.parsed_items:
                rsx_path_810 = getattr(item, "rsx_path_810", "")
                item_id = getattr(item, "item_properties_id", None)
                if rsx_path_810 and item_id:
                    tli_810[str(item_id)] = getattr(item, "put_in_810", False)
            self.artifact_settings["rsx_810_settings"]["tli_sources"] = tli_810

    def _open_artifact_settings(self, settings_type: str) -> None:
        """Open settings dialog for artifact generation"""
        # Get previous settings if they exist
        settings_key = f"{settings_type}_settings"
        previous_settings = self.artifact_settings.get(settings_key, {})
        
        if settings_type == "xtl_850":
            dialog = XTLSettingsDialog(self.current_language, doc_type="850", previous_settings=previous_settings, parent=self)
        elif settings_type == "xtl_860":
            dialog = XTLSettingsDialog(self.current_language, doc_type="860", previous_settings=previous_settings, parent=self)
        elif settings_type == "rsx_855":
            dialog = OrderAckSettingsDialog(self.current_language, self.parsed_items, previous_settings=previous_settings, parent=self)
        elif settings_type == "rsx_856":
            dialog = ShipmentSettingsDialog(self.current_language, self.parsed_items, previous_settings=previous_settings, parent=self)
        elif settings_type == "rsx_810":
            dialog = InvoiceSettingsDialog(self.current_language, self.parsed_items, previous_settings=previous_settings, parent=self)
        elif settings_type == "csv_inbound":
            dialog = CSVInboundItemsDialog(self.current_language, self.parsed_items, previous_settings=previous_settings, parent=self)
        else:
            return
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings_key = f"{settings_type}_settings"
            settings = dialog.get_settings()
            
            self.artifact_settings[settings_key] = settings
            
            # Update ALL Item objects with TLI sources states (using item_id as key)
            if settings_type == "rsx_855" and "tli_sources" in settings:
                for item in self.parsed_items:
                    rsx_path = getattr(item, "rsx_path_855", "")
                    item_id = getattr(item, "item_properties_id", None)
                    if rsx_path and item_id:
                        item.put_in_855 = settings["tli_sources"].get(str(item_id), False)
            elif settings_type == "rsx_856" and "tli_sources" in settings:
                for item in self.parsed_items:
                    rsx_path = getattr(item, "rsx_path_856", "")
                    item_id = getattr(item, "item_properties_id", None)
                    if rsx_path and item_id:
                        item.put_in_856 = settings["tli_sources"].get(str(item_id), False)
            elif settings_type == "rsx_810" and "tli_sources" in settings:
                for item in self.parsed_items:
                    rsx_path = getattr(item, "rsx_path_810", "")
                    item_id = getattr(item, "item_properties_id", None)
                    if rsx_path and item_id:
                        item.put_in_810 = settings["tli_sources"].get(str(item_id), False)
            elif settings_type == "csv_inbound":
                # Regenerate CSV test files to apply updated item selection
                self._regenerate_csv_test_files()

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

        # Create Artifacts group
        artifacts_group = QGroupBox()
        self.ui_elements["artifacts_group_title"] = artifacts_group
        artifacts_layout = QVBoxLayout()
        # Make rows in "Create Artifacts" compact, but keep padding from group border
        artifacts_layout.setContentsMargins(8, 6, 8, 6)
        artifacts_layout.setSpacing(2)
        
        # Initialize artifact checkboxes
        self._create_artifact_checkboxes()
        for checkbox_info in self.artifact_checkboxes:
            cb = checkbox_info["checkbox"]
            settings_btn = checkbox_info.get("settings_button")

            # Wrap each row in its own container with subtle highlighting
            row_widget = QWidget()
            row_widget.setObjectName("artifact_row")
            row_layout = QHBoxLayout()
            # Minimal margins and spacing inside each row
            row_layout.setContentsMargins(4, 0, 4, 0)
            row_layout.setSpacing(4)
            row_widget.setLayout(row_layout)

            # Subtle background and border to visually group checkbox + gear
            # Style is applied only to the row container, not to child widgets
            row_widget.setStyleSheet(
                "#artifact_row {"
                "  background-color: #f7f9fc;"
                "  border: 1px solid #dde3f0;"
                "  border-radius: 4px;"
                "}"
            )

            row_layout.addWidget(cb)
            row_layout.addStretch()

            if settings_btn:
                # Place gear button on the far right of the row
                row_layout.addWidget(settings_btn)

            artifacts_layout.addWidget(row_widget)
        
        artifacts_layout.addSpacing(10)
        
        # Process Data and Open output folder buttons
        buttons_layout = QHBoxLayout()

        self.process_button = QPushButton(t["process_data"])
        self.ui_elements["process_button"] = self.process_button
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_data)  # type: ignore[arg-type]
        buttons_layout.addWidget(self.process_button, stretch=7)

        self.open_output_button = QPushButton(t["open_output_folder"])
        self.open_output_button.clicked.connect(self.open_output_folder)  # type: ignore[arg-type]
        buttons_layout.addWidget(self.open_output_button, stretch=3)

        buttons_layout.addStretch()
        artifacts_layout.addLayout(buttons_layout)
        
        artifacts_group.setLayout(artifacts_layout)
        layout.addWidget(artifacts_group)

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

    def _is_java_package_required(self) -> bool:
        """Return True if Java Package Name field is required.
        
        The field is required only when generation of poRsxRead.xtl (850)
        or pcRsxWrite.xtl (860) is enabled. In all other cases it is
        considered optional.
        """
        return bool(
            self.artifact_settings.get("gen_xtl_850", False)
            or self.artifact_settings.get("gen_xtl_860", False)
        )

    def _update_java_package_label_style(self) -> None:
        """Update Java Package Name label style based on field content"""
        package_label = self.ui_elements["package_label"]
        has_text = bool(self.java_package_field.text().strip())
        is_required = self._is_java_package_required()

        # If the field is not required (both XTL checkboxes are off), the label is always normal
        if not is_required:
            package_label.setStyleSheet("color: black;")
            font = package_label.font()
            font.setBold(False)
            package_label.setFont(font)
            return

        # If the field is required, highlight it only when it is empty
        if has_text:
            package_label.setStyleSheet("color: black;")
            font = package_label.font()
            font.setBold(False)
            package_label.setFont(font)
        else:
            package_label.setStyleSheet("color: red;")
            font = package_label.font()
            font.setBold(True)
            package_label.setFont(font)
    
    def update_process_button_state(self) -> None:
        """Update Process Data button state and artifact checkboxes"""
        has_spreadsheet = self.spreadsheet_path is not None
        has_tnc_platform = self.tnc_platform_path is not None
        has_csv_archive = self.csv_archive_path is not None
        has_company_name = bool(self.company_name_field.text().strip())
        has_java_package = bool(self.java_package_field.text().strip())
        has_author = bool(self.author_field.text().strip())
        java_required = self._is_java_package_required()
        
        all_parsed_successfully = (
            self.spreadsheet_parse_success is True
            and self.tnc_parse_success is True
            and self.csv_archive_parse_success is True
        )

        self.process_button.setEnabled(
            has_spreadsheet
            and has_tnc_platform
            and has_csv_archive
            and has_company_name
            and has_author
            and (not java_required or has_java_package)
        )
        
        # Initialize TLI sources in artifact_settings if all parsed successfully
        if all_parsed_successfully:
            self._init_artifact_tli_sources()
        
        # Update artifact checkboxes state
        self._update_artifact_checkboxes_state(all_parsed_successfully)

    def _update_artifact_checkboxes_state(self, all_parsed_successfully: bool) -> None:
        """Update enabled state of artifact checkboxes based on parsing results"""
        # If artifact checkboxes not yet created, skip
        if not hasattr(self, "artifact_checkboxes") or not self.artifact_checkboxes:
            return
        
        # Check which documents are available in parsed scenarios
        has_850 = any(s.document_number == 850 for s in self.parsed_scenarios)
        has_860 = any(s.document_number == 860 for s in self.parsed_scenarios)
        has_855 = any(s.includes_855_docs for s in self.parsed_scenarios)
        has_856 = any(s.includes_856_docs for s in self.parsed_scenarios)
        has_810 = any(s.includes_810_docs for s in self.parsed_scenarios)
        
        for checkbox_info in self.artifact_checkboxes:
            key = checkbox_info["key"]
            cb = checkbox_info["checkbox"]
            settings_btn = checkbox_info.get("settings_button")
            
            if key == "gen_xtl_850":
                enabled = all_parsed_successfully and has_850
                cb.setEnabled(enabled)
            elif key == "gen_xtl_860":
                enabled = all_parsed_successfully and has_860
                cb.setEnabled(enabled)
            elif key == "gen_csv_inbound":
                cb.setEnabled(all_parsed_successfully)
            elif key == "gen_rsx_855":
                enabled = all_parsed_successfully and has_855
                cb.setEnabled(enabled)
                if enabled and not cb.isChecked():
                    cb.setChecked(True)
            elif key == "gen_rsx_856":
                enabled = all_parsed_successfully and has_856
                cb.setEnabled(enabled)
                if enabled and not cb.isChecked():
                    cb.setChecked(True)
            elif key == "gen_rsx_810":
                enabled = all_parsed_successfully and has_810
                cb.setEnabled(enabled)
                if enabled and not cb.isChecked():
                    cb.setChecked(True)
            
            if settings_btn:
                settings_btn.setEnabled(cb.isEnabled())

    def load_last_author(self) -> None:
        """Load last author value from configuration"""
        author = self.config_manager.get_last_author()
        if author:
            self.author_field.setText(author)

    def save_last_author(self) -> None:
        """Save last author value to configuration"""
        author = self.author_field.text().strip()
        self.config_manager.save_last_author(author)

    def open_output_folder(self) -> None:
        """Open the output folder in the system file manager"""
        output_dir = self.base_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # On Windows, use os.startfile to open the folder in Explorer
            import os

            os.startfile(str(output_dir))  # type: ignore[attr-defined]
        except Exception as e:
            t = TRANSLATIONS[self.current_language]
            QMessageBox.warning(
                self,
                t["warning"],
                f"Failed to open output folder:\n{str(e)}",
            )

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
        java_required = self._is_java_package_required()

        # Company Name and Author are always required.
        # Java Package Name is required only if generation of poRsxRead.xtl or pcRsxWrite.xtl is enabled.
        if (not company_name) or (not author) or (java_required and not java_package):
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
            
            # Generate CSV test files if checkbox is enabled
            if self.artifact_settings.get("gen_csv_inbound", False):
                self._generate_csv_test_files(output_dir)

            # Generate unified RSX 855 test file if checkbox is enabled
            if self.artifact_settings.get("gen_rsx_855", False):
                try:
                    self._generate_rsx_855_test_file(output_dir)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        t["error"],
                        f"Error generating 855 RSX test file:\n{str(e)}",
                    )

            # Generate unified RSX 856 test files if checkbox is enabled
            if self.artifact_settings.get("gen_rsx_856", False):
                try:
                    self._generate_rsx_856_test_file(output_dir)
                    self._generate_rsx_856_consolidated_test_file(output_dir)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        t["error"],
                        f"Error generating 856 RSX test files:\n{str(e)}",
                    )

            # Generate unified RSX 810 test file if checkbox is enabled
            if self.artifact_settings.get("gen_rsx_810", False):
                try:
                    self._generate_rsx_810_test_file(output_dir)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        t["error"],
                        f"Error generating 810 RSX test file:\n{str(e)}",
                    )
            
            QMessageBox.information(
                self,
                t["success"],
                f"{t['data_saved']}:\n{output_file}",
            )

    def _generate_rsx_855_test_file(self, output_dir: Path) -> None:
        """Generate unified RSX 855 XML test file based on OrderAck.xml template."""
        # Determine scenarios that include 855 documents
        scenarios_855 = [s for s in self.parsed_scenarios if s.includes_855_docs]
        if not scenarios_855:
            return

        # Load 855 settings
        rsx_settings = self.artifact_settings.get("rsx_855_settings", {})
        gen_ack_type = rsx_settings.get("gen_ack_type", True)
        gen_line_seq = rsx_settings.get("gen_line_seq", True)
        gen_item_status = rsx_settings.get("gen_item_status", True)

        # Compute max number_of_lines across all 855 scenarios
        max_lines = max((s.number_of_lines for s in scenarios_855), default=0)
        if max_lines <= 0:
            max_lines = 1

        # Choose scenario with maximum LineItem_OrderLine rows for LineSequenceNumber
        scenario_for_seq = max(scenarios_855, key=lambda s: s.number_of_lines or 0)

        # Load OrderAck.xml template from templates folder
        template_path = self.base_path / "application" / "templates" / "OrderAck.xml"
        tree = ET.parse(template_path)
        root = tree.getroot()

        # Clear all text values from template
        self._clear_order_ack_xml_texts(root)

        # Clone LineItem nodes according to max_lines
        self._clone_order_ack_line_items(root, max_lines)

        # Apply AcknowledgementType drafts if enabled
        if gen_ack_type:
            self._apply_ack_type_drafts(root)

        # Apply ItemStatusCode drafts if enabled
        if gen_item_status:
            self._apply_item_status_drafts(root)

        # Apply LineSequenceNumber values if enabled
        if gen_line_seq:
            self._apply_line_sequence_numbers(root, scenario_for_seq)

        # Apply PurchaseOrderNumber values (first live, others commented)
        self._apply_purchase_order_numbers(root, scenarios_855)

        # Apply TLI Sources values (including Header/Address grouping)
        self._apply_tli_sources_855(root, max_lines)

        # Always set TradingPartnerId in header for test 855 file
        self._set_xml_value_by_path(
            root,
            ["Header", "OrderHeader", "TradingPartnerId"],
            "TestTPID",
        )

        # Prune empty elements
        self._prune_empty_elements(root)

        # Pretty-print / indent XML (without XML declaration)
        # Prefer built-in ET.indent when available to keep opening/closing
        # tags on the same level and use tabs for indentation.
        if hasattr(ET, "indent"):
            ET.indent(tree, space="\t", level=0)  # type: ignore[attr-defined]
        else:
            self._indent_xml(root)

        rsx_output_dir = output_dir / "RSX max test files"
        rsx_output_dir.mkdir(parents=True, exist_ok=True)
        output_file = rsx_output_dir / "855_RSX_test_file.xml"

        tree.write(output_file, encoding="utf-8", xml_declaration=False)

    def _generate_rsx_856_test_file(self, output_dir: Path) -> None:
        """Generate unified RSX 856 XML test file based on Shipment.xml template.

        Uses non-consolidated scenarios (includes_856_docs=True, is_consolidated=False)
        and creates a single Shipment/OrderLevel/PackLevel that contains
        max(number_of_lines) ItemLevel repetitions.
        """
        # Select non-consolidated 856 scenarios
        scenarios_856 = [
            s
            for s in self.parsed_scenarios
            if getattr(s, "includes_856_docs", False) and not getattr(s, "is_consolidated", False)
        ]
        if not scenarios_856:
            return

        # Load 856 settings
        rsx_settings = self.artifact_settings.get("rsx_856_settings", {})
        gen_tset_purpose = rsx_settings.get("gen_tset_purpose", True)
        gen_line_seq = rsx_settings.get("gen_line_seq", True)

        # Determine max number_of_lines among selected scenarios
        max_lines = max((s.number_of_lines for s in scenarios_856), default=0)
        if max_lines <= 0:
            max_lines = 1

        # Choose scenario with maximum LineItem_OrderLine rows for LineSequenceNumber
        scenario_for_seq = max(scenarios_856, key=lambda s: s.number_of_lines or 0)

        # Load Shipment.xml template
        template_path = self.base_path / "application" / "templates" / "Shipment.xml"
        tree = ET.parse(template_path)
        root = tree.getroot()

        # Clear all text values from template
        self._clear_order_ack_xml_texts(root)

        # Clone ItemLevel nodes according to max_lines
        self._clone_shipment_item_levels(root, max_lines)

        # Apply TsetPurposeCode drafts if enabled
        if gen_tset_purpose:
            self._apply_tset_purpose_drafts_856(root)

        # Apply LineSequenceNumber values if enabled
        if gen_line_seq:
            self._apply_line_sequence_numbers_856(root, scenario_for_seq)

        # Apply PurchaseOrderNumber values (first live, others commented)
        self._apply_purchase_order_numbers(root, scenarios_856)

        # Apply TLI Sources values (including Header/Address grouping)
        self._apply_tli_sources_856(root)

        # Always set TradingPartnerId and ShipmentIdentification in header for test file
        self._set_xml_value_by_path(
            root,
            ["Header", "ShipmentHeader", "TradingPartnerId"],
            "TestTPID",
        )
        self._set_xml_value_by_path(
            root,
            ["Header", "ShipmentHeader", "ShipmentIdentification"],
            "TestBSN02",
        )

        # Prune empty elements
        self._prune_empty_elements(root)

        # Pretty-print / indent XML (without XML declaration)
        if hasattr(ET, "indent"):
            ET.indent(tree, space="\t", level=0)  # type: ignore[attr-defined]
        else:
            self._indent_xml(root)

        rsx_output_dir = output_dir / "RSX max test files"
        rsx_output_dir.mkdir(parents=True, exist_ok=True)
        output_file = rsx_output_dir / "856_RSX_test_file.xml"

        tree.write(output_file, encoding="utf-8", xml_declaration=False)

    def _generate_rsx_810_test_file(self, output_dir: Path) -> None:
        """Generate unified RSX 810 XML test file based on Invoice.xml template."""
        # Determine scenarios that include 810 documents
        scenarios_810 = [s for s in self.parsed_scenarios if s.includes_810_docs]
        if not scenarios_810:
            return

        # Load 810 settings
        rsx_settings = self.artifact_settings.get("rsx_810_settings", {})
        gen_taxes = rsx_settings.get("gen_taxes", True)
        gen_charges = rsx_settings.get("gen_charges", True)
        gen_line_seq = rsx_settings.get("gen_line_seq", True)
        gen_total_amount = rsx_settings.get("gen_total_amount", True)

        # Compute max number_of_lines across all 810 scenarios
        max_lines = max((s.number_of_lines for s in scenarios_810), default=0)
        if max_lines <= 0:
            max_lines = 1

        # Choose scenario with maximum LineItem_OrderLine rows for LineSequenceNumber
        scenario_for_seq = max(scenarios_810, key=lambda s: s.number_of_lines or 0)

        # Load Invoice.xml template from templates folder
        template_path = self.base_path / "application" / "templates" / "Invoice.xml"
        tree = ET.parse(template_path)
        root = tree.getroot()

        # Clear all text values from template
        self._clear_order_ack_xml_texts(root)

        # Clone LineItem nodes according to max_lines
        self._clone_invoice_line_items(root, max_lines)

        # Apply LineSequenceNumber values if enabled
        if gen_line_seq:
            self._apply_line_sequence_numbers_810(root, scenario_for_seq)

        # Apply PurchaseOrderNumber values (first live, others commented)
        self._apply_purchase_order_numbers(root, scenarios_810)

        # Apply ChargesAllowances block if enabled
        if gen_charges:
            self._apply_charges_allowances_810(root)

        # Apply Taxes block if enabled
        if gen_taxes:
            self._apply_taxes_810(root)

        # Apply TLI Sources values (including Header/Address grouping)
        self._apply_tli_sources_810(root, max_lines)

        # Always set TradingPartnerId and InvoiceNumber in header for test 810 file
        self._set_xml_value_by_path(
            root,
            ["Header", "InvoiceHeader", "TradingPartnerId"],
            "TestTPID",
        )
        self._set_xml_value_by_path(
            root,
            ["Header", "InvoiceHeader", "InvoiceNumber"],
            "TestInvoiceNumber",
        )

        # Apply TotalAmount if enabled
        if gen_total_amount:
            self._apply_total_amount_810(root)

        # Prune empty elements
        self._prune_empty_elements(root)

        # Pretty-print / indent XML (without XML declaration)
        if hasattr(ET, "indent"):
            ET.indent(tree, space="\t", level=0)  # type: ignore[attr-defined]
        else:
            self._indent_xml(root)

        rsx_output_dir = output_dir / "RSX max test files"
        rsx_output_dir.mkdir(parents=True, exist_ok=True)
        output_file = rsx_output_dir / "810_RSX_test_file.xml"

        tree.write(output_file, encoding="utf-8", xml_declaration=False)

    def _generate_rsx_856_consolidated_test_file(self, output_dir: Path) -> None:
        """Generate consolidated RSX 856 XML test file based on Shipment.xml template.

        Uses scenarios where includes_856_docs=True and is_consolidated=True.
        For each such scenario, creates its own Shipment/OrderLevel block with
        PurchaseOrderNumber from scenario.key and ItemLevel repetitions based on
        that scenario's number_of_lines. Additionally, for the first consolidated
        scenario, splits the first PackLevel into two with ShipQty halved.
        """
        scenarios_consolidated = [
            s
            for s in self.parsed_scenarios
            if getattr(s, "includes_856_docs", False) and getattr(s, "is_consolidated", False)
        ]
        if not scenarios_consolidated:
            return

        rsx_settings = self.artifact_settings.get("rsx_856_settings", {})
        gen_tset_purpose = rsx_settings.get("gen_tset_purpose", True)
        gen_line_seq = rsx_settings.get("gen_line_seq", True)

        template_path = self.base_path / "application" / "templates" / "Shipment.xml"
        tree = ET.parse(template_path)
        root = tree.getroot()

        # Clear all text values from template
        self._clear_order_ack_xml_texts(root)

        # Find template OrderLevel and its parent (Shipment root)
        order_parent = None
        template_order_level = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("OrderLevel"):
                template_order_level = elem
                break

        if template_order_level is None:
            return

        # Determine parent of OrderLevel
        for parent in root.iter():
            if template_order_level in list(parent):
                order_parent = parent
                break

        if order_parent is None:
            return

        # Remove existing OrderLevel children from parent
        for child in list(order_parent):
            if isinstance(child.tag, str) and child.tag == template_order_level.tag:
                order_parent.remove(child)

        created_order_levels = []

        # Create separate OrderLevel per consolidated scenario
        for scenario in scenarios_consolidated:
            order_level = copy.deepcopy(template_order_level)

            # For this scenario, clone ItemLevel nodes according to its number_of_lines
            max_lines = scenario.number_of_lines or 1
            self._clone_shipment_item_levels(order_level, max_lines)

            # Apply LineSequenceNumber per scenario if enabled
            if gen_line_seq:
                self._apply_line_sequence_numbers_856(order_level, scenario)

            # Set PurchaseOrderNumber for this OrderLevel
            self._set_xml_value_by_path(
                order_level,
                ["OrderHeader", "PurchaseOrderNumber"],
                scenario.key,
            )

            order_parent.append(order_level)
            created_order_levels.append(order_level)

        # Apply TLI Sources values (including Header/Address grouping) first,
        # щоб усі кількості ShipQty та інші TLI-дані були заповнені.
        self._apply_tli_sources_856(root)

        # For the first consolidated scenario, split first PackLevel in half
        # на основі вже заповненої кількості ShipQty.
        if created_order_levels:
            self._split_first_packlevel_in_half(created_order_levels[0])

        # Apply TsetPurposeCode drafts if enabled
        if gen_tset_purpose:
            self._apply_tset_purpose_drafts_856(root)

        # Always set TradingPartnerId and ShipmentIdentification in header
        self._set_xml_value_by_path(
            root,
            ["Header", "ShipmentHeader", "TradingPartnerId"],
            "TestTPID",
        )
        self._set_xml_value_by_path(
            root,
            ["Header", "ShipmentHeader", "ShipmentIdentification"],
            "TestBSN02",
        )

        # Prune empty elements
        self._prune_empty_elements(root)

        # Pretty-print / indent XML (without XML declaration)
        if hasattr(ET, "indent"):
            ET.indent(tree, space="\t", level=0)  # type: ignore[attr-defined]
        else:
            self._indent_xml(root)

        rsx_output_dir = output_dir / "RSX max test files"
        rsx_output_dir.mkdir(parents=True, exist_ok=True)
        output_file = rsx_output_dir / "856_RSX_consolidated_test_file.xml"

        tree.write(output_file, encoding="utf-8", xml_declaration=False)

    def _clear_order_ack_xml_texts(self, element: ET.Element) -> None:
        """Recursively clear text and tail for all elements in OrderAck template."""
        element.text = None
        element.tail = None
        for child in list(element):
            self._clear_order_ack_xml_texts(child)

    def _clone_order_ack_line_items(self, root: ET.Element, max_lines: int) -> None:
        """Clone LineItem elements so that their count equals max_lines."""
        # Find first LineItem under OrderAck
        line_items_parent = None
        first_line_item = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("LineItem"):
                first_line_item = elem
                line_items_parent = elem.getparent() if hasattr(elem, "getparent") else None
                break

        if first_line_item is None:
            return

        # xml.etree.ElementTree elements do not have getparent by default,
        # so if parent is not determined, infer it by traversing children
        if line_items_parent is None:
            for parent in root.iter():
                if first_line_item in list(parent):
                    line_items_parent = parent
                    break

        if line_items_parent is None:
            return

        # Remove all existing LineItem children and recreate from template
        template_line_item = copy.deepcopy(first_line_item)
        for child in list(line_items_parent):
            if isinstance(child.tag, str) and child.tag == first_line_item.tag:
                line_items_parent.remove(child)

        for _ in range(max_lines):
            line_items_parent.append(copy.deepcopy(template_line_item))

    def _clone_invoice_line_items(self, root: ET.Element, max_lines: int) -> None:
        """Clone Invoice LineItem elements so that their count equals max_lines."""
        line_items_parent = None
        first_line_item = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("LineItem"):
                first_line_item = elem
                line_items_parent = elem.getparent() if hasattr(elem, "getparent") else None
                break

        if first_line_item is None:
            return

        if line_items_parent is None:
            for parent in root.iter():
                if first_line_item in list(parent):
                    line_items_parent = parent
                    break

        if line_items_parent is None:
            return

        # Remember original position of the first LineItem so we can keep
        # Summary (and any other trailing siblings) after all LineItems.
        children = list(line_items_parent)
        try:
            insert_index = children.index(first_line_item)
        except ValueError:
            insert_index = len(children)

        template_line_item = copy.deepcopy(first_line_item)
        for child in list(line_items_parent):
            if isinstance(child.tag, str) and child.tag == first_line_item.tag:
                line_items_parent.remove(child)

        # Insert new LineItem blocks starting at the original index so that
        # Summary remains after all LineItem elements.
        for _ in range(max_lines):
            line_items_parent.insert(insert_index, copy.deepcopy(template_line_item))
            insert_index += 1

    def _clone_shipment_item_levels(self, root: ET.Element, max_lines: int) -> None:
        """Clone Shipment ItemLevel elements so that their count equals max_lines.

        Operates either on the full Shipment document root or on a subtree such as
        a specific OrderLevel when generating consolidated files.
        """
        item_parent = None
        first_item_level = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("ItemLevel"):
                first_item_level = elem
                break

        if first_item_level is None:
            return

        # Determine parent of ItemLevel (expected to be PackLevel)
        for parent in root.iter():
            if first_item_level in list(parent):
                item_parent = parent
                break

        if item_parent is None:
            return

        template_item = copy.deepcopy(first_item_level)

        # Remove all existing ItemLevel children under this parent
        for child in list(item_parent):
            if isinstance(child.tag, str) and child.tag == first_item_level.tag:
                item_parent.remove(child)

        # Append required number of ItemLevel clones
        for _ in range(max_lines):
            item_parent.append(copy.deepcopy(template_item))

    def _split_first_packlevel_in_half(self, order_level: ET.Element) -> None:
        """Split first PackLevel's first ItemLevel into a separate PackLevel with half ShipQty.

        Для першого консолідованого OrderLevel треба розбити кількість
        для першого ItemLevel на два різні PackLevel:
        - у вихідному PackLevel лишаються всі ItemLevel, але ShipQty першого
          ItemLevel ділиться навпіл;
        - створюється другий PackLevel, що містить лише копію цього першого
          ItemLevel з такою ж половинною ShipQty.
        """
        # Locate first PackLevel within this OrderLevel subtree
        pack_level = None
        for elem in order_level.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("PackLevel"):
                pack_level = elem
                break

        if pack_level is None:
            return

        # Find parent of PackLevel (expected to be the OrderLevel itself)
        parent = None
        for p in order_level.iter():
            if pack_level in list(p):
                parent = p
                break

        if parent is None:
            return

        # Find first ItemLevel inside this PackLevel
        first_item_level = None
        for child in pack_level:
            if isinstance(child.tag, str) and child.tag.endswith("ItemLevel"):
                first_item_level = child
                break

        if first_item_level is None:
            return

        # Find ShipQty element in the first ItemLevel
        shipqty_elem = None
        for el in first_item_level.iter():
            if isinstance(el.tag, str) and el.tag.endswith("ShipQty"):
                shipqty_elem = el
                break

        if shipqty_elem is None or shipqty_elem.text is None:
            return

        raw = shipqty_elem.text.strip()
        if not raw:
            return

        try:
            val = float(raw)
        except ValueError:
            return

        half_val = val / 2.0
        if "." in raw:
            decimals = len(raw.split(".")[1])
            fmt = f"{{:.{decimals}f}}"
            half_str = fmt.format(half_val)
        else:
            half_str = str(int(round(half_val)))

        # Set half value in original first ItemLevel
        shipqty_elem.text = half_str

        # Create a copy of the first ItemLevel (already with half ShipQty)
        new_item_level = copy.deepcopy(first_item_level)

        # Create new PackLevel based on original but leave only this one ItemLevel
        new_pack_level = copy.deepcopy(pack_level)
        for child in list(new_pack_level):
            if isinstance(child.tag, str) and child.tag.endswith("ItemLevel"):
                new_pack_level.remove(child)
        new_pack_level.append(new_item_level)

        # Insert the new PackLevel immediately after the original one
        children = list(parent)
        try:
            idx = children.index(pack_level)
        except ValueError:
            idx = len(children) - 1
        parent.insert(idx + 1, new_pack_level)

    def _apply_ack_type_drafts(self, root: ET.Element) -> None:
        """Set AcknowledgementType to AD and add commented alternatives.

        Each alternative code is added as its own commented AcknowledgementType
        node directly after the live AcknowledgementType element.
        """
        alt_codes = ["AK", "AC", "RD", "RJ"]
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("AcknowledgementType"):
                elem.text = "AD"
                parent = None
                for p in root.iter():
                    if isinstance(p.tag, str) and elem in list(p):
                        parent = p
                        break
                if parent is not None:
                    children = list(parent)
                    try:
                        idx = children.index(elem)
                    except ValueError:
                        idx = len(children) - 1
                    insert_index = idx + 1
                    for code in alt_codes:
                        comment = ET.Comment(f"<AcknowledgementType>{code}</AcknowledgementType>")
                        parent.insert(insert_index, comment)
                        insert_index += 1
                break

    def _apply_item_status_drafts(self, root: ET.Element) -> None:
        """Set ItemStatusCode in each LineItemAcknowledgement to IA and add commented alternatives.

        Each alternative code is added as its own commented ItemStatusCode node
        directly after the live ItemStatusCode element.
        """
        alt_codes = ["IR", "IB", "IP", "IQ", "DR"]
        for line_ack in root.iter():
            if isinstance(line_ack.tag, str) and line_ack.tag.endswith("LineItemAcknowledgement"):
                for idx, child in enumerate(list(line_ack)):
                    if isinstance(child.tag, str) and child.tag.endswith("ItemStatusCode"):
                        # Set main (uncommented) status code
                        child.text = "IA"
                        insert_index = idx + 1
                        # Insert a separate commented ItemStatusCode after the main one for each alternative code
                        for code in alt_codes:
                            comment = ET.Comment(f"<ItemStatusCode>{code}</ItemStatusCode>")
                            line_ack.insert(insert_index, comment)
                            insert_index += 1

    def _apply_tset_purpose_drafts_856(self, root: ET.Element) -> None:
        """Set TsetPurposeCode drafts for Shipment (856).

        Replaces the existing code with 00 and adds a commented alternative 06
        directly after it, preserving indentation.
        """
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("TsetPurposeCode"):
                elem.text = "00"
                parent = None
                for p in root.iter():
                    if isinstance(p.tag, str) and elem in list(p):
                        parent = p
                        break
                if parent is not None:
                    children = list(parent)
                    try:
                        idx = children.index(elem)
                    except ValueError:
                        idx = len(children) - 1
                    comment = ET.Comment("<TsetPurposeCode>06</TsetPurposeCode>")
                    parent.insert(idx + 1, comment)
                break

    def _apply_line_sequence_numbers(self, root: ET.Element, scenario_for_seq: InboundDocScenario) -> None:
        """Fill LineSequenceNumber in OrderLine items using csv_design of selected scenario.

        This is used for the 855 (OrderAck) document.
        """
        if not scenario_for_seq.csv_design:
            return

        # Extract LineItem_OrderLine rows from CSV design using CSV parser
        lines: List[str] = []
        csv_reader = csv.reader(io.StringIO(scenario_for_seq.csv_design))
        for row in csv_reader:
            # Expected format: LineItem_OrderLine, <LineSequenceNumber>, ...
            if len(row) > 0 and row[0] == "LineItem_OrderLine" and len(row) > 1:
                value = row[1].strip()
                if value:
                    lines.append(value)

        # Apply to LineItem/OrderLine/LineSequenceNumber only
        index = 0
        for line_item in root.iter():
            if isinstance(line_item.tag, str) and line_item.tag.endswith("LineItem"):
                order_line = None
                for child in line_item:
                    if isinstance(child.tag, str) and child.tag.endswith("OrderLine"):
                        order_line = child
                        break
                if order_line is None:
                    continue
                for child in order_line:
                    if isinstance(child.tag, str) and child.tag.endswith("LineSequenceNumber"):
                        if index < len(lines):
                            child.text = lines[index]
                        index += 1

    def _apply_line_sequence_numbers_810(self, root: ET.Element, scenario_for_seq: InboundDocScenario) -> None:
        """Fill LineSequenceNumber in InvoiceLine items using csv_design of selected scenario."""
        if not scenario_for_seq.csv_design:
            return

        # Extract LineItem_OrderLine rows from CSV design using CSV parser
        lines: List[str] = []
        csv_reader = csv.reader(io.StringIO(scenario_for_seq.csv_design))
        for row in csv_reader:
            # Expected format: LineItem_OrderLine, <LineSequenceNumber>, ...
            if len(row) > 0 and row[0] == "LineItem_OrderLine" and len(row) > 1:
                value = row[1].strip()
                if value:
                    lines.append(value)

        # Apply to LineItem/InvoiceLine/LineSequenceNumber only
        index = 0
        for line_item in root.iter():
            if isinstance(line_item.tag, str) and line_item.tag.endswith("LineItem"):
                invoice_line = None
                for child in line_item:
                    if isinstance(child.tag, str) and child.tag.endswith("InvoiceLine"):
                        invoice_line = child
                        break
                if invoice_line is None:
                    continue
                for child in invoice_line:
                    if isinstance(child.tag, str) and child.tag.endswith("LineSequenceNumber"):
                        if index < len(lines):
                            child.text = lines[index]
                        index += 1

    def _apply_line_sequence_numbers_856(self, root: ET.Element, scenario_for_seq: InboundDocScenario) -> None:
        """Fill LineSequenceNumber in ShipmentLine items using csv_design of selected scenario."""
        if not scenario_for_seq.csv_design:
            return

        # Extract LineItem_OrderLine rows from CSV design using CSV parser
        lines: List[str] = []
        csv_reader = csv.reader(io.StringIO(scenario_for_seq.csv_design))
        for row in csv_reader:
            # Expected format: LineItem_OrderLine, <LineSequenceNumber>, ...
            if len(row) > 0 and row[0] == "LineItem_OrderLine" and len(row) > 1:
                value = row[1].strip()
                if value:
                    lines.append(value)

        # Apply to ItemLevel/ShipmentLine/LineSequenceNumber
        index = 0
        for item_level in root.iter():
            if isinstance(item_level.tag, str) and item_level.tag.endswith("ItemLevel"):
                shipment_line = None
                for child in item_level:
                    if isinstance(child.tag, str) and child.tag.endswith("ShipmentLine"):
                        shipment_line = child
                        break
                if shipment_line is None:
                    continue
                for child in shipment_line:
                    if isinstance(child.tag, str) and child.tag.endswith("LineSequenceNumber"):
                        if index < len(lines):
                            child.text = lines[index]
                        index += 1

    def _apply_purchase_order_numbers(self, root: ET.Element, scenarios_855: List[InboundDocScenario]) -> None:
        """Set PurchaseOrderNumber from first 855 scenario and add commented alternatives for others."""
        if not scenarios_855:
            return

        first_value = scenarios_855[0].key
        other_values = [s.key for s in scenarios_855[1:]]

        po_parent = None
        po_element = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("PurchaseOrderNumber"):
                po_element = elem
                # Determine parent
                for p in root.iter():
                    if isinstance(p.tag, str) and elem in list(p):
                        po_parent = p
                        break
                break

        if po_element is None:
            return

        po_element.text = first_value

        if po_parent is None or not other_values:
            return

        # Insert commented PurchaseOrderNumber elements directly after the main one
        children = list(po_parent)
        try:
            idx = children.index(po_element)
        except ValueError:
            idx = len(children) - 1

        insert_index = idx + 1
        for value in other_values:
            comment = ET.Comment(f"<PurchaseOrderNumber>{value}</PurchaseOrderNumber>")
            po_parent.insert(insert_index, comment)
            insert_index += 1

    def _apply_tli_sources_855(self, root: ET.Element, max_lines: int) -> None:
        """Apply TLI Sources values to OrderAck XML, including Header/Address grouping."""
        rsx_settings = self.artifact_settings.get("rsx_855_settings", {})
        tli_sources = rsx_settings.get("tli_sources", {})
        if not tli_sources:
            return

        # Separate header and detail items
        header_items = []
        detail_items = []
        for item in self.parsed_items:
            item_id = getattr(item, "item_properties_id", None)
            rsx_path = getattr(item, "rsx_path_855", "")
            if not rsx_path or not item_id:
                continue
            if not tli_sources.get(str(item_id), False):
                continue
            if item.is_on_detail_level:
                detail_items.append(item)
            else:
                header_items.append(item)

        # Apply header items
        self._apply_header_tli_items(root, header_items)

        # Apply detail items for each LineItem
        self._apply_detail_tli_items(root, detail_items, max_lines)

    def _apply_header_tli_items(self, root: ET.Element, header_items: List[Item]) -> None:
        """Apply header-level TLI items for OrderAck with Extra Record grouping support."""

        def apply_normal_item(item: Item, path_parts: List[str]) -> None:
            """Apply a single header item without Extra Record grouping."""
            self._set_xml_value_by_path(root, path_parts, item.tli_value)

        self._apply_header_items_with_extra_records(
            root=root,
            header_items=header_items,
            rsx_attr_name="rsx_path_855",
            doc_root_name="OrderAck",
            apply_normal_item=apply_normal_item,
        )

    def _apply_detail_tli_items(self, root: ET.Element, detail_items: List[Item], max_lines: int) -> None:
        """Apply detail-level TLI items for each LineItem, substituting {sequential_number}."""
        if not detail_items:
            return

        # Collect all LineItem elements
        line_items = [elem for elem in root.iter() if isinstance(elem.tag, str) and elem.tag.endswith("LineItem")]
        if not line_items:
            return

        for index, line_item in enumerate(line_items, start=1):
            items_for_line = []
            for item in detail_items:
                if not item.rsx_path_855:
                    continue
                value = item.tli_value.replace("{sequential_number}", str(index))
                parts = item.rsx_path_855.split("_")
                # Skip leading parts until we reach LineItem subtree
                try:
                    idx = parts.index("LineItem")
                    sub_parts = parts[idx + 1 :]
                except ValueError:
                    sub_parts = parts
                items_for_line.append((item, sub_parts, value))

            self._apply_detail_items_with_extra_records(line_item, items_for_line)

    def _apply_tli_sources_856(self, root: ET.Element) -> None:
        """Apply TLI Sources values to Shipment XML, including Header/Address grouping."""
        rsx_settings = self.artifact_settings.get("rsx_856_settings", {})
        tli_sources = rsx_settings.get("tli_sources", {})
        if not tli_sources:
            return

        header_items: List[Item] = []
        detail_items: List[Item] = []
        for item in self.parsed_items:
            item_id = getattr(item, "item_properties_id", None)
            rsx_path = getattr(item, "rsx_path_856", "")
            if not rsx_path or not item_id:
                continue
            if not tli_sources.get(str(item_id), False):
                continue
            if item.is_on_detail_level:
                detail_items.append(item)
            else:
                header_items.append(item)

        self._apply_header_tli_items_856(root, header_items)
        self._apply_detail_tli_items_856(root, detail_items)

    def _apply_header_tli_items_856(self, root: ET.Element, header_items: List[Item]) -> None:
        """Apply header-level TLI items for Shipment with Extra Record grouping support."""

        def apply_normal_item(item: Item, path_parts: List[str]) -> None:
            """Apply a single header item without Extra Record grouping."""
            # Якщо шлях містить OrderLevel, значення має бути вставлене
            # в кожен Shipment/OrderLevel (наприклад, OrderHeader/Vendor
            # для кожного замовлення в консолідованому 856).
            if "OrderLevel" in path_parts:
                try:
                    idx = path_parts.index("OrderLevel")
                    sub_parts = path_parts[idx + 1 :]
                except ValueError:
                    sub_parts = path_parts

                order_levels = [
                    elem
                    for elem in root.iter()
                    if isinstance(elem.tag, str) and elem.tag.endswith("OrderLevel")
                ]
                for order_level in order_levels:
                    self._set_xml_value_by_path(order_level, sub_parts, item.tli_value)
            else:
                # Звичайний випадок: один елемент під Header/Shipment
                self._set_xml_value_by_path(root, path_parts, item.tli_value)

        self._apply_header_items_with_extra_records(
            root=root,
            header_items=header_items,
            rsx_attr_name="rsx_path_856",
            doc_root_name="Shipment",
            apply_normal_item=apply_normal_item,
        )

    def _apply_detail_tli_items_856(self, root: ET.Element, detail_items: List[Item]) -> None:
        """Apply detail-level TLI items for each Shipment ItemLevel, substituting {sequential_number}."""
        if not detail_items:
            return

        # Для консолідованого 856 нумерація повинна починатися з 1
        # всередині кожного OrderLevel окремо. Тому обробляємо ItemLevel
        # по групах OrderLevel, а не одним суцільним списком.

        order_levels = [
            elem for elem in root.iter() if isinstance(elem.tag, str) and elem.tag.endswith("OrderLevel")
        ]

        if order_levels:
            # Основний шлях: є явні OrderLevel, нумерація скидається для кожного
            for order_level in order_levels:
                item_levels = [
                    elem
                    for elem in order_level.iter()
                    if isinstance(elem.tag, str) and elem.tag.endswith("ItemLevel")
                ]
                if not item_levels:
                    continue
                for index, item_level in enumerate(item_levels, start=1):
                    items_for_level = []
                    for item in detail_items:
                        rsx_path = getattr(item, "rsx_path_856", "")
                        if not rsx_path:
                            continue
                        value = item.tli_value.replace("{sequential_number}", str(index))
                        parts = rsx_path.split("_")
                        try:
                            idx = parts.index("ItemLevel")
                            sub_parts = parts[idx + 1 :]
                        except ValueError:
                            sub_parts = parts
                        items_for_level.append((item, sub_parts, value))

                    self._apply_detail_items_with_extra_records(item_level, items_for_level)
        else:
            # Fallback: старий режим, якщо з якихось причин немає тегів OrderLevel
            item_levels = [
                elem for elem in root.iter() if isinstance(elem.tag, str) and elem.tag.endswith("ItemLevel")
            ]
            if not item_levels:
                return

            for index, item_level in enumerate(item_levels, start=1):
                items_for_level = []
                for item in detail_items:
                    rsx_path = getattr(item, "rsx_path_856", "")
                    if not rsx_path:
                        continue
                    value = item.tli_value.replace("{sequential_number}", str(index))
                    parts = rsx_path.split("_")
                    try:
                        idx = parts.index("ItemLevel")
                        sub_parts = parts[idx + 1 :]
                    except ValueError:
                        sub_parts = parts
                    items_for_level.append((item, sub_parts, value))

                self._apply_detail_items_with_extra_records(item_level, items_for_level)

    def _apply_tli_sources_810(self, root: ET.Element, max_lines: int) -> None:
        """Apply TLI Sources values to Invoice XML, including Header/Address grouping."""
        rsx_settings = self.artifact_settings.get("rsx_810_settings", {})
        tli_sources = rsx_settings.get("tli_sources", {})
        if not tli_sources:
            return

        header_items: List[Item] = []
        detail_items: List[Item] = []
        for item in self.parsed_items:
            item_id = getattr(item, "item_properties_id", None)
            rsx_path = getattr(item, "rsx_path_810", "")
            if not rsx_path or not item_id:
                continue
            if not tli_sources.get(str(item_id), False):
                continue
            if item.is_on_detail_level:
                detail_items.append(item)
            else:
                header_items.append(item)

        self._apply_header_tli_items_810(root, header_items)
        self._apply_detail_tli_items_810(root, detail_items, max_lines)

    def _apply_header_tli_items_810(self, root: ET.Element, header_items: List[Item]) -> None:
        """Apply header-level TLI items for Invoice with Extra Record grouping support."""

        def apply_normal_item(item: Item, path_parts: List[str]) -> None:
            """Apply a single header item without Extra Record grouping."""
            self._set_xml_value_by_path(root, path_parts, item.tli_value)

        self._apply_header_items_with_extra_records(
            root=root,
            header_items=header_items,
            rsx_attr_name="rsx_path_810",
            doc_root_name="Invoice",
            apply_normal_item=apply_normal_item,
        )

    def _apply_detail_items_with_extra_records(
        self,
        container: ET.Element,
        items_for_container: List[tuple],
    ) -> None:
        """Apply detail-level items inside a single LineItem/ItemLevel with Extra Record grouping.

        items_for_container is a list of tuples (item, sub_parts, value), where
        sub_parts is the RSX path relative to the container element (for
        example ["ProductOrItemDescription", "ProductDescription"]). Items
        that have extra_record_defining_rsx_tag and extra_record_defining_qual
        set will be grouped so that for each unique combination of:

        - parent path (up to the repeating container element),
        - extra_record_defining_rsx_tag (qualifier element name),
        - extra_record_defining_qual (qualifier value),

        all values are written into the same repeated element instance inside
        this LineItem/ItemLevel.
        """
        if not items_for_container:
            return

        grouped = {}
        normal_items = []

        for item, sub_parts, value in items_for_container:
            if not sub_parts:
                normal_items.append((item, sub_parts, value))
                continue

            extra_tag = (getattr(item, "extra_record_defining_rsx_tag", "") or "").strip()
            extra_qual = (getattr(item, "extra_record_defining_qual", "") or "").strip()

            if extra_tag and extra_qual and len(sub_parts) >= 2:
                parent_parts = sub_parts[:-1]
                key = (tuple(parent_parts), extra_tag, extra_qual)
                grouped.setdefault(key, []).append((item, sub_parts, value))
            else:
                normal_items.append((item, sub_parts, value))

        # Handle grouped items with Extra Record semantics
        for (parent_parts_tuple, extra_tag, extra_qual), items_for_group in grouped.items():
            parent_parts = list(parent_parts_tuple)
            if not parent_parts:
                continue

            repeated_tag = parent_parts[-1]
            container_parent_parts = parent_parts[:-1]

            parent_elem = self._find_element_by_path(container, container_parent_parts)
            if parent_elem is None:
                continue

            existing = [
                child
                for child in list(parent_elem)
                if isinstance(child.tag, str) and child.tag.endswith(repeated_tag)
            ]

            # Try to find an existing repeated element with matching qualifier value
            container_elem = None
            for candidate in existing:
                qual_elem = self._find_element_by_path(candidate, [extra_tag])
                if qual_elem is not None and (qual_elem.text or "").strip() == extra_qual:
                    container_elem = candidate
                    break

            # If not found, create a new repeated element
            if container_elem is None:
                if existing:
                    template_elem = existing[0]
                else:
                    template_elem = ET.Element(repeated_tag)
                container_elem = copy.deepcopy(template_elem)
                parent_elem.append(container_elem)

            # Set defining qualifier element
            self._set_xml_value_by_path(container_elem, [extra_tag], extra_qual)

            # Apply all values from this group inside the same repeated element
            for grouped_item, full_sub_parts, grouped_value in items_for_group:
                try:
                    idx = full_sub_parts.index(repeated_tag)
                    inner_parts = full_sub_parts[idx + 1 :]
                except ValueError:
                    inner_parts = full_sub_parts

                if not inner_parts:
                    continue

                if len(inner_parts) == 1 and inner_parts[0] == extra_tag:
                    continue

                self._set_xml_value_by_path(container_elem, inner_parts, grouped_value)

        # Apply non-grouped items normally
        for item, sub_parts, value in normal_items:
            if not sub_parts:
                continue
            self._set_xml_value_by_path(container, sub_parts, value)

    def _apply_header_items_with_extra_records(
        self,
        root: ET.Element,
        header_items: List[Item],
        rsx_attr_name: str,
        doc_root_name: str,
        apply_normal_item,
    ) -> None:
        """Apply header items with support for Extra Record grouping.

        For each header item whose extra_record_defining_rsx_tag and
        extra_record_defining_qual are filled, we:
        - build the parent path from its RSX path (up to the repeating
          container element),
        - look for an existing repeated element at that path where the
          defining element (extra_record_defining_rsx_tag) already has the
          required value (extra_record_defining_qual),
        - if found, write this item's value into that repeat;
          otherwise, create a new repeat, set the defining element, and
          then write all grouped items into it.
        """
        if not header_items:
            return

        # Split items into Extra Record groups and regular header items
        grouped = {}
        normal_items = []

        for item in header_items:
            rsx_path = getattr(item, rsx_attr_name, "") or ""
            if not rsx_path:
                continue

            path_parts = rsx_path.split("_")
            if path_parts and path_parts[0] == doc_root_name:
                path_parts = path_parts[1:]

            extra_tag = (getattr(item, "extra_record_defining_rsx_tag", "") or "").strip()
            extra_qual = (getattr(item, "extra_record_defining_qual", "") or "").strip()

            # Only items that have both Extra Record fields and at least
            # two path parts (so there is a parent container) participate
            # in grouping. Others are treated as regular header items.
            if extra_tag and extra_qual and len(path_parts) >= 2:
                parent_parts = path_parts[:-1]
                key = (tuple(parent_parts), extra_tag, extra_qual)
                grouped.setdefault(key, []).append((item, path_parts))
            else:
                normal_items.append((item, path_parts))

        # For each Extra Record group create or reuse a repeated container
        # element under its parent and write all values into that container.
        for (parent_parts_tuple, extra_tag, extra_qual), items_for_group in grouped.items():
            parent_parts = list(parent_parts_tuple)
            if not parent_parts:
                continue

            repeated_tag = parent_parts[-1]
            container_parent_parts = parent_parts[:-1]

            parent_elem = self._find_element_by_path(root, container_parent_parts)
            if parent_elem is None:
                continue

            existing = [
                child
                for child in list(parent_elem)
                if isinstance(child.tag, str) and child.tag.endswith(repeated_tag)
            ]

            # First, try to find an existing repeated element where the
            # defining qualifier element already has the required value.
            container_elem = None
            for candidate in existing:
                qual_elem = self._find_element_by_path(candidate, [extra_tag])
                if qual_elem is not None and (qual_elem.text or "").strip() == extra_qual:
                    container_elem = candidate
                    break

            # If not found, create a new repeated element (clone template
            # if available, otherwise create a bare element) and append it.
            if container_elem is None:
                if existing:
                    template_elem = existing[0]
                else:
                    # Fallback: create a bare element if the template is
                    # missing. In this rare case nested paths may not be
                    # populated, but we avoid crashing.
                    template_elem = ET.Element(repeated_tag)
                container_elem = copy.deepcopy(template_elem)
                parent_elem.append(container_elem)

            # First, set the qualifier element that defines this Extra
            # Record group (for example AddressTypeCode = ST / VN).
            self._set_xml_value_by_path(container_elem, [extra_tag], extra_qual)

            # Then, apply all TLI values that belong to this group into
            # the same repeated container.
            for grouped_item, full_path_parts in items_for_group:
                try:
                    idx = full_path_parts.index(repeated_tag)
                    sub_parts = full_path_parts[idx + 1 :]
                except ValueError:
                    sub_parts = full_path_parts

                # Nothing to set inside this container
                if not sub_parts:
                    continue

                # Skip the defining element itself – its value comes from
                # extra_record_defining_qual, not from TLI value.
                if len(sub_parts) == 1 and sub_parts[0] == extra_tag:
                    continue

                self._set_xml_value_by_path(container_elem, sub_parts, grouped_item.tli_value)

        # Finally, apply all remaining header items without Extra Record
        # grouping using the document-specific logic.
        for normal_item, normal_path_parts in normal_items:
            apply_normal_item(normal_item, normal_path_parts)

    def _apply_detail_tli_items_810(self, root: ET.Element, detail_items: List[Item], max_lines: int) -> None:
        """Apply detail-level TLI items for each Invoice LineItem, substituting {sequential_number}."""
        if not detail_items:
            return

        line_items = [elem for elem in root.iter() if isinstance(elem.tag, str) and elem.tag.endswith("LineItem")]
        if not line_items:
            return

        for index, line_item in enumerate(line_items, start=1):
            items_for_line = []
            for item in detail_items:
                rsx_path = getattr(item, "rsx_path_810", "")
                if not rsx_path:
                    continue
                value = item.tli_value.replace("{sequential_number}", str(index))
                parts = rsx_path.split("_")
                try:
                    idx = parts.index("LineItem")
                    sub_parts = parts[idx + 1 :]
                except ValueError:
                    sub_parts = parts
                items_for_line.append((item, sub_parts, value))

            self._apply_detail_items_with_extra_records(line_item, items_for_line)

    def _find_element_by_path(self, root: ET.Element, path_parts: List[str]) -> Optional[ET.Element]:
        """Navigate XML by tag parts and return the last element, if found."""
        if not path_parts:
            return root

        current = root
        for part in path_parts:
            found = None
            for child in current:
                if isinstance(child.tag, str) and child.tag.endswith(part):
                    found = child
                    break
            if found is None:
                return None
            current = found
        return current

    def _set_xml_value_by_path(self, root: ET.Element, path_parts: List[str], value: str) -> None:
        """Navigate XML by tag parts and set text value on last element."""
        if not path_parts:
            return

        current = root
        for part in path_parts:
            found = None
            for child in current:
                if isinstance(child.tag, str) and child.tag.endswith(part):
                    found = child
                    break
            if found is None:
                return
            current = found
        current.text = value

    def _prune_empty_elements(self, element: ET.Element) -> bool:
        """Recursively remove elements that have no text and no children.

        Returns True if the element itself is empty and should be pruned by caller.
        """
        # Work on a copy of children list because we may remove elements
        for child in list(element):
            if isinstance(child.tag, str):  # Skip comments
                empty = self._prune_empty_elements(child)
                if empty:
                    element.remove(child)

        is_empty = (element.text is None or not str(element.text).strip()) and len(element) == 0
        return is_empty

    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Fallback pretty-printer for XML when ET.indent is unavailable.

        Uses one tab per nesting level and keeps opening/closing tags aligned.
        """
        indent_char = "\t"
        i = "\n" + level * indent_char
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent_char
            for child in elem:
                self._indent_xml(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def _apply_charges_allowances_810(self, root: ET.Element) -> None:
        """Populate Invoice/Header ChargesAllowances with fixed test values when enabled."""
        charges_elem = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("ChargesAllowances"):
                # First ChargesAllowances under Header is the header-level block
                charges_elem = elem
                break
        if charges_elem is None:
            return

        values = {
            "AllowChrgIndicator": "C",
            "AllowChrgCode": "D240",
            "AllowChrgAmt": "200",
            "AllowChrgHandlingDescription": "SAC15 Description",
        }

        for child in list(charges_elem):
            if not isinstance(child.tag, str):
                continue
            name = child.tag.split("}")[-1]
            if name in values:
                child.text = values[name]
            else:
                child.text = None

    def _apply_taxes_810(self, root: ET.Element) -> None:
        """Populate Invoice/Header Taxes with fixed test values when enabled."""
        taxes_elem = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("Taxes"):
                taxes_elem = elem
                break
        if taxes_elem is None:
            return

        values = {
            "TaxTypeCode": "GS",
            "TaxAmount": "100",
        }

        for child in list(taxes_elem):
            if not isinstance(child.tag, str):
                continue
            name = child.tag.split("}")[-1]
            if name in values:
                child.text = values[name]
            else:
                child.text = None

    def _apply_total_amount_810(self, root: ET.Element) -> None:
        """Calculate Summary/TotalAmount as sum(InvoiceQty * PurchasePrice) across LineItems."""
        total = 0.0

        # Iterate through all LineItem/InvoiceLine blocks
        for line_item in root.iter():
            if not (isinstance(line_item.tag, str) and line_item.tag.endswith("LineItem")):
                continue

            invoice_line = None
            for child in line_item:
                if isinstance(child.tag, str) and child.tag.endswith("InvoiceLine"):
                    invoice_line = child
                    break
            if invoice_line is None:
                continue

            qty_val = None
            price_val = None
            for child in invoice_line:
                if not isinstance(child.tag, str):
                    continue
                if child.tag.endswith("InvoiceQty"):
                    qty_val = child.text
                elif child.tag.endswith("PurchasePrice"):
                    price_val = child.text

            try:
                qty = float(qty_val) if qty_val is not None and qty_val.strip() else 0.0
            except ValueError:
                qty = 0.0
            try:
                price = float(price_val) if price_val is not None and price_val.strip() else 0.0
            except ValueError:
                price = 0.0

            total += qty * price

        # Set Summary/TotalAmount
        summary_elem = None
        total_amount_elem = None
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.endswith("Summary"):
                summary_elem = elem
                break
        if summary_elem is None:
            return

        for child in summary_elem:
            if isinstance(child.tag, str) and child.tag.endswith("TotalAmount"):
                total_amount_elem = child
                break
        if total_amount_elem is None:
            return

        # Adjust total with Taxes and ChargesAllowances if corresponding options are enabled
        rsx_settings = self.artifact_settings.get("rsx_810_settings", {})
        if rsx_settings.get("gen_taxes", True):
            total += 100.0
        if rsx_settings.get("gen_charges", True):
            total += 200.0

        total_amount_elem.text = f"{total:.2f}"

    def _generate_csv_test_files(self, output_dir: Path) -> None:
        """Generate CSV test files for inbound documents"""
        t = TRANSLATIONS[self.current_language]
        
        try:
            # Create subdirectory for CSV files
            csv_output_dir = output_dir / "CSV max test files (inbound docs)"
            csv_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate file for each scenario with CSV test file
            for scenario in self.parsed_scenarios:
                if scenario.csv_test_file and scenario.csv_design_filename:
                    # Use original csv_design_filename without adding "_test" suffix
                    output_filename = scenario.csv_design_filename
                    output_filepath = csv_output_dir / output_filename
                    
                    # Write CSV test file
                    output_filepath.write_text(scenario.csv_test_file, encoding="utf-8")
        except Exception as e:
            t = TRANSLATIONS[self.current_language]
            QMessageBox.warning(
                self,
                t["error"],
                f"Error generating CSV test files:\n{str(e)}",
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
        if hasattr(self, "open_output_button"):
            self.open_output_button.setText(t.get("open_output_folder", "Open output folder"))

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
        
        # Update artifact group and checkboxes
        self.ui_elements["artifacts_group_title"].setTitle(t.get("create_artifacts", "Create Artifacts"))
        for checkbox_info in self.artifact_checkboxes:
            cb = checkbox_info["checkbox"]
            key = checkbox_info["key"]
            label_key = key
            cb.setText(t.get(label_key, label_key))

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

        # Apply CSV inbound item settings (disabled items will produce empty values)
        items_for_csv = self._get_csv_items_for_generation() if self.spreadsheet_parse_success else []

        success, error_message = parser.parse(
            self.csv_archive_path,
            self.parsed_scenarios,
            items_for_csv
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

    def _get_csv_inbound_enabled_mask(self) -> List[bool]:
        """Return a boolean mask for which Items are enabled for CSV inbound generation.

        If settings are missing or length does not match, all items are treated as enabled.
        """
        total = len(self.parsed_items)
        if total == 0:
            return []

        settings = self.artifact_settings.get("csv_inbound_settings", {})
        saved = settings.get("enabled_items")

        if isinstance(saved, list) and len(saved) == total:
            return [bool(v) for v in saved]

        # Default: all items enabled
        return [True] * total

    def _get_csv_items_for_generation(self) -> List[Item]:
        """Return a cloned Items list for CSV generation.

        Disabled items keep their position but have empty tli_value so that
        CSV structure (number of columns) remains unchanged, and those
        positions become just empty values between commas.
        """
        if not self.parsed_items:
            return []

        mask = self._get_csv_inbound_enabled_mask()

        # Deep-copy items so we don't mutate original parsed_items
        items_copy: List[Item] = copy.deepcopy(self.parsed_items)

        for idx, enabled in enumerate(mask):
            if not enabled and idx < len(items_copy):
                # Empty value for disabled items
                items_copy[idx].tli_value = ""

        return items_copy
    
    def _regenerate_csv_test_files(self) -> None:
        """Regenerate CSV test files for all scenarios"""
        if not self.parsed_scenarios or not self.parsed_items:
            return
        
        parser = CSVArchiveParser(self.current_language)
        errors = []
        
        # Prepare items list for CSV generation, applying CSV inbound settings
        items_for_csv = self._get_csv_items_for_generation()

        for scenario in self.parsed_scenarios:
            if not scenario.csv_design:
                continue
            
            try:
                import csv
                import io
                csv_reader = csv.reader(io.StringIO(scenario.csv_design))
                csv_rows = list(csv_reader)
                
                csv_test_content = parser._generate_csv_test_file(csv_rows, items_for_csv, errors)
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

