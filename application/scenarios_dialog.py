"""Dialog for displaying scenario information"""

from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)

from application.tommm_parser import InboundDocScenario
from application.translations import TRANSLATIONS


class ScenariosInfoDialog(QDialog):
    """Dialog for displaying scenario information"""
    
    def __init__(
        self, 
        scenarios: List[InboundDocScenario], 
        current_language: str, 
        csv_parse_success: bool = False,
        parent=None
    ):
        """
        Initialize dialog
        
        Args:
            scenarios: List of InboundDocScenario objects
            current_language: Current UI language
            csv_parse_success: Whether CSV archive was successfully parsed
            parent: Parent widget
        """
        super().__init__(parent)
        self.scenarios = scenarios
        self.current_language = current_language
        self.csv_parse_success = csv_parse_success
        self.t = TRANSLATIONS.get(current_language, TRANSLATIONS["UA"])
        self.setWindowTitle(self.t.get("scenarios_info_title", "Scenario Information"))
        # Width reduced by 20% (1200 * 0.8 = 960), height by 30% (600 * 1.3 = 780)
        self.setMinimumSize(960, 780)
        self.create_ui()
    
    def _wrap_text(self, text: str, max_length: int = 30) -> str:
        """
        Wrap text to multiple lines if it exceeds max_length
        
        Args:
            text: Text to wrap
            max_length: Maximum length per line
            
        Returns:
            Text with line breaks inserted
        """
        if len(text) <= max_length:
            return text
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_length:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return "\n".join(lines)
    
    def create_ui(self) -> None:
        """Create user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        scroll = QWidget()
        scroll_layout = QVBoxLayout()
        scroll.setLayout(scroll_layout)
        
        # Field descriptions mapping
        field_descriptions = {
            "name": self.t.get("scenario_name", "Name"),
            "key": self.t.get("scenario_key", "Key"),
            "document_number": self.t.get("scenario_document_number", "Document Number"),
            "tset_code": self.t.get("scenario_tset_code", "TSET Code"),
            "number_of_tli": self.t.get("scenario_number_of_tli", "Number of TLI"),
            "number_of_lines": self.t.get("scenario_number_of_lines", "Number of Lines"),
            "includes_855_docs": self.t.get("scenario_includes_855_docs", "Includes 855 Docs"),
            "includes_856_docs": self.t.get("scenario_includes_856_docs", "Includes 856 Docs"),
            "includes_810_docs": self.t.get("scenario_includes_810_docs", "Includes 810 Docs"),
            "is_changed_by_850_scenario": self.t.get("scenario_is_changed_by_850_scenario", "Is Changed by 850 Scenario"),
            "is_changer_850": self.t.get("scenario_is_changer_850", "Is Changer 850"),
            "is_consolidated": self.t.get("scenario_is_consolidated", "Is Consolidated"),
            "csv_design_filename": self.t.get("scenario_csv_design_filename", "CSV Design File Name"),
            "csv_design": self.t.get("scenario_csv_design", "CSV Design"),
            "csv_test_file": self.t.get("scenario_csv_test_file", "CSV Test File"),
        }
        
        # Display each scenario
        for idx, scenario in enumerate(self.scenarios):
            # Create collapsible group box with compact header (like ItemsInfoDialog)
            scenario_group = QGroupBox()
            scenario_group.setCheckable(True)
            scenario_group.setChecked(False)  # Collapsed by default

            # Header with basic info (always visible): number and name on first line
            header_text = f"{idx + 1}. {scenario.name}"
            scenario_group.setTitle(header_text)

            # Match checkbox/border style with ItemsInfoDialog
            scenario_group.setStyleSheet(
                "QGroupBox {"
                "    font-weight: bold;"
                "    border: 2px solid #cccccc;"
                "    border-radius: 5px;"
                "    margin-top: 3px;"
                "    margin-bottom: 3px;"
                "    padding-top: 5px;"
                "    padding-bottom: 3px;"
                "}"
                "QGroupBox::indicator {"
                "    width: 20px;"
                "    height: 20px;"
                "}"
                "QGroupBox::indicator:unchecked {"
                "    image: none;"
                "    background-color: #e0e0e0;"
                "    border: 2px solid #999999;"
                "    border-radius: 3px;"
                "}"
                "QGroupBox::indicator:checked {"
                "    image: none;"
                "    background-color: #4CAF50;"
                "    border: 2px solid #2e7d32;"
                "    border-radius: 3px;"
                "}"
                "QGroupBox::indicator:unchecked:hover {"
                "    background-color: #d0d0d0;"
                "}"
                "QGroupBox::indicator:checked:hover {"
                "    background-color: #45a049;"
                "}"
            )

            scenario_layout = QVBoxLayout()
            # similar compact margins as in ItemsInfoDialog
            scenario_layout.setContentsMargins(28, 8, 8, 2)
            scenario_layout.setSpacing(0)
            scenario_group.setLayout(scenario_layout)

            # Second line with key and document number (always visible in collapsed view)
            # Compact, aligned with title text
            second_line_layout = QHBoxLayout()
            second_line_layout.setContentsMargins(18, 3, 0, 0)
            second_line_layout.setSpacing(0)
            key_doc_label = QLabel(f"{self.t.get('scenario_key', 'Key')}={scenario.key}, {self.t.get('scenario_document_number', 'Document Number')}={scenario.document_number}")
            key_doc_label.setStyleSheet("color: #666666; font-size: 9pt; margin: 0px; padding: 0px;")
            second_line_layout.addWidget(key_doc_label)
            second_line_layout.addStretch()
            scenario_layout.addLayout(second_line_layout)
            
            # Expanded content (hidden by default, shown when checked)
            expanded_widget = QWidget()
            expanded_layout = QVBoxLayout()
            expanded_widget.setLayout(expanded_layout)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.horizontalHeader().setVisible(False)
            table.verticalHeader().setVisible(False)
            table.setShowGrid(True)
            table.setAlternatingRowColors(True)
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

            current_row = 0

            def add_simple_row(label_text: str, value_text: str) -> None:
                nonlocal current_row
                table.insertRow(current_row)
                # Keep description in a single line
                desc_item = QTableWidgetItem(label_text)
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(current_row, 0, desc_item)
                value_item = QTableWidgetItem(value_text)
                value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(current_row, 1, value_item)
                current_row += 1

            def add_button_row(label_text: str, content: str, title: str) -> None:
                nonlocal current_row
                table.insertRow(current_row)
                # Keep description in a single line
                desc_item = QTableWidgetItem(label_text)
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(current_row, 0, desc_item)
                button = QPushButton(self.t.get("show_content", "Show Content"))
                button.setFixedWidth(140)
                button.setFixedHeight(24)
                button.clicked.connect(
                    lambda checked, text=content, ttitle=title: self._show_csv_content(text, ttitle)
                )
                table.setCellWidget(current_row, 1, button)
                current_row += 1

            # Name field
            add_simple_row(field_descriptions["name"], scenario.name)

            # Key field
            add_simple_row(field_descriptions["key"], scenario.key)

            # Document number field
            add_simple_row(field_descriptions["document_number"], str(scenario.document_number))

            # key_with_date if present
            if scenario.key_with_date:
                add_simple_row(self.t.get("scenario_key_with_date", "Key (with date mask)"), scenario.key_with_date)

            # TSET Code and basic counts (only if CSV parsing was successful)
            if self.csv_parse_success:
                add_simple_row(field_descriptions["tset_code"], str(scenario.tset_code) if scenario.tset_code else "")
                add_simple_row(field_descriptions["number_of_tli"], str(scenario.number_of_tli))
                add_simple_row(field_descriptions["number_of_lines"], str(scenario.number_of_lines))

            # Flags (always visible)
            add_simple_row(field_descriptions["includes_855_docs"], "Yes" if scenario.includes_855_docs else "No")
            add_simple_row(field_descriptions["includes_856_docs"], "Yes" if scenario.includes_856_docs else "No")
            add_simple_row(field_descriptions["includes_810_docs"], "Yes" if scenario.includes_810_docs else "No")
            add_simple_row(field_descriptions["is_changed_by_850_scenario"], "Yes" if scenario.is_changed_by_850_scenario else "No")
            add_simple_row(field_descriptions["is_changer_850"], "Yes" if scenario.is_changer_850 else "No")
            add_simple_row(field_descriptions["is_consolidated"], "Yes" if scenario.is_consolidated else "No")

            # CSV design filename (from archive) if available
            if self.csv_parse_success and getattr(scenario, "csv_design_filename", ""):
                add_simple_row(field_descriptions["csv_design_filename"], scenario.csv_design_filename)

            # CSV Design content button
            if self.csv_parse_success and scenario.csv_design:
                add_button_row(field_descriptions["csv_design"], scenario.csv_design, field_descriptions["csv_design"])

            # CSV Test File content button
            if self.csv_parse_success and scenario.csv_test_file:
                add_button_row(field_descriptions["csv_test_file"], scenario.csv_test_file, field_descriptions["csv_test_file"])

            # Ensure the whole table is visible (no inner scrolling) and rows have equal minimal height
            table.setWordWrap(False)
            table.resizeRowsToContents()
            base_height = table.fontMetrics().height() + 8
            for r in range(table.rowCount()):
                if table.rowHeight(r) < base_height:
                    table.setRowHeight(r, base_height)

            # Make first column slightly narrower (about 25% less than before)
            table.setColumnWidth(0, 270)

            header_height = table.horizontalHeader().height() if table.horizontalHeader().isVisible() else 0
            total_height = header_height + 2 * table.frameWidth()
            for r in range(table.rowCount()):
                total_height += table.rowHeight(r)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table.setMinimumHeight(total_height)
            table.setMaximumHeight(total_height)

            expanded_layout.addWidget(table)
            # Add expanded widget to group box
            scenario_layout.addWidget(expanded_widget)
            
            # Connect checkbox to show/hide expanded content
            scenario_group.toggled.connect(
                lambda checked, widget=expanded_widget: widget.setVisible(checked)
            )
            
            # Initially hide expanded content
            expanded_widget.setVisible(False)
            
            scroll_layout.addWidget(scenario_group)
        
        scroll_layout.addStretch()
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _show_csv_content(self, content: str, title: str) -> None:
        """Show CSV content in a separate dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(900, 600)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.exec()
