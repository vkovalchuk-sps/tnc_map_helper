"""Dialogs for artifact generation settings"""

from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QGridLayout,
    QWidget,
)

from application.translations import TRANSLATIONS


class XTLSettingsDialog(QDialog):
    """Dialog for XTL (850/860) generation settings"""

    def __init__(self, language: str, doc_type: str = "850", previous_settings: Dict = None, parent=None):
        """
        Initialize XTL settings dialog
        
        Args:
            language: Current UI language
            doc_type: Document type ("850" or "860")
            previous_settings: Previously saved settings dict
            parent: Parent widget
        """
        super().__init__(parent)
        self.language = language
        self.doc_type = doc_type
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])
        
        # Use previous settings or defaults
        if previous_settings is None:
            previous_settings = {}
        
        title = f"poRsxRead.xtl" if doc_type == "850" else "pcRsxWrite.xtl"
        self.setWindowTitle(f"{title} - {self.t.get('settings', 'Settings')}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create checkboxes with previous values
        self.gen_tli_fields = QCheckBox(self.t.get("gen_tli_fields", "Generate TLI fields"))
        self.gen_tli_fields.setChecked(previous_settings.get("gen_tli_fields", True))
        
        self.gen_order_model = QCheckBox(self.t.get("gen_get_order_model", "Generate getOrderManagementModel() method"))
        self.gen_order_model.setChecked(previous_settings.get("gen_order_model", True))
        
        self.gen_populate_methods = QCheckBox(self.t.get("gen_populate_methods", "Generate populate methods"))
        self.gen_populate_methods.setChecked(previous_settings.get("gen_populate_methods", True))
        
        self.gen_populate_calls = QCheckBox(self.t.get("gen_populate_calls", "Generate code calling populate methods"))
        self.gen_populate_calls.setChecked(previous_settings.get("gen_populate_calls", True))
        
        layout.addWidget(self.gen_tli_fields)
        layout.addWidget(self.gen_order_model)
        layout.addWidget(self.gen_populate_methods)
        layout.addWidget(self.gen_populate_calls)
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_settings(self) -> Dict[str, bool]:
        """Get current settings"""
        return {
            "gen_tli_fields": self.gen_tli_fields.isChecked(),
            "gen_order_model": self.gen_order_model.isChecked(),
            "gen_populate_methods": self.gen_populate_methods.isChecked(),
            "gen_populate_calls": self.gen_populate_calls.isChecked(),
        }


class OrderAckSettingsDialog(QDialog):
    """Dialog for OrderAck (855) generation settings"""

    def __init__(self, language: str, items: List, previous_settings: Dict = None, parent=None):
        """
        Initialize OrderAck settings dialog
        
        Args:
            language: Current UI language
            items: List of Item instances with rsx_path_855 and put_in_855 fields
            previous_settings: Previously saved settings dict
            parent: Parent widget
        """
        super().__init__(parent)
        self.language = language
        self.items = items
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])
        
        # Use previous settings or defaults
        if previous_settings is None:
            previous_settings = {}
        
        self.setWindowTitle(f"855 - {self.t.get('settings', 'Settings')}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Main options with previous values
        self.gen_ack_type = QCheckBox(self.t.get("gen_ack_type_drafts", "Generate AcknowledgementType drafts"))
        self.gen_ack_type.setChecked(previous_settings.get("gen_ack_type", True))
        
        self.gen_line_seq = QCheckBox(self.t.get("gen_line_seq_number", "Generate LineSequenceNumber"))
        self.gen_line_seq.setChecked(previous_settings.get("gen_line_seq", True))
        
        self.gen_item_status = QCheckBox(self.t.get("gen_item_status_drafts", "Generate ItemStatusCode drafts"))
        self.gen_item_status.setChecked(previous_settings.get("gen_item_status", True))
        
        layout.addWidget(self.gen_ack_type)
        layout.addWidget(self.gen_line_seq)
        layout.addWidget(self.gen_item_status)
        
        # TLI Sources group
        tli_group = QGroupBox(self.t.get("tli_sources", "TLI Sources"))
        tli_layout = QVBoxLayout()
        
        # Scroll area for TLI checkboxes
        scroll = QWidget()
        scroll_layout = QGridLayout()
        scroll.setLayout(scroll_layout)
        
        self.tli_checkboxes: Dict[str, QCheckBox] = {}  # Key: item_id for uniqueness
        
        # Get saved TLI sources states from previous settings
        saved_tli_sources = previous_settings.get("tli_sources", {})
        
        # Collect items with rsx_path_855 and determine checked state
        items_to_display = []

        for item in items:
            rsx_path = getattr(item, "rsx_path_855", "")
            if rsx_path:  # Only show if path is not empty
                item_id = getattr(item, "item_properties_id", None)
                # Use saved state if exists, otherwise fall back to Item's value
                if str(item_id) in saved_tli_sources:
                    is_checked = saved_tli_sources[str(item_id)]

                else:
                    is_checked = getattr(item, "put_in_855", False)

                items_to_display.append((item, rsx_path, is_checked, item_id))
        
        # Sort: checked items first (True > False in reverse order)
        items_to_display.sort(key=lambda x: x[2], reverse=True)
        
        row = 0
        for item, rsx_path, is_checked, item_id in items_to_display:
            # Build EDI info text
            edi_segment = getattr(item, "edi_segment", "")
            edi_element = getattr(item, "edi_element_number", "")
            edi_qualifier = getattr(item, "edi_qualifier", "")

            edi_parts = []
            if edi_segment:
                edi_parts.append(edi_segment)
            if edi_element:
                edi_parts.append(edi_element)
            if edi_qualifier:
                edi_parts.append(edi_qualifier)

            edi_text = " | ".join(edi_parts)

            checkbox = QCheckBox()
            checkbox.setChecked(is_checked)
            self.tli_checkboxes[str(item_id)] = checkbox  # Use item_id as key for uniqueness

            edi_label = QLabel(edi_text)
            path_label = QLabel(rsx_path)

            scroll_layout.addWidget(checkbox, row, 0)
            scroll_layout.addWidget(edi_label, row, 1)
            scroll_layout.addWidget(path_label, row, 2)

            row += 1

        # Add stretch row to push content to the top
        scroll_layout.setRowStretch(row, 1)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll)
        scroll_area.setWidgetResizable(True)
        tli_layout.addWidget(scroll_area)
        tli_group.setLayout(tli_layout)
        
        layout.addWidget(tli_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_settings(self) -> Dict:
        """Get current settings"""
        return {
            "gen_ack_type": self.gen_ack_type.isChecked(),
            "gen_line_seq": self.gen_line_seq.isChecked(),
            "gen_item_status": self.gen_item_status.isChecked(),
            "tli_sources": {str(item_id): cb.isChecked() for item_id, cb in self.tli_checkboxes.items()},
        }


class ShipmentSettingsDialog(QDialog):
    """Dialog for Shipment (856) generation settings"""

    def __init__(self, language: str, items: List, previous_settings: Dict = None, parent=None):
        """
        Initialize Shipment settings dialog
        
        Args:
            language: Current UI language
            items: List of Item instances with rsx_path_856 and put_in_856 fields
            previous_settings: Previously saved settings dict
            parent: Parent widget
        """
        super().__init__(parent)
        self.language = language
        self.items = items
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])
        
        # Use previous settings or defaults
        if previous_settings is None:
            previous_settings = {}
        
        self.setWindowTitle(f"856 - {self.t.get('settings', 'Settings')}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Main options with previous values
        self.gen_tset_purpose = QCheckBox(self.t.get("gen_tset_purpose_drafts", "Generate TsetPurposeCode drafts"))
        self.gen_tset_purpose.setChecked(previous_settings.get("gen_tset_purpose", True))
        
        self.gen_line_seq = QCheckBox(self.t.get("gen_line_seq_number", "Generate LineSequenceNumber"))
        self.gen_line_seq.setChecked(previous_settings.get("gen_line_seq", True))
        
        layout.addWidget(self.gen_tset_purpose)
        layout.addWidget(self.gen_line_seq)
        
        # TLI Sources group
        tli_group = QGroupBox(self.t.get("tli_sources", "TLI Sources"))
        tli_layout = QVBoxLayout()
        
        # Scroll area for TLI checkboxes
        scroll = QWidget()
        scroll_layout = QGridLayout()
        scroll.setLayout(scroll_layout)
        
        self.tli_checkboxes: Dict[str, QCheckBox] = {}
        
        # Get saved TLI sources states from previous settings
        saved_tli_sources = previous_settings.get("tli_sources", {})
        
        # Collect items with rsx_path_856 and determine checked state
        items_to_display = []
        for item in items:
            rsx_path = getattr(item, "rsx_path_856", "")
            if rsx_path:  # Only show if path is not empty
                item_id = getattr(item, "item_properties_id", None)
                # Use saved state if exists, otherwise fall back to Item's value
                if str(item_id) in saved_tli_sources:
                    is_checked = saved_tli_sources[str(item_id)]
                else:
                    is_checked = getattr(item, "put_in_856", False)
                items_to_display.append((item, rsx_path, is_checked, item_id))
        
        # Sort: checked items first (True > False in reverse order)
        items_to_display.sort(key=lambda x: x[2], reverse=True)
        
        row = 0
        for item, rsx_path, is_checked, item_id in items_to_display:
            # Build EDI info text
            edi_segment = getattr(item, "edi_segment", "")
            edi_element = getattr(item, "edi_element_number", "")
            edi_qualifier = getattr(item, "edi_qualifier", "")

            edi_parts = []
            if edi_segment:
                edi_parts.append(edi_segment)
            if edi_element:
                edi_parts.append(edi_element)
            if edi_qualifier:
                edi_parts.append(edi_qualifier)

            edi_text = " | ".join(edi_parts)

            checkbox = QCheckBox()
            checkbox.setChecked(is_checked)
            self.tli_checkboxes[str(item_id)] = checkbox  # Use item_id as key for uniqueness

            edi_label = QLabel(edi_text)
            path_label = QLabel(rsx_path)

            scroll_layout.addWidget(checkbox, row, 0)
            scroll_layout.addWidget(edi_label, row, 1)
            scroll_layout.addWidget(path_label, row, 2)

            row += 1

        # Add stretch row to push content to the top
        scroll_layout.setRowStretch(row, 1)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll)
        scroll_area.setWidgetResizable(True)
        tli_layout.addWidget(scroll_area)
        tli_group.setLayout(tli_layout)
        
        layout.addWidget(tli_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_settings(self) -> Dict:
        """Get current settings"""
        return {
            "gen_tset_purpose": self.gen_tset_purpose.isChecked(),
            "gen_line_seq": self.gen_line_seq.isChecked(),
            "tli_sources": {str(item_id): cb.isChecked() for item_id, cb in self.tli_checkboxes.items()},
        }


class InvoiceSettingsDialog(QDialog):
    """Dialog for Invoice (810) generation settings"""

    def __init__(self, language: str, items: List, previous_settings: Dict = None, parent=None):
        """
        Initialize Invoice settings dialog
        
        Args:
            language: Current UI language
            items: List of Item instances with rsx_path_810 and put_in_810 fields
            previous_settings: Previously saved settings dict
            parent: Parent widget
        """
        super().__init__(parent)
        self.language = language
        self.items = items
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])
        
        # Use previous settings or defaults
        if previous_settings is None:
            previous_settings = {}
        
        self.setWindowTitle(f"810 - {self.t.get('settings', 'Settings')}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Main options with previous values
        self.gen_taxes = QCheckBox(self.t.get("gen_taxes", "Generate Taxes"))
        self.gen_taxes.setChecked(previous_settings.get("gen_taxes", True))
        
        self.gen_charges = QCheckBox(self.t.get("gen_charges_allowances", "Generate ChargesAllowances"))
        self.gen_charges.setChecked(previous_settings.get("gen_charges", True))
        
        self.gen_line_seq = QCheckBox(self.t.get("gen_line_seq_number", "Generate LineSequenceNumber"))
        self.gen_line_seq.setChecked(previous_settings.get("gen_line_seq", True))
        
        self.gen_total_amount = QCheckBox(self.t.get("gen_total_amount", "Generate calculated TotalAmount value"))
        self.gen_total_amount.setChecked(previous_settings.get("gen_total_amount", True))
        
        layout.addWidget(self.gen_taxes)
        layout.addWidget(self.gen_charges)
        layout.addWidget(self.gen_line_seq)
        layout.addWidget(self.gen_total_amount)
        
        # TLI Sources group
        tli_group = QGroupBox(self.t.get("tli_sources", "TLI Sources"))
        tli_layout = QVBoxLayout()
        
        # Scroll area for TLI checkboxes
        scroll = QWidget()
        scroll_layout = QGridLayout()
        scroll.setLayout(scroll_layout)
        
        self.tli_checkboxes: Dict[str, QCheckBox] = {}
        
        # Get saved TLI sources states from previous settings
        saved_tli_sources = previous_settings.get("tli_sources", {})
        
        # Collect items with rsx_path_810 and determine checked state
        items_to_display = []
        for item in items:
            rsx_path = getattr(item, "rsx_path_810", "")
            if rsx_path:  # Only show if path is not empty
                item_id = getattr(item, "item_properties_id", None)
                # Use saved state if exists, otherwise fall back to Item's value
                if str(item_id) in saved_tli_sources:
                    is_checked = saved_tli_sources[str(item_id)]
                else:
                    is_checked = getattr(item, "put_in_810", False)
                items_to_display.append((item, rsx_path, is_checked, item_id))
        
        # Sort: checked items first (True > False in reverse order)
        items_to_display.sort(key=lambda x: x[2], reverse=True)
        
        row = 0
        for item, rsx_path, is_checked, item_id in items_to_display:
            # Build EDI info text
            edi_segment = getattr(item, "edi_segment", "")
            edi_element = getattr(item, "edi_element_number", "")
            edi_qualifier = getattr(item, "edi_qualifier", "")

            edi_parts = []
            if edi_segment:
                edi_parts.append(edi_segment)
            if edi_element:
                edi_parts.append(edi_element)
            if edi_qualifier:
                edi_parts.append(edi_qualifier)

            edi_text = " | ".join(edi_parts)

            checkbox = QCheckBox()
            checkbox.setChecked(is_checked)
            self.tli_checkboxes[str(item_id)] = checkbox  # Use item_id as key for uniqueness

            edi_label = QLabel(edi_text)
            path_label = QLabel(rsx_path)

            scroll_layout.addWidget(checkbox, row, 0)
            scroll_layout.addWidget(edi_label, row, 1)
            scroll_layout.addWidget(path_label, row, 2)

            row += 1

        # Add stretch row to push content to the top
        scroll_layout.setRowStretch(row, 1)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll)
        scroll_area.setWidgetResizable(True)
        tli_layout.addWidget(scroll_area)
        tli_group.setLayout(tli_layout)
        
        layout.addWidget(tli_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_settings(self) -> Dict:
        """Get current settings"""
        return {
            "gen_taxes": self.gen_taxes.isChecked(),
            "gen_charges": self.gen_charges.isChecked(),
            "gen_line_seq": self.gen_line_seq.isChecked(),
            "gen_total_amount": self.gen_total_amount.isChecked(),
            "tli_sources": {str(item_id): cb.isChecked() for item_id, cb in self.tli_checkboxes.items()},
        }


class CSVInboundItemsDialog(QDialog):
    """Dialog for selecting which Items are used in inbound CSV test files."""

    def __init__(self, language: str, items: List, previous_settings: Dict = None, parent=None):
        """Initialize CSV inbound items settings dialog.

        Args:
            language: Current UI language
            items: List of Item instances
            previous_settings: Previously saved settings dict
            parent: Parent widget
        """
        super().__init__(parent)
        self.language = language
        self.items = items
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])

        if previous_settings is None:
            previous_settings = {}

        self.setWindowTitle(f"{self.t.get('gen_csv_inbound', 'CSV inbound')} - {self.t.get('settings', 'Settings')}")
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        row_count = len(items)
        self.table = QTableWidget(row_count, 5, self)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        # Columns: index, checkbox, EDI triple, spreadsheet_label, tli_value
        self.table.setHorizontalHeaderLabels([
            "№",
            "",
            "EDI",
            "Label",
            "TLI value",
        ])

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 40)

        # Restore enabled flags if available and length matches, else default to all enabled
        saved_enabled = previous_settings.get("enabled_items")
        if isinstance(saved_enabled, list) and len(saved_enabled) == row_count:
            enabled_flags = [bool(v) for v in saved_enabled]
        else:
            enabled_flags = [True] * row_count

        self._row_checkboxes: List[QCheckBox] = []

        for row, item in enumerate(items):
            # Index (1-based)
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            index_item.setFlags(index_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, index_item)

            # Checkbox
            cb = QCheckBox()
            cb.setChecked(enabled_flags[row])
            cb.setTristate(False)
            self.table.setCellWidget(row, 1, cb)
            self._row_checkboxes.append(cb)

            # EDI triple: segment | element | qualifier
            edi_segment = getattr(item, "edi_segment", "") or ""
            edi_element = getattr(item, "edi_element_number", "") or ""
            edi_qualifier = getattr(item, "edi_qualifier", "") or ""

            edi_parts = []
            if edi_segment:
                edi_parts.append(str(edi_segment))
            if edi_element:
                edi_parts.append(str(edi_element))
            if edi_qualifier:
                edi_parts.append(str(edi_qualifier))

            edi_text = " | ".join(edi_parts)
            edi_item = QTableWidgetItem(edi_text)
            edi_item.setFlags(edi_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, edi_item)

            # Spreadsheet label
            label_text = getattr(item, "spreadsheet_label", "") or ""
            label_item = QTableWidgetItem(label_text)
            label_item.setFlags(label_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, label_item)

            # TLI value
            tli_text = getattr(item, "tli_value", "") or ""
            tli_item = QTableWidgetItem(tli_text)
            tli_item.setFlags(tli_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, tli_item)

        layout.addWidget(self.table)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> Dict:
        """Return current CSV inbound item selection settings."""
        enabled_items = [cb.isChecked() for cb in self._row_checkboxes]
        return {"enabled_items": enabled_items}
