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
)

from application.tnc_parser import InboundDocScenario
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
            
            # Name field
            name_layout = QHBoxLayout()
            name_label_text = self._wrap_text(field_descriptions['name'])
            name_label = QLabel(name_label_text)
            name_label.setMinimumWidth(200)
            name_label.setWordWrap(True)
            name_value = QLabel(scenario.name)
            name_layout.addWidget(name_label)
            name_layout.addWidget(name_value)
            name_layout.addStretch()
            expanded_layout.addLayout(name_layout)
            
            # Key field (moved to second line in expanded view)
            key_layout = QHBoxLayout()
            key_label_text = self._wrap_text(field_descriptions['key'])
            key_label = QLabel(key_label_text)
            key_label.setMinimumWidth(200)
            key_label.setWordWrap(True)
            key_value = QLabel(scenario.key)
            key_layout.addWidget(key_label)
            key_layout.addWidget(key_value)
            key_layout.addStretch()
            expanded_layout.addLayout(key_layout)
            
            # Document number field (moved to second line in expanded view)
            doc_num_layout = QHBoxLayout()
            doc_num_label_text = self._wrap_text(field_descriptions['document_number'])
            doc_num_label = QLabel(doc_num_label_text)
            doc_num_label.setMinimumWidth(200)
            doc_num_label.setWordWrap(True)
            doc_num_value = QLabel(str(scenario.document_number))
            doc_num_layout.addWidget(doc_num_label)
            doc_num_layout.addWidget(doc_num_value)
            doc_num_layout.addStretch()
            expanded_layout.addLayout(doc_num_layout)
            
            # Display key_with_date only if it's not empty (always available)
            if scenario.key_with_date:
                key_with_date_layout = QHBoxLayout()
                key_with_date_label_text = self._wrap_text(self.t.get('scenario_key_with_date', 'Key (with date mask)'))
                key_with_date_label = QLabel(key_with_date_label_text)
                key_with_date_label.setMinimumWidth(200)
                key_with_date_label.setWordWrap(True)
                key_with_date_value = QLabel(scenario.key_with_date)
                key_with_date_layout.addWidget(key_with_date_label)
                key_with_date_layout.addWidget(key_with_date_value)
                key_with_date_layout.addStretch()
                expanded_layout.addLayout(key_with_date_layout)
            
            # TSET Code and basic counts (only if CSV parsing was successful)
            if self.csv_parse_success:
                # TSET Code
                tset_layout = QHBoxLayout()
                tset_label_text = self._wrap_text(field_descriptions['tset_code'])
                tset_label = QLabel(tset_label_text)
                tset_label.setMinimumWidth(200)
                tset_label.setWordWrap(True)
                tset_value = QLabel(str(scenario.tset_code) if scenario.tset_code else "")
                tset_layout.addWidget(tset_label)
                tset_layout.addWidget(tset_value)
                tset_layout.addStretch()
                expanded_layout.addLayout(tset_layout)
                
                # Number of TLI
                tli_layout = QHBoxLayout()
                tli_label_text = self._wrap_text(field_descriptions['number_of_tli'])
                tli_label = QLabel(tli_label_text)
                tli_label.setMinimumWidth(200)
                tli_label.setWordWrap(True)
                tli_value = QLabel(str(scenario.number_of_tli))
                tli_layout.addWidget(tli_label)
                tli_layout.addWidget(tli_value)
                tli_layout.addStretch()
                expanded_layout.addLayout(tli_layout)
                
                # Number of Lines
                lines_layout = QHBoxLayout()
                lines_label_text = self._wrap_text(field_descriptions['number_of_lines'])
                lines_label = QLabel(lines_label_text)
                lines_label.setMinimumWidth(200)
                lines_label.setWordWrap(True)
                lines_value = QLabel(str(scenario.number_of_lines))
                lines_layout.addWidget(lines_label)
                lines_layout.addWidget(lines_value)
                lines_layout.addStretch()
                expanded_layout.addLayout(lines_layout)

            # These flags should be visible even without successful CSV parsing
            # Includes 855 Docs
            includes_855_layout = QHBoxLayout()
            includes_855_label_text = self._wrap_text(field_descriptions['includes_855_docs'])
            includes_855_label = QLabel(includes_855_label_text)
            includes_855_label.setMinimumWidth(200)
            includes_855_label.setWordWrap(True)
            includes_855_value = QLabel("Yes" if scenario.includes_855_docs else "No")
            includes_855_layout.addWidget(includes_855_label)
            includes_855_layout.addWidget(includes_855_value)
            includes_855_layout.addStretch()
            expanded_layout.addLayout(includes_855_layout)

            # Includes 856 Docs
            includes_856_layout = QHBoxLayout()
            includes_856_label_text = self._wrap_text(field_descriptions['includes_856_docs'])
            includes_856_label = QLabel(includes_856_label_text)
            includes_856_label.setMinimumWidth(200)
            includes_856_label.setWordWrap(True)
            includes_856_value = QLabel("Yes" if scenario.includes_856_docs else "No")
            includes_856_layout.addWidget(includes_856_label)
            includes_856_layout.addWidget(includes_856_value)
            includes_856_layout.addStretch()
            expanded_layout.addLayout(includes_856_layout)

            # Includes 810 Docs
            includes_810_layout = QHBoxLayout()
            includes_810_label_text = self._wrap_text(field_descriptions['includes_810_docs'])
            includes_810_label = QLabel(includes_810_label_text)
            includes_810_label.setMinimumWidth(200)
            includes_810_label.setWordWrap(True)
            includes_810_value = QLabel("Yes" if scenario.includes_810_docs else "No")
            includes_810_layout.addWidget(includes_810_label)
            includes_810_layout.addWidget(includes_810_value)
            includes_810_layout.addStretch()
            expanded_layout.addLayout(includes_810_layout)

            # Is Changed by 850 Scenario
            changed_850_layout = QHBoxLayout()
            changed_850_label_text = self._wrap_text(field_descriptions['is_changed_by_850_scenario'])
            changed_850_label = QLabel(changed_850_label_text)
            changed_850_label.setMinimumWidth(200)
            changed_850_label.setWordWrap(True)
            changed_850_value = QLabel("Yes" if scenario.is_changed_by_850_scenario else "No")
            changed_850_layout.addWidget(changed_850_label)
            changed_850_layout.addWidget(changed_850_value)
            changed_850_layout.addStretch()
            expanded_layout.addLayout(changed_850_layout)

            # Is Changer 850
            changer_850_layout = QHBoxLayout()
            changer_850_label_text = self._wrap_text(field_descriptions['is_changer_850'])
            changer_850_label = QLabel(changer_850_label_text)
            changer_850_label.setMinimumWidth(200)
            changer_850_label.setWordWrap(True)
            changer_850_value = QLabel("Yes" if scenario.is_changer_850 else "No")
            changer_850_layout.addWidget(changer_850_label)
            changer_850_layout.addWidget(changer_850_value)
            changer_850_layout.addStretch()
            expanded_layout.addLayout(changer_850_layout)

            # Is Consolidated
            consolidated_layout = QHBoxLayout()
            consolidated_label_text = self._wrap_text(field_descriptions['is_consolidated'])
            consolidated_label = QLabel(consolidated_label_text)
            consolidated_label.setMinimumWidth(200)
            consolidated_label.setWordWrap(True)
            consolidated_value = QLabel("Yes" if scenario.is_consolidated else "No")
            consolidated_layout.addWidget(consolidated_label)
            consolidated_layout.addWidget(consolidated_value)
            consolidated_layout.addStretch()
            expanded_layout.addLayout(consolidated_layout)

            # CSV design filename (from archive) if available, show after consolidated flag
            if self.csv_parse_success and getattr(scenario, "csv_design_filename", ""):
                csv_name_layout = QHBoxLayout()
                csv_name_label_text = self._wrap_text(field_descriptions['csv_design_filename'])
                csv_name_label = QLabel(csv_name_label_text)
                csv_name_label.setMinimumWidth(200)
                csv_name_label.setWordWrap(True)
                csv_name_value = QLabel(scenario.csv_design_filename)
                csv_name_layout.addWidget(csv_name_label)
                csv_name_layout.addWidget(csv_name_value)
                csv_name_layout.addStretch()
                expanded_layout.addLayout(csv_name_layout)

            # CSV Design field with button (show only if content exists and CSV parsing succeeded)
            if self.csv_parse_success and scenario.csv_design:
                csv_design_layout = QHBoxLayout()
                csv_design_label_text = self._wrap_text(field_descriptions['csv_design'])
                csv_design_label = QLabel(csv_design_label_text)
                csv_design_label.setMinimumWidth(200)
                csv_design_label.setWordWrap(True)
                csv_design_button = QPushButton(self.t.get("show_content", "Show Content"))
                # Capture content and title in local variables for proper closure
                csv_content = scenario.csv_design
                csv_title = field_descriptions['csv_design']
                csv_design_button.clicked.connect(
                    lambda checked, content=csv_content, title=csv_title: self._show_csv_content(content, title)
                )
                csv_design_layout.addWidget(csv_design_label)
                csv_design_layout.addWidget(csv_design_button)
                csv_design_layout.addStretch()
                expanded_layout.addLayout(csv_design_layout)
            
            # CSV Test File field with button (show only if content exists and CSV parsing succeeded)
            if self.csv_parse_success and scenario.csv_test_file:
                csv_test_layout = QHBoxLayout()
                csv_test_label_text = self._wrap_text(field_descriptions['csv_test_file'])
                csv_test_label = QLabel(csv_test_label_text)
                csv_test_label.setMinimumWidth(200)
                csv_test_label.setWordWrap(True)
                csv_test_button = QPushButton(self.t.get("show_content", "Show Content"))
                # Capture content and title in local variables for proper closure
                test_content = scenario.csv_test_file
                test_title = field_descriptions['csv_test_file']
                csv_test_button.clicked.connect(
                    lambda checked, content=test_content, title=test_title: self._show_csv_content(content, title)
                )
                csv_test_layout.addWidget(csv_test_label)
                csv_test_layout.addWidget(csv_test_button)
                csv_test_layout.addStretch()
                expanded_layout.addLayout(csv_test_layout)
            
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
