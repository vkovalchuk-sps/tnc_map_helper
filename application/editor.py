"""Editor window for managing database records"""

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from application.database import Database
from application.translations import TRANSLATIONS


class ItemPropertiesEditor(QDialog):
    """Editor dialog for item properties"""

    def __init__(self, database: Database, current_language: str, parent=None) -> None:
        """
        Initialize ItemPropertiesEditor

        Args:
            database: Database instance
            current_language: Current UI language
            parent: Parent widget
        """
        super().__init__(parent)
        self.database = database
        self.current_language = current_language
        self.setWindowTitle(self._t("editor_title"))
        self.setMinimumSize(1000, 700)

        self.create_ui()
        self.load_data()

    def _t(self, key: str) -> str:
        """Get translation"""
        return TRANSLATIONS[self.current_language].get(key, key)

    def create_ui(self) -> None:
        """Create user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tab widget for three tables
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Item Properties (first tab)
        items_tab = QWidget()
        items_layout = QVBoxLayout()
        items_tab.setLayout(items_layout)

        # Buttons for items
        items_buttons = QHBoxLayout()
        self.add_item_btn = QPushButton(self._t("add"))
        self.add_item_btn.clicked.connect(self.add_item)  # type: ignore[arg-type]
        self.edit_item_btn = QPushButton(self._t("edit"))
        self.edit_item_btn.clicked.connect(self.edit_item)  # type: ignore[arg-type]
        self.clone_item_btn = QPushButton(self._t("clone"))
        self.clone_item_btn.clicked.connect(self.clone_item)  # type: ignore[arg-type]
        self.delete_item_btn = QPushButton(self._t("delete"))
        self.delete_item_btn.clicked.connect(self.delete_item)  # type: ignore[arg-type]
        items_buttons.addWidget(self.add_item_btn)
        items_buttons.addWidget(self.edit_item_btn)
        items_buttons.addWidget(self.clone_item_btn)
        items_buttons.addWidget(self.delete_item_btn)
        items_buttons.addStretch()
        items_layout.addLayout(items_buttons)

        # Table for items
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(13)
        self.items_table.setHorizontalHeaderLabels([
            "ID",
            self._t("edi_segment"),
            self._t("edi_element_number"),
            self._t("edi_qualifier"),
            self._t("TLI_value"),
            self._t("850_RSX_tag"),
            self._t("850_TLI_tag"),
            self._t("sourcing_group_id"),
            self._t("is_on_detail_level"),
            self._t("is_partnumber"),
            self._t("855_RSX_path"),
            self._t("856_RSX_path"),
            self._t("810_RSX_path"),
        ])
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            QTableWidget::item:selected:active {
                background-color: #357abd;
                color: white;
            }
            QHeaderView::section {
                font-weight: bold;
            }
        """)
        items_layout.addWidget(self.items_table)

        tabs.addTab(items_tab, self._t("items_tab"))

        # Tab 2: Sourcing Group Properties
        sourcing_tab = QWidget()
        sourcing_layout = QVBoxLayout()
        sourcing_tab.setLayout(sourcing_layout)

        # Buttons for sourcing groups
        sourcing_buttons = QHBoxLayout()
        self.add_sourcing_btn = QPushButton(self._t("add"))
        self.add_sourcing_btn.clicked.connect(self.add_sourcing_group)  # type: ignore[arg-type]
        self.edit_sourcing_btn = QPushButton(self._t("edit"))
        self.edit_sourcing_btn.clicked.connect(self.edit_sourcing_group)  # type: ignore[arg-type]
        self.clone_sourcing_btn = QPushButton(self._t("clone"))
        self.clone_sourcing_btn.clicked.connect(self.clone_sourcing_group)  # type: ignore[arg-type]
        self.delete_sourcing_btn = QPushButton(self._t("delete"))
        self.delete_sourcing_btn.clicked.connect(self.delete_sourcing_group)  # type: ignore[arg-type]
        sourcing_buttons.addWidget(self.add_sourcing_btn)
        sourcing_buttons.addWidget(self.edit_sourcing_btn)
        sourcing_buttons.addWidget(self.clone_sourcing_btn)
        sourcing_buttons.addWidget(self.delete_sourcing_btn)
        sourcing_buttons.addStretch()
        sourcing_layout.addLayout(sourcing_buttons)

        # Table for sourcing groups
        self.sourcing_table = QTableWidget()
        self.sourcing_table.setColumnCount(5)
        self.sourcing_table.setHorizontalHeaderLabels([
            "ID",
            self._t("populate_method_name"),
            self._t("map_name"),
            self._t("call_method_path"),
            self._t("call_method_java_code"),
        ])
        self.sourcing_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sourcing_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sourcing_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sourcing_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            QTableWidget::item:selected:active {
                background-color: #357abd;
                color: white;
            }
            QHeaderView::section {
                font-weight: bold;
            }
        """)
        sourcing_layout.addWidget(self.sourcing_table)

        tabs.addTab(sourcing_tab, self._t("sourcing_groups_tab"))

        # Tab 3: Order Path Properties
        order_path_tab = QWidget()
        order_path_layout = QVBoxLayout()
        order_path_tab.setLayout(order_path_layout)

        # Buttons for order paths
        order_path_buttons = QHBoxLayout()
        self.add_order_path_btn = QPushButton(self._t("add"))
        self.add_order_path_btn.clicked.connect(self.add_order_path)  # type: ignore[arg-type]
        self.edit_order_path_btn = QPushButton(self._t("edit"))
        self.edit_order_path_btn.clicked.connect(self.edit_order_path)  # type: ignore[arg-type]
        self.clone_order_path_btn = QPushButton(self._t("clone"))
        self.clone_order_path_btn.clicked.connect(self.clone_order_path)  # type: ignore[arg-type]
        self.delete_order_path_btn = QPushButton(self._t("delete"))
        self.delete_order_path_btn.clicked.connect(self.delete_order_path)  # type: ignore[arg-type]
        order_path_buttons.addWidget(self.add_order_path_btn)
        order_path_buttons.addWidget(self.edit_order_path_btn)
        order_path_buttons.addWidget(self.clone_order_path_btn)
        order_path_buttons.addWidget(self.delete_order_path_btn)
        order_path_buttons.addStretch()
        order_path_layout.addLayout(order_path_buttons)

        # Table for order paths
        self.order_path_table = QTableWidget()
        self.order_path_table.setColumnCount(3)
        self.order_path_table.setHorizontalHeaderLabels([
            "ID",
            self._t("order_path"),
            self._t("java_code_wrapper"),
        ])
        self.order_path_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.order_path_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.order_path_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.order_path_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            QTableWidget::item:selected:active {
                background-color: #357abd;
                color: white;
            }
            QHeaderView::section {
                font-weight: bold;
            }
        """)
        order_path_layout.addWidget(self.order_path_table)

        tabs.addTab(order_path_tab, self._t("order_paths_tab"))

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)  # type: ignore[arg-type]
        layout.addWidget(button_box)

    def load_data(self) -> None:
        """Load data from database into tables"""
        # Load sourcing groups
        groups = self.database.get_all_sourcing_groups()
        self.sourcing_table.setRowCount(len(groups))
        for row, group in enumerate(groups):
            item0 = QTableWidgetItem(str(group["sourcing_group_properties_id"]))
            item0.setToolTip(self._t("desc_sourcing_group_properties_id"))
            self.sourcing_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(group["populate_method_name"])
            item1.setToolTip(self._t("desc_populate_method_name"))
            self.sourcing_table.setItem(row, 1, item1)
            item2 = QTableWidgetItem(group["map_name"])
            item2.setToolTip(self._t("desc_map_name"))
            self.sourcing_table.setItem(row, 2, item2)
            call_method_path = group.get("order_path", group.get("call_method_path", ""))
            item3 = QTableWidgetItem(call_method_path)
            item3.setToolTip(self._t("desc_call_method_path"))
            self.sourcing_table.setItem(row, 3, item3)
            call_method_java_code = group.get("call_method_java_code", "")
            # Truncate for display
            display_java_code = call_method_java_code[:50] + "..." if len(call_method_java_code) > 50 else call_method_java_code
            item4 = QTableWidgetItem(display_java_code)
            item4.setToolTip(self._t("desc_call_method_java_code"))
            self.sourcing_table.setItem(row, 4, item4)
        self.sourcing_table.resizeColumnsToContents()

        # Load order paths
        paths = self.database.get_all_order_paths()
        self.order_path_table.setRowCount(len(paths))
        for row, path in enumerate(paths):
            item0 = QTableWidgetItem(str(path["order_path_properties_id"]))
            item0.setToolTip(self._t("desc_order_path_properties_id"))
            self.order_path_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(path["order_path"])
            item1.setToolTip(self._t("desc_order_path"))
            self.order_path_table.setItem(row, 1, item1)
            java_wrapper = path.get("java_code_wrapper") or ""
            # Truncate for display
            display_wrapper = java_wrapper[:50] + "..." if len(java_wrapper) > 50 else java_wrapper
            item2 = QTableWidgetItem(display_wrapper)
            item2.setToolTip(self._t("desc_java_code_wrapper"))
            self.order_path_table.setItem(row, 2, item2)
        self.order_path_table.resizeColumnsToContents()

        # Load items
        items = self.database.get_all_items()
        self.items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            item0 = QTableWidgetItem(str(item["item_properties_id"]))
            item0.setToolTip(self._t("desc_item_properties_id"))
            self.items_table.setItem(row, 0, item0)
            item1 = QTableWidgetItem(item["edi_segment"])
            item1.setToolTip(self._t("desc_edi_segment"))
            self.items_table.setItem(row, 1, item1)
            # Format edi_element_number as 01, 02, 03, etc.
            edi_element_str = f"{item['edi_element_number']:02d}"
            item2 = QTableWidgetItem(edi_element_str)
            item2.setToolTip(self._t("desc_edi_element_number"))
            self.items_table.setItem(row, 2, item2)
            item3 = QTableWidgetItem(item["edi_qualifier"] or "")
            item3.setToolTip(self._t("desc_edi_qualifier"))
            self.items_table.setItem(row, 3, item3)
            item4 = QTableWidgetItem(item["TLI_value"])
            item4.setToolTip(self._t("desc_TLI_value"))
            self.items_table.setItem(row, 4, item4)
            item5 = QTableWidgetItem(item["850_RSX_tag"])
            item5.setToolTip(self._t("desc_850_RSX_tag"))
            self.items_table.setItem(row, 5, item5)
            item6 = QTableWidgetItem(item["850_TLI_tag"])
            item6.setToolTip(self._t("desc_850_TLI_tag"))
            self.items_table.setItem(row, 6, item6)
            item7 = QTableWidgetItem(str(item["sourcing_group_properties_id"]))
            item7.setToolTip(self._t("desc_sourcing_group_id"))
            self.items_table.setItem(row, 7, item7)
            item8 = QTableWidgetItem("Yes" if item["is_on_detail_level"] else "No")
            item8.setToolTip(self._t("desc_is_on_detail_level"))
            self.items_table.setItem(row, 8, item8)
            item9 = QTableWidgetItem("Yes" if item["is_partnumber"] else "No")
            item9.setToolTip(self._t("desc_is_partnumber"))
            self.items_table.setItem(row, 9, item9)
            item10 = QTableWidgetItem(item["855_RSX_path"])
            item10.setToolTip(self._t("desc_855_RSX_path"))
            self.items_table.setItem(row, 10, item10)
            item11 = QTableWidgetItem(item["856_RSX_path"])
            item11.setToolTip(self._t("desc_856_RSX_path"))
            self.items_table.setItem(row, 11, item11)
            item12 = QTableWidgetItem(item["810_RSX_path"])
            item12.setToolTip(self._t("desc_810_RSX_path"))
            self.items_table.setItem(row, 12, item12)
        self.items_table.resizeColumnsToContents()

    def get_selected_sourcing_group_id(self) -> Optional[int]:
        """Get selected sourcing group ID"""
        selected = self.sourcing_table.selectedItems()
        if selected:
            row = selected[0].row()
            id_item = self.sourcing_table.item(row, 0)
            if id_item:
                return int(id_item.text())
        return None

    def get_selected_item_id(self) -> Optional[int]:
        """Get selected item ID"""
        selected = self.items_table.selectedItems()
        if selected:
            row = selected[0].row()
            id_item = self.items_table.item(row, 0)
            if id_item:
                return int(id_item.text())
        return None

    def get_selected_order_path_id(self) -> Optional[int]:
        """Get selected order path ID"""
        selected = self.order_path_table.selectedItems()
        if selected:
            row = selected[0].row()
            id_item = self.order_path_table.item(row, 0)
            if id_item:
                return int(id_item.text())
        return None

    def add_sourcing_group(self) -> None:
        """Add new sourcing group"""
        dialog = SourcingGroupDialog(self.database, self.current_language, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_sourcing_group(self) -> None:
        """Edit selected sourcing group"""
        group_id = self.get_selected_sourcing_group_id()
        if not group_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        group = self.database.get_sourcing_group(group_id)
        if group:
            dialog = SourcingGroupDialog(
                self.database, self.current_language, self, group
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def delete_sourcing_group(self) -> None:
        """Delete selected sourcing group"""
        group_id = self.get_selected_sourcing_group_id()
        if not group_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        reply = QMessageBox.question(
            self,
            self._t("confirm_delete"),
            self._t("confirm_delete_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_sourcing_group(group_id):
                self.load_data()
            else:
                QMessageBox.warning(
                    self, self._t("error"), self._t("cannot_delete_has_items")
                )

    def add_item(self) -> None:
        """Add new item"""
        dialog = ItemDialog(self.database, self.current_language, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_item(self) -> None:
        """Edit selected item"""
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        item = self.database.get_item(item_id)
        if item:
            dialog = ItemDialog(self.database, self.current_language, self, item)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def clone_item(self) -> None:
        """Clone selected item"""
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        item = self.database.get_item(item_id)
        if item:
            # Remove ID to create new item
            item.pop("item_properties_id", None)
            dialog = ItemDialog(self.database, self.current_language, self, item)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def delete_item(self) -> None:
        """Delete selected item"""
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        reply = QMessageBox.question(
            self,
            self._t("confirm_delete"),
            self._t("confirm_delete_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_item(item_id):
                self.load_data()
            else:
                QMessageBox.warning(self, self._t("error"), self._t("delete_failed"))

    def clone_sourcing_group(self) -> None:
        """Clone selected sourcing group"""
        group_id = self.get_selected_sourcing_group_id()
        if not group_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        group = self.database.get_sourcing_group(group_id)
        if group:
            # Remove ID to create new group
            group.pop("sourcing_group_properties_id", None)
            dialog = SourcingGroupDialog(self.database, self.current_language, self, group)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def add_order_path(self) -> None:
        """Add new order path"""
        dialog = OrderPathDialog(self.database, self.current_language, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_order_path(self) -> None:
        """Edit selected order path"""
        path_id = self.get_selected_order_path_id()
        if not path_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        path = self.database.get_order_path(path_id)
        if path:
            dialog = OrderPathDialog(
                self.database, self.current_language, self, path
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def clone_order_path(self) -> None:
        """Clone selected order path"""
        path_id = self.get_selected_order_path_id()
        if not path_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        path = self.database.get_order_path(path_id)
        if path:
            # Remove ID to create new path
            path.pop("order_path_properties_id", None)
            dialog = OrderPathDialog(self.database, self.current_language, self, path)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def delete_order_path(self) -> None:
        """Delete selected order path"""
        path_id = self.get_selected_order_path_id()
        if not path_id:
            QMessageBox.warning(self, self._t("error"), self._t("select_record"))
            return

        reply = QMessageBox.question(
            self,
            self._t("confirm_delete"),
            self._t("confirm_delete_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_order_path(path_id):
                self.load_data()
            else:
                QMessageBox.warning(
                    self, self._t("error"), self._t("cannot_delete_has_groups")
                )


class SourcingGroupDialog(QDialog):
    """Dialog for editing sourcing group properties"""

    def __init__(
        self,
        database: Database,
        current_language: str,
        parent=None,
        group_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.current_language = current_language
        self.group_data = group_data
        self.setWindowTitle(
            self._t("edit_sourcing_group") if group_data else self._t("add_sourcing_group")
        )
        self.setMinimumWidth(600)
        self.create_ui()

    def _t(self, key: str) -> str:
        """Get translation"""
        return TRANSLATIONS[self.current_language].get(key, key)
    
    def _create_help_button(self, description_key: str) -> QPushButton:
        """Create a help button with question mark that shows description"""
        help_btn = QPushButton("?")
        help_btn.setMaximumWidth(25)
        help_btn.setMaximumHeight(25)
        help_btn.setToolTip(self._t("click_for_description"))
        
        def show_description():
            QMessageBox.information(
                self,
                self._t("field_description"),
                self._t(description_key)
            )
        
        help_btn.clicked.connect(show_description)  # type: ignore[arg-type]
        return help_btn

    def create_ui(self) -> None:
        """Create user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Use GridLayout for three aligned columns: Label | Help Button | Input Field
        grid = QGridLayout()
        grid.setColumnStretch(2, 1)  # Make input field column stretchable

        self.populate_method_field = QLineEdit()
        self.populate_method_field.setToolTip(self._t("desc_populate_method_name"))
        self.populate_method_field.setMinimumWidth(400)
        self.map_name_field = QLineEdit()
        self.map_name_field.setToolTip(self._t("desc_map_name"))
        self.map_name_field.setMinimumWidth(400)
        
        # Order path combo (used for call_method_path selection)
        paths = self.database.get_all_order_paths()
        self.order_path_combo = QComboBox()
        self.order_path_combo.setToolTip(self._t("desc_call_method_path"))
        self.order_path_combo.setMinimumWidth(400)
        for path in paths:
            self.order_path_combo.addItem(
                f"{path['order_path_properties_id']}: {path['order_path']}",
                path["order_path_properties_id"],
            )
        
        self.call_method_java_code_field = QTextEdit()
        self.call_method_java_code_field.setToolTip(self._t("desc_call_method_java_code"))
        self.call_method_java_code_field.setMinimumWidth(400)
        self.call_method_java_code_field.setMinimumHeight(150)  # 7 rows approximately
        self.call_method_java_code_field.setMaximumHeight(150)

        # Row 0: populate_method_name
        grid.addWidget(QLabel(self._t("populate_method_name") + ":"), 0, 0)
        grid.addWidget(self._create_help_button("desc_populate_method_name"), 0, 1)
        grid.addWidget(self.populate_method_field, 0, 2)
        
        # Row 1: map_name
        grid.addWidget(QLabel(self._t("map_name") + ":"), 1, 0)
        grid.addWidget(self._create_help_button("desc_map_name"), 1, 1)
        grid.addWidget(self.map_name_field, 1, 2)
        
        # Row 2: call_method_path (using order_path_combo for selection)
        grid.addWidget(QLabel(self._t("call_method_path") + ":"), 2, 0)
        grid.addWidget(self._create_help_button("desc_call_method_path"), 2, 1)
        grid.addWidget(self.order_path_combo, 2, 2)
        
        # Row 3: call_method_java_code
        grid.addWidget(QLabel(self._t("call_method_java_code") + ":"), 3, 0)
        grid.addWidget(self._create_help_button("desc_call_method_java_code"), 3, 1)
        grid.addWidget(self.call_method_java_code_field, 3, 2)
        
        layout.addLayout(grid)

        if self.group_data:
            self.populate_method_field.setText(self.group_data["populate_method_name"])
            self.map_name_field.setText(self.group_data["map_name"])
            # Set order path
            order_path_id = self.group_data.get("order_path_properties_id")
            if order_path_id:
                index = self.order_path_combo.findData(order_path_id)
                if index >= 0:
                    self.order_path_combo.setCurrentIndex(index)
            # Set java code
            java_code = self.group_data.get("call_method_java_code", "")
            self.call_method_java_code_field.setPlainText(java_code)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_dialog)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

    def accept_dialog(self) -> None:
        """Handle OK button click"""
        populate_method = self.populate_method_field.text().strip()
        map_name = self.map_name_field.text().strip()
        order_path_id = self.order_path_combo.currentData()
        call_method_java_code = self.call_method_java_code_field.toPlainText().strip()

        if not all([populate_method, map_name, call_method_java_code]):
            QMessageBox.warning(self, self._t("error"), self._t("fill_all_fields"))
            return

        if order_path_id is None:
            QMessageBox.warning(self, self._t("error"), self._t("select_order_path"))
            return

        if self.group_data:
            self.database.update_sourcing_group(
                self.group_data["sourcing_group_properties_id"],
                populate_method,
                map_name,
                order_path_id,
                call_method_java_code,
            )
        else:
            self.database.create_sourcing_group(
                populate_method, map_name, order_path_id, call_method_java_code
            )

        self.accept()


class ItemDialog(QDialog):
    """Dialog for editing item properties"""

    def __init__(
        self,
        database: Database,
        current_language: str,
        parent=None,
        item_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.current_language = current_language
        self.item_data = item_data
        self.setWindowTitle(self._t("edit_item") if item_data else self._t("add_item"))
        self.setMinimumWidth(600)
        self.create_ui()

    def _t(self, key: str) -> str:
        """Get translation"""
        return TRANSLATIONS[self.current_language].get(key, key)
    
    def _create_help_button(self, description_key: str) -> QPushButton:
        """Create a help button with question mark that shows description"""
        help_btn = QPushButton("?")
        help_btn.setMaximumWidth(25)
        help_btn.setMaximumHeight(25)
        help_btn.setToolTip(self._t("click_for_description"))
        
        def show_description():
            QMessageBox.information(
                self,
                self._t("field_description"),
                self._t(description_key)
            )
        
        help_btn.clicked.connect(show_description)  # type: ignore[arg-type]
        return help_btn

    def create_ui(self) -> None:
        """Create user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        scroll = QWidget()
        scroll_layout = QVBoxLayout()
        scroll.setLayout(scroll_layout)

        # Use GridLayout for three aligned columns: Label | Help Button | Input Field
        grid = QGridLayout()
        grid.setColumnStretch(2, 1)  # Make input field column stretchable

        self.edi_segment_field = QLineEdit()
        self.edi_segment_field.setToolTip(self._t("desc_edi_segment"))
        self.edi_segment_field.setMinimumWidth(400)
        self.edi_element_number_field = QLineEdit()
        self.edi_element_number_field.setToolTip(self._t("desc_edi_element_number"))
        self.edi_element_number_field.setMinimumWidth(400)
        self.edi_element_number_field.setPlaceholderText("01, 02, 03, ...")
        self.edi_qualifier_field = QLineEdit()
        self.edi_qualifier_field.setToolTip(self._t("desc_edi_qualifier"))
        self.edi_qualifier_field.setMinimumWidth(400)
        self.TLI_value_field = QLineEdit()
        self.TLI_value_field.setToolTip(self._t("desc_TLI_value"))
        self.TLI_value_field.setMinimumWidth(400)
        self.rsx_850_tag_field = QLineEdit()
        self.rsx_850_tag_field.setToolTip(self._t("desc_850_RSX_tag"))
        self.rsx_850_tag_field.setMinimumWidth(400)
        self.tli_850_tag_field = QLineEdit()
        self.tli_850_tag_field.setToolTip(self._t("desc_850_TLI_tag"))
        self.tli_850_tag_field.setMinimumWidth(400)

        # Sourcing group combo
        groups = self.database.get_all_sourcing_groups()
        self.sourcing_group_combo = QComboBox()
        self.sourcing_group_combo.setToolTip(self._t("desc_sourcing_group_id"))
        self.sourcing_group_combo.setMinimumWidth(400)
        for group in groups:
            self.sourcing_group_combo.addItem(
                f"{group['sourcing_group_properties_id']}: {group['map_name']}",
                group["sourcing_group_properties_id"],
            )

        self.is_on_detail_level_check = QCheckBox()
        self.is_on_detail_level_check.setToolTip(self._t("desc_is_on_detail_level"))
        self.is_on_detail_level_check.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")
        self.is_partnumber_check = QCheckBox()
        self.is_partnumber_check.setToolTip(self._t("desc_is_partnumber"))
        self.is_partnumber_check.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")

        self.rsx_855_path_field = QLineEdit()
        self.rsx_855_path_field.setToolTip(self._t("desc_855_RSX_path"))
        self.rsx_855_path_field.setMinimumWidth(400)
        self.rsx_856_path_field = QLineEdit()
        self.rsx_856_path_field.setToolTip(self._t("desc_856_RSX_path"))
        self.rsx_856_path_field.setMinimumWidth(400)
        self.rsx_810_path_field = QLineEdit()
        self.rsx_810_path_field.setToolTip(self._t("desc_810_RSX_path"))
        self.rsx_810_path_field.setMinimumWidth(400)

        # Add rows to grid: Column 0 = Label, Column 1 = Help Button, Column 2 = Input Field
        row = 0
        grid.addWidget(QLabel(self._t("edi_segment") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_edi_segment"), row, 1)
        grid.addWidget(self.edi_segment_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("edi_element_number") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_edi_element_number"), row, 1)
        grid.addWidget(self.edi_element_number_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("edi_qualifier") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_edi_qualifier"), row, 1)
        grid.addWidget(self.edi_qualifier_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("TLI_value") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_TLI_value"), row, 1)
        grid.addWidget(self.TLI_value_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("850_RSX_tag") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_850_RSX_tag"), row, 1)
        grid.addWidget(self.rsx_850_tag_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("850_TLI_tag") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_850_TLI_tag"), row, 1)
        grid.addWidget(self.tli_850_tag_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("sourcing_group_id") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_sourcing_group_id"), row, 1)
        grid.addWidget(self.sourcing_group_combo, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("is_on_detail_level") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_is_on_detail_level"), row, 1)
        grid.addWidget(self.is_on_detail_level_check, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("is_partnumber") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_is_partnumber"), row, 1)
        grid.addWidget(self.is_partnumber_check, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("855_RSX_path") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_855_RSX_path"), row, 1)
        grid.addWidget(self.rsx_855_path_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("856_RSX_path") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_856_RSX_path"), row, 1)
        grid.addWidget(self.rsx_856_path_field, row, 2)
        row += 1
        
        grid.addWidget(QLabel(self._t("810_RSX_path") + ":"), row, 0)
        grid.addWidget(self._create_help_button("desc_810_RSX_path"), row, 1)
        grid.addWidget(self.rsx_810_path_field, row, 2)

        scroll_layout.addLayout(grid)
        scroll_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        if self.item_data:
            self.edi_segment_field.setText(self.item_data["edi_segment"])
            # Format edi_element_number as 01, 02, 03, etc.
            edi_element_str = f"{self.item_data['edi_element_number']:02d}"
            self.edi_element_number_field.setText(edi_element_str)
            self.edi_qualifier_field.setText(self.item_data["edi_qualifier"] or "")
            self.TLI_value_field.setText(self.item_data["TLI_value"])
            self.rsx_850_tag_field.setText(self.item_data["850_RSX_tag"])
            self.tli_850_tag_field.setText(self.item_data["850_TLI_tag"])

            # Set sourcing group
            index = self.sourcing_group_combo.findData(
                self.item_data["sourcing_group_properties_id"]
            )
            if index >= 0:
                self.sourcing_group_combo.setCurrentIndex(index)

            self.is_on_detail_level_check.setChecked(self.item_data["is_on_detail_level"])
            self.is_partnumber_check.setChecked(self.item_data["is_partnumber"])
            self.rsx_855_path_field.setText(self.item_data["855_RSX_path"])
            self.rsx_856_path_field.setText(self.item_data["856_RSX_path"])
            self.rsx_810_path_field.setText(self.item_data["810_RSX_path"])

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_dialog)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

    def accept_dialog(self) -> None:
        """Handle OK button click"""
        edi_segment = self.edi_segment_field.text().strip()
        # Parse edi_element_number (accepts both "01" and "1")
        edi_element_text = self.edi_element_number_field.text().strip()
        try:
            edi_element_number = int(edi_element_text)
        except ValueError:
            QMessageBox.warning(self, self._t("error"), self._t("invalid_edi_element_number"))
            return
        edi_qualifier = self.edi_qualifier_field.text().strip() or None
        TLI_value = self.TLI_value_field.text().strip()
        rsx_850_tag = self.rsx_850_tag_field.text().strip()
        tli_850_tag = self.tli_850_tag_field.text().strip()
        sourcing_group_id = self.sourcing_group_combo.currentData()
        is_on_detail_level = self.is_on_detail_level_check.isChecked()
        is_partnumber = self.is_partnumber_check.isChecked()
        rsx_855_path = self.rsx_855_path_field.text().strip()
        rsx_856_path = self.rsx_856_path_field.text().strip()
        rsx_810_path = self.rsx_810_path_field.text().strip()

        if not all([
            edi_segment,
            TLI_value,
            rsx_850_tag,
            tli_850_tag,
            rsx_855_path,
            rsx_856_path,
            rsx_810_path,
        ]):
            QMessageBox.warning(self, self._t("error"), self._t("fill_all_fields"))
            return

        if sourcing_group_id is None:
            QMessageBox.warning(self, self._t("error"), self._t("select_sourcing_group"))
            return

        if self.item_data:
            self.database.update_item(
                self.item_data["item_properties_id"],
                edi_segment,
                edi_element_number,
                edi_qualifier,
                TLI_value,
                rsx_850_tag,
                tli_850_tag,
                sourcing_group_id,
                is_on_detail_level,
                is_partnumber,
                rsx_855_path,
                rsx_856_path,
                rsx_810_path,
            )
        else:
            self.database.create_item(
                edi_segment,
                edi_element_number,
                edi_qualifier,
                TLI_value,
                rsx_850_tag,
                tli_850_tag,
                sourcing_group_id,
                is_on_detail_level,
                is_partnumber,
                rsx_855_path,
                rsx_856_path,
                rsx_810_path,
            )

        self.accept()


class OrderPathDialog(QDialog):
    """Dialog for editing order path properties"""

    def __init__(
        self,
        database: Database,
        current_language: str,
        parent=None,
        path_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.current_language = current_language
        self.path_data = path_data
        self.setWindowTitle(
            self._t("edit_order_path") if path_data else self._t("add_order_path")
        )
        self.setMinimumWidth(600)
        self.create_ui()

    def _t(self, key: str) -> str:
        """Get translation"""
        return TRANSLATIONS[self.current_language].get(key, key)
    
    def _create_help_button(self, description_key: str) -> QPushButton:
        """Create a help button with question mark that shows description"""
        help_btn = QPushButton("?")
        help_btn.setMaximumWidth(25)
        help_btn.setMaximumHeight(25)
        help_btn.setToolTip(self._t("click_for_description"))
        
        def show_description():
            QMessageBox.information(
                self,
                self._t("field_description"),
                self._t(description_key)
            )
        
        help_btn.clicked.connect(show_description)  # type: ignore[arg-type]
        return help_btn

    def create_ui(self) -> None:
        """Create user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Use GridLayout for three aligned columns: Label | Help Button | Input Field
        grid = QGridLayout()
        grid.setColumnStretch(2, 1)  # Make input field column stretchable

        self.order_path_field = QLineEdit()
        self.order_path_field.setToolTip(self._t("desc_order_path"))
        self.order_path_field.setMinimumWidth(400)
        
        self.java_code_wrapper_field = QTextEdit()
        self.java_code_wrapper_field.setToolTip(self._t("desc_java_code_wrapper"))
        self.java_code_wrapper_field.setMinimumWidth(400)
        self.java_code_wrapper_field.setMinimumHeight(150)  # 7 rows approximately
        self.java_code_wrapper_field.setMaximumHeight(150)

        # Row 0: order_path
        grid.addWidget(QLabel(self._t("order_path") + ":"), 0, 0)
        grid.addWidget(self._create_help_button("desc_order_path"), 0, 1)
        grid.addWidget(self.order_path_field, 0, 2)
        
        # Row 1: java_code_wrapper
        grid.addWidget(QLabel(self._t("java_code_wrapper") + ":"), 1, 0)
        grid.addWidget(self._create_help_button("desc_java_code_wrapper"), 1, 1)
        grid.addWidget(self.java_code_wrapper_field, 1, 2)
        
        layout.addLayout(grid)

        if self.path_data:
            self.order_path_field.setText(self.path_data["order_path"])
            java_wrapper = self.path_data.get("java_code_wrapper", "")
            self.java_code_wrapper_field.setPlainText(java_wrapper)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_dialog)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

    def accept_dialog(self) -> None:
        """Handle OK button click"""
        order_path = self.order_path_field.text().strip()
        java_code_wrapper = self.java_code_wrapper_field.toPlainText().strip()

        if not order_path:
            QMessageBox.warning(self, self._t("error"), self._t("fill_all_fields"))
            return

        if self.path_data:
            self.database.update_order_path(
                self.path_data["order_path_properties_id"],
                order_path,
                java_code_wrapper if java_code_wrapper else None,
            )
        else:
            self.database.create_order_path(
                order_path,
                java_code_wrapper if java_code_wrapper else None,
            )

        self.accept()

