"""Database module for SQLite operations"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class Database:
    """Manages SQLite database operations"""

    def __init__(self, db_path: Path) -> None:
        """
        Initialize Database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def init_database(self) -> None:
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create order_path_properties table first (referenced by sourcing_group_properties)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_path_properties (
                order_path_properties_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_path TEXT NOT NULL,
                java_code_wrapper TEXT
            )
        """)

        # Create sourcing_group_properties table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sourcing_group_properties (
                sourcing_group_properties_id INTEGER PRIMARY KEY AUTOINCREMENT,
                populate_method_name TEXT NOT NULL,
                map_name TEXT NOT NULL,
                order_path_properties_id INTEGER NOT NULL,
                call_method_java_code TEXT NOT NULL,
                FOREIGN KEY (order_path_properties_id) 
                    REFERENCES order_path_properties(order_path_properties_id)
            )
        """)

        # Migrate existing data if needed
        try:
            # Check if old column exists
            cursor.execute("PRAGMA table_info(sourcing_group_properties)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if "call_method_path" in columns and "order_path_properties_id" not in columns:
                # Migration: create order_path_properties entries and update sourcing_group_properties
                cursor.execute("SELECT DISTINCT call_method_path FROM sourcing_group_properties")
                paths = cursor.fetchall()
                
                path_to_id = {}
                for path_row in paths:
                    path = path_row[0]
                    cursor.execute(
                        "INSERT INTO order_path_properties (order_path) VALUES (?)",
                        (path,)
                    )
                    path_to_id[path] = cursor.lastrowid
                
                # Add new columns
                cursor.execute("ALTER TABLE sourcing_group_properties ADD COLUMN order_path_properties_id INTEGER")
                cursor.execute("ALTER TABLE sourcing_group_properties ADD COLUMN call_method_java_code TEXT DEFAULT ''")
                
                # Update existing rows
                cursor.execute("SELECT sourcing_group_properties_id, call_method_path FROM sourcing_group_properties")
                rows = cursor.fetchall()
                for row in rows:
                    group_id, path = row
                    path_id = path_to_id.get(path)
                    if path_id:
                        cursor.execute(
                            "UPDATE sourcing_group_properties SET order_path_properties_id = ?, call_method_java_code = ? WHERE sourcing_group_properties_id = ?",
                            (path_id, "", group_id)
                        )
                
                # Drop old column (SQLite doesn't support DROP COLUMN, so we'll recreate the table)
                # For now, we'll keep both columns for compatibility
        except Exception:
            pass  # Migration failed, continue with new schema

        # Create item_properties table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_properties (
                item_properties_id INTEGER PRIMARY KEY AUTOINCREMENT,
                edi_segment TEXT NOT NULL,
                edi_element_number INTEGER NOT NULL,
                edi_qualifier TEXT,
                TLI_value TEXT NOT NULL,
                "850_RSX_tag" TEXT NOT NULL,
                "850_TLI_tag" TEXT NOT NULL,
                sourcing_group_properties_id INTEGER NOT NULL,
                is_on_detail_level INTEGER NOT NULL DEFAULT 0,
                is_partnumber INTEGER NOT NULL DEFAULT 0,
                "855_RSX_path" TEXT NOT NULL,
                "856_RSX_path" TEXT NOT NULL,
                "810_RSX_path" TEXT NOT NULL,
                FOREIGN KEY (sourcing_group_properties_id) 
                    REFERENCES sourcing_group_properties(sourcing_group_properties_id)
            )
        """)

        conn.commit()
        conn.close()

    # Order Path Properties CRUD operations
    def create_order_path(
        self, order_path: str, java_code_wrapper: Optional[str] = None
    ) -> int:
        """Create a new order path property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO order_path_properties (order_path, java_code_wrapper)
            VALUES (?, ?)
            """,
            (order_path, java_code_wrapper or ""),
        )
        conn.commit()
        path_id = cursor.lastrowid
        conn.close()
        return path_id

    def get_all_order_paths(self) -> List[Dict[str, Any]]:
        """Get all order path properties"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM order_path_properties ORDER BY order_path_properties_id")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_order_path(self, path_id: int) -> Optional[Dict[str, Any]]:
        """Get order path property by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM order_path_properties WHERE order_path_properties_id = ?",
            (path_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_order_path(
        self,
        path_id: int,
        order_path: str,
        java_code_wrapper: Optional[str] = None,
    ) -> bool:
        """Update order path property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE order_path_properties
            SET order_path = ?, java_code_wrapper = ?
            WHERE order_path_properties_id = ?
            """,
            (order_path, java_code_wrapper or "", path_id),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def delete_order_path(self, path_id: int) -> bool:
        """Delete order path property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Check if there are sourcing groups using this path
        cursor.execute(
            "SELECT COUNT(*) FROM sourcing_group_properties WHERE order_path_properties_id = ?",
            (path_id,),
        )
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return False  # Cannot delete if sourcing groups reference it

        cursor.execute(
            "DELETE FROM order_path_properties WHERE order_path_properties_id = ?",
            (path_id,),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    # Sourcing Group Properties CRUD operations
    def create_sourcing_group(
        self,
        populate_method_name: str,
        map_name: str,
        order_path_properties_id: int,
        call_method_java_code: str,
    ) -> int:
        """Create a new sourcing group property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sourcing_group_properties 
            (populate_method_name, map_name, order_path_properties_id, call_method_java_code)
            VALUES (?, ?, ?, ?)
            """,
            (populate_method_name, map_name, order_path_properties_id, call_method_java_code),
        )
        conn.commit()
        group_id = cursor.lastrowid
        conn.close()
        return group_id

    def get_all_sourcing_groups(self) -> List[Dict[str, Any]]:
        """Get all sourcing group properties"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, o.order_path, o.java_code_wrapper
            FROM sourcing_group_properties s
            LEFT JOIN order_path_properties o ON s.order_path_properties_id = o.order_path_properties_id
            ORDER BY s.sourcing_group_properties_id
        """)
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            # Add call_method_path for backward compatibility
            if "order_path" in d:
                d["call_method_path"] = d["order_path"]
            result.append(d)
        return result

    def get_sourcing_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get sourcing group property by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, o.order_path, o.java_code_wrapper
            FROM sourcing_group_properties s
            LEFT JOIN order_path_properties o ON s.order_path_properties_id = o.order_path_properties_id
            WHERE s.sourcing_group_properties_id = ?
        """, (group_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            d = dict(row)
            # Add call_method_path for backward compatibility
            if "order_path" in d:
                d["call_method_path"] = d["order_path"]
            return d
        return None

    def update_sourcing_group(
        self,
        group_id: int,
        populate_method_name: str,
        map_name: str,
        order_path_properties_id: int,
        call_method_java_code: str,
    ) -> bool:
        """Update sourcing group property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE sourcing_group_properties
            SET populate_method_name = ?, map_name = ?, order_path_properties_id = ?, call_method_java_code = ?
            WHERE sourcing_group_properties_id = ?
            """,
            (populate_method_name, map_name, order_path_properties_id, call_method_java_code, group_id),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def delete_sourcing_group(self, group_id: int) -> bool:
        """Delete sourcing group property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Check if there are items using this group
        cursor.execute(
            "SELECT COUNT(*) FROM item_properties WHERE sourcing_group_properties_id = ?",
            (group_id,),
        )
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return False  # Cannot delete if items reference it

        cursor.execute(
            "DELETE FROM sourcing_group_properties WHERE sourcing_group_properties_id = ?",
            (group_id,),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    # Item Properties CRUD operations
    def create_item(
        self,
        edi_segment: str,
        edi_element_number: int,
        edi_qualifier: Optional[str],
        TLI_value: str,
        rsx_850_tag: str,
        tli_850_tag: str,
        sourcing_group_properties_id: int,
        is_on_detail_level: bool,
        is_partnumber: bool,
        rsx_855_path: str,
        rsx_856_path: str,
        rsx_810_path: str,
    ) -> int:
        """Create a new item property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO item_properties 
            (edi_segment, edi_element_number, edi_qualifier, TLI_value,
             "850_RSX_tag", "850_TLI_tag", sourcing_group_properties_id,
             is_on_detail_level, is_partnumber, "855_RSX_path", "856_RSX_path", "810_RSX_path")
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edi_segment,
                edi_element_number,
                edi_qualifier or "",
                TLI_value,
                rsx_850_tag,
                tli_850_tag,
                sourcing_group_properties_id,
                1 if is_on_detail_level else 0,
                1 if is_partnumber else 0,
                rsx_855_path,
                rsx_856_path,
                rsx_810_path,
            ),
        )
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return item_id

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all item properties"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM item_properties ORDER BY item_properties_id")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get item property by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM item_properties WHERE item_properties_id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            item = dict(row)
            # Convert boolean fields
            item["is_on_detail_level"] = bool(item["is_on_detail_level"])
            item["is_partnumber"] = bool(item["is_partnumber"])
            return item
        return None

    def update_item(
        self,
        item_id: int,
        edi_segment: str,
        edi_element_number: int,
        edi_qualifier: Optional[str],
        TLI_value: str,
        rsx_850_tag: str,
        tli_850_tag: str,
        sourcing_group_properties_id: int,
        is_on_detail_level: bool,
        is_partnumber: bool,
        rsx_855_path: str,
        rsx_856_path: str,
        rsx_810_path: str,
    ) -> bool:
        """Update item property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE item_properties
            SET edi_segment = ?, edi_element_number = ?, edi_qualifier = ?,
                TLI_value = ?, "850_RSX_tag" = ?, "850_TLI_tag" = ?,
                sourcing_group_properties_id = ?, is_on_detail_level = ?,
                is_partnumber = ?, "855_RSX_path" = ?, "856_RSX_path" = ?, "810_RSX_path" = ?
            WHERE item_properties_id = ?
            """,
            (
                edi_segment,
                edi_element_number,
                edi_qualifier or "",
                TLI_value,
                rsx_850_tag,
                tli_850_tag,
                sourcing_group_properties_id,
                1 if is_on_detail_level else 0,
                1 if is_partnumber else 0,
                rsx_855_path,
                rsx_856_path,
                rsx_810_path,
                item_id,
            ),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def delete_item(self, item_id: int) -> bool:
        """Delete item property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM item_properties WHERE item_properties_id = ?", (item_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

