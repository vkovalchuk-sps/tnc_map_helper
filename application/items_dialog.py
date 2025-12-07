"""Dialog for displaying Item information"""

from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
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

        # Field descriptions (reuse editor translations where possible)
        t = self.t
        field_descriptions = {
            "spreadsheet_label": t.get("spreadsheet", "Spreadsheet"),
            "edi_segment": t.get("edi_segment", "edi_segment"),
            "edi_element_number": t.get("edi_element_number", "edi_element_number"),
            "edi_qualifier": t.get("edi_qualifier", "edi_qualifier"),
            "TLI_value": t.get("TLI_value", "TLI_value"),
            "850_RSX_tag": t.get("850_RSX_tag", "850_RSX_tag"),
            "850_TLI_tag": t.get("850_TLI_tag", "850_TLI_tag"),
            "is_on_detail_level": t.get("is_on_detail_level", "is_on_detail_level"),
            "is_partnumber": t.get("is_partnumber", "is_partnumber"),
            "855_RSX_path": t.get("855_RSX_path", "855_RSX_path"),
            "856_RSX_path": t.get("856_RSX_path", "856_RSX_path"),
            "810_RSX_path": t.get("810_RSX_path", "810_RSX_path"),
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

            # EDI fields
            def add_simple_row(field_key: str, value_text: str) -> None:
                row = QHBoxLayout()
                label = QLabel(self._wrap_text(field_descriptions[field_key]))
                label.setMinimumWidth(200)
                label.setWordWrap(True)
                value = QLabel(value_text)
                row.addWidget(label)
                row.addWidget(value)
                row.addStretch()
                expanded_layout.addLayout(row)

            if item.edi_segment:
                add_simple_row("edi_segment", item.edi_segment)
            if item.edi_element_number:
                add_simple_row("edi_element_number", str(item.edi_element_number))
            if item.edi_qualifier:
                add_simple_row("edi_qualifier", item.edi_qualifier)

            # TLI value and mapping fields
            if item.tli_value:
                add_simple_row("TLI_value", item.tli_value)
            if item.rsx_tag_850:
                add_simple_row("850_RSX_tag", item.rsx_tag_850)
            if item.tli_tag_850:
                add_simple_row("850_TLI_tag", item.tli_tag_850)

            # Flags
            add_simple_row(
                "is_on_detail_level",
                "Yes" if item.is_on_detail_level else "No",
            )
            add_simple_row(
                "is_partnumber",
                "Yes" if item.is_partnumber else "No",
            )

            # RSX paths
            if item.rsx_path_855:
                add_simple_row("855_RSX_path", item.rsx_path_855)
            if item.rsx_path_856:
                add_simple_row("856_RSX_path", item.rsx_path_856)
            if item.rsx_path_810:
                add_simple_row("810_RSX_path", item.rsx_path_810)

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
