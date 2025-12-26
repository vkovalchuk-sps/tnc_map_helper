"""Dialog for displaying Item information"""

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

from application.spreadsheet_parser import Item
from application.translations import TRANSLATIONS


class ItemsInfoDialog(QDialog):
    """Dialog for displaying parsed Item information"""

    def __init__(
        self,
        items: List[Item],
        current_language: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.items = items
        self.current_language = current_language
        self.t = TRANSLATIONS.get(current_language, TRANSLATIONS["UA"])
        self.setWindowTitle(self.t.get("items_info_title", "Items Information"))
        self.setMinimumSize(960, 780)
        self._create_ui()

    def _wrap_text(self, text: str, max_length: int = 30) -> str:
        """Wrap text to multiple lines if it exceeds max_length"""
        if len(text) <= max_length:
            return text

        words = text.split()
        lines: list[str] = []
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

    def _create_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Scroll area for items
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Field descriptions (use human-readable description strings from translations)
        t = self.t
        field_descriptions = {
            "edi_segment": t.get("desc_edi_segment", "edi_segment"),
            "edi_element_number": t.get("desc_edi_element_number", "edi_element_number"),
            "edi_qualifier": t.get("desc_edi_qualifier", "edi_qualifier"),
            "spreadsheet_label": t.get("desc_spreadsheet_label", "spreadsheet_label"),
            "spreadsheet_usage": t.get("desc_spreadsheet_usage", "spreadsheet_usage"),
            "spreadsheet_min": t.get("desc_spreadsheet_min", "spreadsheet_min"),
            "spreadsheet_max": t.get("desc_spreadsheet_max", "spreadsheet_max"),
            "spreadsheet_description": t.get("desc_spreadsheet_description", "spreadsheet_description"),
            "extra_record_defining_rsx_tag": t.get("desc_extra_record_defining_rsx_tag", "extra_record_defining_rsx_tag"),
            "extra_record_defining_qual": t.get("desc_extra_record_defining_qual", "extra_record_defining_qual"),
            "TLI_value": t.get("desc_TLI_value", "TLI_value"),
            "850_RSX_tag": t.get("desc_850_RSX_tag", "850_RSX_tag"),
            "850_TLI_tag": t.get("desc_850_TLI_tag", "850_TLI_tag"),
            "is_on_detail_level": t.get("desc_is_on_detail_level", "is_on_detail_level"),
            "is_partnumber": t.get("desc_is_partnumber", "is_partnumber"),
            "855_RSX_path": t.get("desc_855_RSX_path", "855_RSX_path"),
            "put_in_855_by_default": t.get("desc_put_in_855_by_default", "put_in_855_by_default"),
            "856_RSX_path": t.get("desc_856_RSX_path", "856_RSX_path"),
            "put_in_856_by_default": t.get("desc_put_in_856_by_default", "put_in_856_by_default"),
            "810_RSX_path": t.get("desc_810_RSX_path", "810_RSX_path"),
            "put_in_810_by_default": t.get("desc_put_in_810_by_default", "put_in_810_by_default"),
            "populate_method_name": t.get("desc_populate_method_name", "populate_method_name"),
            "map_name": t.get("desc_map_name", "map_name"),
            "call_method_java_code": t.get("desc_call_method_java_code", "call_method_java_code"),
            "order_path": t.get("desc_order_path", "order_path"),
            "order_change_path": t.get("desc_order_change_path", "order_change_path"),
            "java_code_wrapper": t.get("desc_java_code_wrapper", "java_code_wrapper"),
        }

        for idx, item in enumerate(self.items, start=1):
            # Header (always visible): number + spreadsheet_label
            title = item.spreadsheet_label or "Item"
            group_title = f"{idx}. {title}"
            item_group = QGroupBox(group_title)
            item_group.setCheckable(True)
            item_group.setChecked(False)
            # Match checkbox and border style with scenarios dialog
            item_group.setStyleSheet(
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

            item_layout = QVBoxLayout(item_group)
            # slightly larger top margin so the second line is clearer under the title
            item_layout.setContentsMargins(28, 8, 8, 2)
            item_layout.setSpacing(0)

            # Second line (always visible in collapsed view): compact EDI info
            second_line_layout = QHBoxLayout()
            # increased top margin so second row is visually separated
            second_line_layout.setContentsMargins(18, 3, 0, 0)
            second_line_layout.setSpacing(0)

            edi_parts = []
            if item.edi_segment:
                edi_parts.append(str(item.edi_segment))
            if item.edi_element_number is not None:
                edi_parts.append(str(item.edi_element_number))
            if item.edi_qualifier:
                edi_parts.append(str(item.edi_qualifier))

            edi_text = " | ".join(edi_parts) if edi_parts else ""
            edi_label = QLabel(edi_text)
            edi_label.setStyleSheet("color: #666666; font-size: 8pt; margin: 0px; padding: 0px;")
            second_line_layout.addWidget(edi_label)
            second_line_layout.addStretch()
            item_layout.addLayout(second_line_layout)

            # Expanded content (hidden by default)
            expanded_widget = QWidget()
            expanded_layout = QVBoxLayout(expanded_widget)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.horizontalHeader().setVisible(False)
            table.verticalHeader().setVisible(False)
            table.setShowGrid(True)
            table.setAlternatingRowColors(True)
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

            current_row = 0

            # Helper functions for rows
            def add_simple_row(field_key: str, value_text: str) -> None:
                nonlocal current_row
                table.insertRow(current_row)
                desc_item = QTableWidgetItem(field_descriptions[field_key])
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(current_row, 0, desc_item)
                value_item = QTableWidgetItem(value_text)
                value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(current_row, 1, value_item)
                current_row += 1

            def add_button_row(field_key: str, content: str) -> None:
                nonlocal current_row
                table.insertRow(current_row)
                desc_item = QTableWidgetItem(field_descriptions[field_key])
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(current_row, 0, desc_item)
                button = QPushButton(self.t.get("show_content", "Show Content"))
                button.setFixedWidth(140)
                button.setFixedHeight(24)
                title = field_descriptions[field_key]
                button.clicked.connect(
                    lambda checked, text=content, ttitle=title: self._show_text_content(text, ttitle)
                )
                table.setCellWidget(current_row, 1, button)
                current_row += 1

            # Order of fields as requested
            # 1) EDI fields
            if item.edi_segment:
                add_simple_row("edi_segment", item.edi_segment)
            if item.edi_element_number:
                add_simple_row("edi_element_number", str(item.edi_element_number))
            if item.edi_qualifier:
                add_simple_row("edi_qualifier", item.edi_qualifier)

            # 2) Spreadsheet fields
            if item.spreadsheet_label:
                add_simple_row("spreadsheet_label", item.spreadsheet_label)
            if item.spreadsheet_usage:
                add_simple_row("spreadsheet_usage", item.spreadsheet_usage)
            if item.spreadsheet_min is not None:
                add_simple_row("spreadsheet_min", str(item.spreadsheet_min))
            if item.spreadsheet_max is not None:
                add_simple_row("spreadsheet_max", str(item.spreadsheet_max))
            if item.spreadsheet_description:
                add_button_row("spreadsheet_description", item.spreadsheet_description)

            # 3) Extra record fields
            if getattr(item, "extra_record_defining_rsx_tag", ""):
                add_simple_row("extra_record_defining_rsx_tag", item.extra_record_defining_rsx_tag)
            if getattr(item, "extra_record_defining_qual", ""):
                add_simple_row("extra_record_defining_qual", item.extra_record_defining_qual)

            # 4) TLI value and mapping fields
            if item.tli_value:
                add_simple_row("TLI_value", item.tli_value)
            if item.rsx_tag_850:
                add_simple_row("850_RSX_tag", item.rsx_tag_850)
            if item.tli_tag_850:
                add_simple_row("850_TLI_tag", item.tli_tag_850)

            # 5) Flags
            add_simple_row("is_on_detail_level", "Yes" if item.is_on_detail_level else "No")
            add_simple_row("is_partnumber", "Yes" if item.is_partnumber else "No")

            # 6) RSX paths and put_in flags
            if item.rsx_path_855:
                add_simple_row("855_RSX_path", item.rsx_path_855)
            add_simple_row("put_in_855_by_default", "Yes" if getattr(item, "put_in_855", False) else "No")

            if item.rsx_path_856:
                add_simple_row("856_RSX_path", item.rsx_path_856)
            add_simple_row("put_in_856_by_default", "Yes" if getattr(item, "put_in_856", False) else "No")

            if item.rsx_path_810:
                add_simple_row("810_RSX_path", item.rsx_path_810)
            add_simple_row("put_in_810_by_default", "Yes" if getattr(item, "put_in_810", False) else "No")

            # 7) Sourcing group and order path fields
            if item.populate_method_name:
                add_simple_row("populate_method_name", item.populate_method_name)
            if item.map_name:
                add_simple_row("map_name", item.map_name)
            if item.call_method_java_code:
                add_button_row("call_method_java_code", item.call_method_java_code)
            if getattr(item, "order_path", ""):
                add_simple_row("order_path", item.order_path)
            if getattr(item, "order_change_path", ""):
                add_simple_row("order_change_path", item.order_change_path)
            if getattr(item, "java_code_wrapper", ""):
                add_button_row("java_code_wrapper", item.java_code_wrapper)

            # Ensure the whole table is visible (no inner scrolling)
            table.setWordWrap(True)
            table.resizeRowsToContents()
            base_height = table.fontMetrics().height() + 8
            for r in range(table.rowCount()):
                if table.rowHeight(r) < base_height:
                    table.setRowHeight(r, base_height)

            header_height = table.horizontalHeader().height() if table.horizontalHeader().isVisible() else 0
            total_height = header_height + 2 * table.frameWidth()
            for r in range(table.rowCount()):
                total_height += table.rowHeight(r)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table.setMinimumHeight(total_height)
            table.setMaximumHeight(total_height)

            expanded_layout.addWidget(table)
            item_layout.addWidget(expanded_widget)

            # Toggle visibility
            item_group.toggled.connect(
                lambda checked, widget=expanded_widget: widget.setVisible(checked)
            )
            expanded_widget.setVisible(False)

            scroll_layout.addWidget(item_group)

        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _show_text_content(self, content: str, title: str) -> None:
        """Show long text content in a separate dialog (similar to scenarios dialog)."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(900, 600)

        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=dialog)
        buttons.rejected.connect(dialog.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

        dialog.exec()
