"""Dialog for displaying Sourcing Groups information"""

from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QVBoxLayout,
    QWidget,
)

from application.parsers.spreadsheet_parser import Item, SourcingGroup, SourceFromTLIPath
from application.translations import TRANSLATIONS


class SourcingGroupsInfoDialog(QDialog):
    """Dialog for displaying Sourcing Groups information"""

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
        self.setWindowTitle(self.t.get("sourcing_groups_info_title", "Sourcing Groups Information"))
        self.setMinimumSize(960, 780)
        self._create_ui()

    def _create_ui(self) -> None:
        """Create user interface"""
        layout = QVBoxLayout(self)

        # Scroll area for groups
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Group items by SourceFromTLIPath.order_path
        # Structure: path -> list of (SourcingGroup, List[Item]) tuples
        groups_by_path: Dict[SourceFromTLIPath, List[Tuple[SourcingGroup, List[Item]]]] = {}
        seen_per_path: Dict[SourceFromTLIPath, set] = {}
        
        for item in self.items:
            sg = item.sourcing_group
            if sg is None:
                continue
            
            path = sg.source_from_tli_path
            if path is None:
                continue
            
            if path not in groups_by_path:
                groups_by_path[path] = []
                seen_per_path[path] = set()
            
            # Use a tuple key to ensure uniqueness
            sg_key = (
                sg.sourcing_group_properties_id,
                sg.populate_method_name,
                sg.map_name,
            )
            
            # Find existing group or create new one
            found = False
            for idx, (existing_sg, items_list) in enumerate(groups_by_path[path]):
                existing_key = (
                    existing_sg.sourcing_group_properties_id,
                    existing_sg.populate_method_name,
                    existing_sg.map_name,
                )
                if existing_key == sg_key:
                    items_list.append(item)
                    found = True
                    break
            
            if not found:
                groups_by_path[path].append((sg, [item]))
                seen_per_path[path].add(sg_key)

        # Display groups grouped by order_path (expanded by default)
        for path, groups_dict in groups_by_path.items():
            # Create group box for order_path
            path_group = QGroupBox()
            path_group.setCheckable(True)
            path_group.setChecked(True)  # Expanded by default

            # Header with order_path
            header_text = path.order_path if path.order_path else self.t.get("no_order_path", "No order path")
            path_group.setTitle(header_text)

            # Match checkbox/border style with ScenariosInfoDialog
            path_group.setStyleSheet(
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

            path_layout = QVBoxLayout()
            path_layout.setContentsMargins(28, 8, 8, 2)
            path_layout.setSpacing(0)
            path_group.setLayout(path_layout)

            # Expanded content (visible by default)
            expanded_widget = QWidget()
            expanded_layout = QVBoxLayout()
            expanded_widget.setLayout(expanded_layout)

            # Display each SourcingGroup within this path
            for idx, (sg, items_for_group) in enumerate(groups_dict):
                # Create collapsible group box for each SourcingGroup
                sg_group = QGroupBox()
                sg_group.setCheckable(True)
                sg_group.setChecked(False)  # Collapsed by default

                # Header with map_name
                sg_header_text = f"{idx + 1}. {sg.map_name}"
                sg_group.setTitle(sg_header_text)

                # Same style as path groups
                sg_group.setStyleSheet(
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

                sg_layout = QVBoxLayout()
                sg_layout.setContentsMargins(28, 8, 8, 2)
                sg_layout.setSpacing(0)
                sg_group.setLayout(sg_layout)

                # Items table (hidden by default)
                items_widget = QWidget()
                items_layout = QVBoxLayout()
                items_widget.setLayout(items_layout)

                # Create table for items
                table = QTableWidget()
                table.setColumnCount(4)
                table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                table.horizontalHeader().setVisible(True)
                table.verticalHeader().setVisible(False)
                table.setShowGrid(True)
                table.setAlternatingRowColors(True)
                
                # Set headers
                headers = [
                    self.t.get("sourcing_group_table_tli_name", "Назва TLI поля"),
                    self.t.get("sourcing_group_table_x12_element", "Елемент в X12"),
                    self.t.get("sourcing_group_table_tli_javaname", "JavaName TLI поля"),
                    self.t.get("sourcing_group_table_rsx_javaname", "JavaName відповідного RSX поля"),
                ]
                table.setHorizontalHeaderLabels(headers)
                
                header = table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
                
                # Make header text bold
                font = header.font()
                font.setBold(True)
                header.setFont(font)

                # Populate table with items
                for item in items_for_group:
                    row = table.rowCount()
                    table.insertRow(row)

                    # spreadsheet_label
                    label_item = QTableWidgetItem(item.spreadsheet_label)
                    label_item.setFlags(label_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(row, 0, label_item)

                    # EDI element in format "REF | 02 | IA" (or just parts that exist)
                    edi_parts = []
                    if item.edi_segment:
                        edi_parts.append(item.edi_segment)
                    if item.edi_element_number:
                        edi_parts.append(item.edi_element_number)
                    if item.edi_qualifier:
                        edi_parts.append(item.edi_qualifier)
                    
                    edi_text = " | ".join(edi_parts) if edi_parts else ""
                    edi_item = QTableWidgetItem(edi_text)
                    edi_item.setFlags(edi_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(row, 1, edi_item)

                    # tli_tag_850
                    tli_item = QTableWidgetItem(item.tli_tag_850)
                    tli_item.setFlags(tli_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(row, 2, tli_item)

                    # rsx_tag_850
                    rsx_item = QTableWidgetItem(item.rsx_tag_850)
                    rsx_item.setFlags(rsx_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(row, 3, rsx_item)

                # Resize rows to content
                table.setWordWrap(False)
                table.resizeRowsToContents()
                
                # Set minimum row height
                base_height = table.fontMetrics().height() + 8
                for r in range(table.rowCount()):
                    if table.rowHeight(r) < base_height:
                        table.setRowHeight(r, base_height)
                
                # Resize columns to content
                table.resizeColumnsToContents()
                
                # Set minimum column widths
                table.setColumnWidth(0, max(200, table.columnWidth(0)))
                table.setColumnWidth(1, max(150, table.columnWidth(1)))
                table.setColumnWidth(2, max(200, table.columnWidth(2)))
                
                # Calculate total height dynamically based on content
                header_height = table.horizontalHeader().height() if table.horizontalHeader().isVisible() else 0
                if header_height == 0:
                    # If header height is 0, use a default value
                    header_height = table.fontMetrics().height() + 12
                
                total_height = header_height + 2 * table.frameWidth()
                for r in range(table.rowCount()):
                    total_height += table.rowHeight(r)
                
                # Ensure minimum height even if no rows
                if table.rowCount() == 0:
                    total_height = header_height + 2 * table.frameWidth() + base_height
                
                table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                table.setMinimumHeight(total_height)
                table.setMaximumHeight(total_height)

                items_layout.addWidget(table)
                sg_layout.addWidget(items_widget)

                # Connect checkbox to show/hide items table
                sg_group.toggled.connect(
                    lambda checked, widget=items_widget: widget.setVisible(checked)
                )

                # Initially hide items table
                items_widget.setVisible(False)

                expanded_layout.addWidget(sg_group)

            path_layout.addWidget(expanded_widget)

            # Connect checkbox to show/hide expanded content
            path_group.toggled.connect(
                lambda checked, widget=expanded_widget: widget.setVisible(checked)
            )

            scroll_layout.addWidget(path_group)

        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

