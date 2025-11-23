"""UI components factory for creating interface elements"""

from pathlib import Path
from typing import Dict

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class UIComponents:
    """Factory for creating UI components"""

    @staticmethod
    def create_language_selector() -> tuple[QHBoxLayout, QComboBox]:
        """Create language selection component"""
        layout = QHBoxLayout()
        language_label = QLabel("Language:")
        language_combo = QComboBox()
        language_combo.addItems(["UA", "EN"])
        layout.addWidget(language_label)
        layout.addWidget(language_combo)
        layout.addStretch()
        return layout, language_combo

    @staticmethod
    def create_file_selection_group(
        title: str, label: QLabel, button: QPushButton
    ) -> QGroupBox:
        """Create file selection group"""
        group = QGroupBox(title)
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)
        group.setLayout(layout)
        return group

    @staticmethod
    def create_text_field_group(
        label_text: str, field: QLineEdit, min_width: int = 150
    ) -> QHBoxLayout:
        """Create text field with label"""
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(min_width)
        layout.addWidget(label)
        layout.addWidget(field)
        return layout, label

    @staticmethod
    def get_bold_font() -> QFont:
        """Get bold font for file labels"""
        font = QFont()
        font.setBold(True)
        return font

    @staticmethod
    def get_groupbox_style() -> str:
        """Get stylesheet for QGroupBox"""
        return """
            QGroupBox {
                font-weight: bold;
            }
        """

