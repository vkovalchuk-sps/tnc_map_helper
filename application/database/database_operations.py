"""Database module for SQLite operations"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DuplicateItemError(Exception):
    """Exception raised when trying to create/update item with duplicate EDI combination"""
    
    def __init__(self, edi_segment: str, edi_element_number: int, edi_qualifier: str):
        self.edi_segment = edi_segment
        self.edi_element_number = edi_element_number
        self.edi_qualifier = edi_qualifier
        super().__init__()


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

        # Create or migrate order_path_properties table first (referenced by sourcing_group_properties)
        cursor.execute("PRAGMA table_info(order_path_properties)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        if not existing_columns:
            # Fresh database – create table with new schema
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS order_path_properties (
                    order_path_properties_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_path TEXT NOT NULL,
                    xtl_part_to_replace_850 TEXT NOT NULL,
                    xtl_part_to_paste_850 TEXT NOT NULL,
                    xtl_part_to_replace_860 TEXT NOT NULL,
                    xtl_part_to_paste_860 TEXT NOT NULL
                )
                """
            )
        elif "xtl_part_to_replace_850" not in existing_columns:
            # Old schema detected – migrate to new columns, drop order_change_path/java_code_wrapper
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS order_path_properties_new (
                    order_path_properties_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_path TEXT NOT NULL,
                    xtl_part_to_replace_850 TEXT NOT NULL,
                    xtl_part_to_paste_850 TEXT NOT NULL,
                    xtl_part_to_replace_860 TEXT NOT NULL,
                    xtl_part_to_paste_860 TEXT NOT NULL
                )
                """
            )

            # Preserve existing IDs and order_path; initialize new columns as empty strings
            cursor.execute(
                """
                INSERT INTO order_path_properties_new (
                    order_path_properties_id,
                    order_path,
                    xtl_part_to_replace_850,
                    xtl_part_to_paste_850,
                    xtl_part_to_replace_860,
                    xtl_part_to_paste_860
                )
                SELECT
                    order_path_properties_id,
                    order_path,
                    '',
                    '',
                    '',
                    ''
                FROM order_path_properties
                """
            )

            cursor.execute("DROP TABLE order_path_properties")
            cursor.execute("ALTER TABLE order_path_properties_new RENAME TO order_path_properties")

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
            # Check if old column exists and needs migration
            cursor.execute("PRAGMA table_info(sourcing_group_properties)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if "call_method_path" in columns:
                # Migration: remove call_method_path column by recreating table without it
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sourcing_group_properties_new (
                        sourcing_group_properties_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        populate_method_name TEXT NOT NULL,
                        map_name TEXT NOT NULL,
                        order_path_properties_id INTEGER NOT NULL,
                        call_method_java_code TEXT NOT NULL,
                        FOREIGN KEY (order_path_properties_id) 
                            REFERENCES order_path_properties(order_path_properties_id)
                    )
                """)
                
                # Copy data (excluding call_method_path)
                cursor.execute("""
                    INSERT INTO sourcing_group_properties_new (
                        sourcing_group_properties_id, populate_method_name, map_name,
                        order_path_properties_id, call_method_java_code
                    )
                    SELECT
                        sourcing_group_properties_id, populate_method_name, map_name,
                        order_path_properties_id, call_method_java_code
                    FROM sourcing_group_properties
                """)
                
                # Drop old table and rename
                cursor.execute("DROP TABLE sourcing_group_properties")
                cursor.execute("ALTER TABLE sourcing_group_properties_new RENAME TO sourcing_group_properties")
        except Exception:
            pass  # Migration failed, continue with new schema

        # Create item_properties table
        # Note: Boolean columns (is_on_detail_level, is_partnumber, put_in_*_by_default) use INTEGER (0/1)
        # as SQLite doesn't have a native BOOLEAN type
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
                put_in_855_by_default INTEGER NOT NULL DEFAULT 0,
                "856_RSX_path" TEXT NOT NULL,
                put_in_856_by_default INTEGER NOT NULL DEFAULT 0,
                "810_RSX_path" TEXT NOT NULL,
                put_in_810_by_default INTEGER NOT NULL DEFAULT 0,
                extra_record_defining_rsx_tag TEXT,
                extra_record_defining_qual TEXT,
                FOREIGN KEY (sourcing_group_properties_id) 
                    REFERENCES sourcing_group_properties(sourcing_group_properties_id)
            )
        """)

        # Ensure optional columns exist for older databases and migrate if needed
        additional_columns = [
            ("put_in_855_by_default", "ALTER TABLE item_properties ADD COLUMN put_in_855_by_default INTEGER NOT NULL DEFAULT 0"),
            ("put_in_856_by_default", "ALTER TABLE item_properties ADD COLUMN put_in_856_by_default INTEGER NOT NULL DEFAULT 0"),
            ("put_in_810_by_default", "ALTER TABLE item_properties ADD COLUMN put_in_810_by_default INTEGER NOT NULL DEFAULT 0"),
            ("extra_record_defining_rsx_tag", "ALTER TABLE item_properties ADD COLUMN extra_record_defining_rsx_tag TEXT"),
            ("extra_record_defining_qual", "ALTER TABLE item_properties ADD COLUMN extra_record_defining_qual TEXT"),
        ]
        for column_name, ddl in additional_columns:
            if not self._table_has_column(cursor, "item_properties", column_name):
                cursor.execute(ddl)

        # Migration: Remove description column if it exists (not used anywhere)
        if self._table_has_column(cursor, "item_properties", "description"):
            try:
                # SQLite: recreate table without description column
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS item_properties_new (
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
                        put_in_855_by_default INTEGER NOT NULL DEFAULT 0,
                        "856_RSX_path" TEXT NOT NULL,
                        put_in_856_by_default INTEGER NOT NULL DEFAULT 0,
                        "810_RSX_path" TEXT NOT NULL,
                        put_in_810_by_default INTEGER NOT NULL DEFAULT 0,
                        extra_record_defining_rsx_tag TEXT,
                        extra_record_defining_qual TEXT,
                        FOREIGN KEY (sourcing_group_properties_id) 
                            REFERENCES sourcing_group_properties(sourcing_group_properties_id)
                    )
                """)
                
                # Copy data from old table to new table (excluding description)
                cursor.execute("""
                    INSERT INTO item_properties_new (
                        item_properties_id, edi_segment, edi_element_number, edi_qualifier,
                        TLI_value, "850_RSX_tag", "850_TLI_tag", sourcing_group_properties_id,
                        is_on_detail_level, is_partnumber, "855_RSX_path", put_in_855_by_default,
                        "856_RSX_path", put_in_856_by_default, "810_RSX_path", put_in_810_by_default,
                        extra_record_defining_rsx_tag, extra_record_defining_qual
                    )
                    SELECT
                        item_properties_id, edi_segment, edi_element_number, edi_qualifier,
                        TLI_value, "850_RSX_tag", "850_TLI_tag", sourcing_group_properties_id,
                        is_on_detail_level, is_partnumber, "855_RSX_path", put_in_855_by_default,
                        "856_RSX_path", put_in_856_by_default, "810_RSX_path", put_in_810_by_default,
                        extra_record_defining_rsx_tag, extra_record_defining_qual
                    FROM item_properties
                """)
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE item_properties")
                cursor.execute("ALTER TABLE item_properties_new RENAME TO item_properties")
                
                # Recreate the unique index
                try:
                    cursor.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_item_properties_unique_edi 
                        ON item_properties(edi_segment, edi_element_number, edi_qualifier)
                    """)
                except sqlite3.Error:
                    pass
            except sqlite3.Error:
                # If migration fails, continue (table may have been already migrated)
                pass

        # Create unique index for edi_segment, edi_element_number, edi_qualifier combination
        # Note: Since we normalize edi_qualifier to empty string (not NULL) in create/update,
        # we can create a simple unique index. The manual check in create/update methods
        # provides additional validation.
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_item_properties_unique_edi 
                ON item_properties(edi_segment, edi_element_number, edi_qualifier)
            """)
        except sqlite3.Error:
            # Index creation might fail if duplicates exist, but manual check will handle it
            pass

        # Create metadata table for storing database version and other metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Set default database content version if not exists
        cursor.execute("SELECT value FROM metadata WHERE key = 'db_content_version'")
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO metadata (key, value) VALUES ('db_content_version', '1.0')")

        conn.commit()
        conn.close()

    # Order Path Properties CRUD operations
    def create_order_path(
        self,
        order_path: str,
        xtl_part_to_replace_850: str,
        xtl_part_to_paste_850: str,
        xtl_part_to_replace_860: str,
        xtl_part_to_paste_860: str,
    ) -> int:
        """Create a new order path property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO order_path_properties (
                order_path,
                xtl_part_to_replace_850,
                xtl_part_to_paste_850,
                xtl_part_to_replace_860,
                xtl_part_to_paste_860
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_path,
                xtl_part_to_replace_850,
                xtl_part_to_paste_850,
                xtl_part_to_replace_860,
                xtl_part_to_paste_860,
            ),
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
        result = []
        for row in rows:
            item = dict(row)
            item["is_on_detail_level"] = bool(item.get("is_on_detail_level", 0))
            item["is_partnumber"] = bool(item.get("is_partnumber", 0))
            item["put_in_855_by_default"] = bool(item.get("put_in_855_by_default", 0))
            item["put_in_856_by_default"] = bool(item.get("put_in_856_by_default", 0))
            item["put_in_810_by_default"] = bool(item.get("put_in_810_by_default", 0))
            result.append(item)
        return result

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
        xtl_part_to_replace_850: str,
        xtl_part_to_paste_850: str,
        xtl_part_to_replace_860: str,
        xtl_part_to_paste_860: str,
    ) -> bool:
        """Update order path property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE order_path_properties
            SET order_path = ?,
                xtl_part_to_replace_850 = ?,
                xtl_part_to_paste_850 = ?,
                xtl_part_to_replace_860 = ?,
                xtl_part_to_paste_860 = ?
            WHERE order_path_properties_id = ?
            """,
            (
                order_path,
                xtl_part_to_replace_850,
                xtl_part_to_paste_850,
                xtl_part_to_replace_860,
                xtl_part_to_paste_860,
                path_id,
            ),
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
            SELECT s.*, o.order_path
            FROM sourcing_group_properties s
            LEFT JOIN order_path_properties o ON s.order_path_properties_id = o.order_path_properties_id
            ORDER BY s.sourcing_group_properties_id
        """)
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            result.append(d)
        return result

    def get_sourcing_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get sourcing group property by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, o.order_path
            FROM sourcing_group_properties s
            LEFT JOIN order_path_properties o ON s.order_path_properties_id = o.order_path_properties_id
            WHERE s.sourcing_group_properties_id = ?
        """, (group_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
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

    def _table_has_column(self, cursor, table_name: str, column_name: str) -> bool:
        """Check if a table contains a specific column"""
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            return any(col[1] == column_name for col in columns)
        except sqlite3.Error:
            return False

    def _get_order_path_value(self, cursor, order_path_properties_id: int) -> str:
        """Get order path string for given order_path_properties_id"""
        cursor.execute(
            "SELECT order_path FROM order_path_properties WHERE order_path_properties_id = ?",
            (order_path_properties_id,),
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else ""

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
        put_in_855_by_default: bool,
        rsx_856_path: str,
        put_in_856_by_default: bool,
        rsx_810_path: str,
        put_in_810_by_default: bool,
        extra_record_defining_rsx_tag: Optional[str] = None,
        extra_record_defining_qual: Optional[str] = None,
    ) -> int:
        """Create a new item property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check for uniqueness: edi_segment, edi_element_number, edi_qualifier combination
        # Normalize edi_qualifier: treat None and empty string as the same
        normalized_qualifier = (edi_qualifier or "").strip()
        
        cursor.execute("""
            SELECT item_properties_id FROM item_properties
            WHERE edi_segment = ? AND edi_element_number = ?
            AND COALESCE(edi_qualifier, '') = ?
        """, (edi_segment, edi_element_number, normalized_qualifier))
        
        existing_item = cursor.fetchone()
        if existing_item:
            conn.close()
            raise DuplicateItemError(edi_segment, edi_element_number, normalized_qualifier)
        
        cursor.execute(
            """
            INSERT INTO item_properties 
            (edi_segment, edi_element_number, edi_qualifier, TLI_value,
             "850_RSX_tag", "850_TLI_tag", sourcing_group_properties_id,
             is_on_detail_level, is_partnumber, "855_RSX_path", put_in_855_by_default,
             "856_RSX_path", put_in_856_by_default, "810_RSX_path", put_in_810_by_default,
             extra_record_defining_rsx_tag, extra_record_defining_qual)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edi_segment,
                edi_element_number,
                normalized_qualifier or "",
                TLI_value,
                rsx_850_tag,
                tli_850_tag,
                sourcing_group_properties_id,
                1 if is_on_detail_level else 0,
                1 if is_partnumber else 0,
                rsx_855_path,
                1 if put_in_855_by_default else 0,
                rsx_856_path,
                1 if put_in_856_by_default else 0,
                rsx_810_path,
                1 if put_in_810_by_default else 0,
                extra_record_defining_rsx_tag,
                extra_record_defining_qual,
            ),
        )
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return item_id

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all item properties with sourcing group details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, s.map_name
            FROM item_properties i
            LEFT JOIN sourcing_group_properties s ON i.sourcing_group_properties_id = s.sourcing_group_properties_id
            ORDER BY i.item_properties_id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get item property by ID with sourcing group details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.*, s.map_name
            FROM item_properties i
            LEFT JOIN sourcing_group_properties s ON i.sourcing_group_properties_id = s.sourcing_group_properties_id
            WHERE i.item_properties_id = ?
        """, (item_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            item = dict(row)
            # Convert boolean fields
            item["is_on_detail_level"] = bool(item.get("is_on_detail_level", 0))
            item["is_partnumber"] = bool(item.get("is_partnumber", 0))
            item["put_in_855_by_default"] = bool(item.get("put_in_855_by_default", 0))
            item["put_in_856_by_default"] = bool(item.get("put_in_856_by_default", 0))
            item["put_in_810_by_default"] = bool(item.get("put_in_810_by_default", 0))
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
        put_in_855_by_default: bool,
        rsx_856_path: str,
        put_in_856_by_default: bool,
        rsx_810_path: str,
        put_in_810_by_default: bool,
        extra_record_defining_rsx_tag: Optional[str] = None,
        extra_record_defining_qual: Optional[str] = None,
    ) -> bool:
        """Update item property"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check for uniqueness: edi_segment, edi_element_number, edi_qualifier combination
        # Normalize edi_qualifier: treat None and empty string as the same
        normalized_qualifier = (edi_qualifier or "").strip()
        
        # Check if another item with the same combination exists (excluding current item)
        cursor.execute("""
            SELECT item_properties_id FROM item_properties
            WHERE edi_segment = ? AND edi_element_number = ?
            AND COALESCE(edi_qualifier, '') = ?
            AND item_properties_id != ?
        """, (edi_segment, edi_element_number, normalized_qualifier, item_id))
        
        existing_item = cursor.fetchone()
        if existing_item:
            conn.close()
            raise DuplicateItemError(edi_segment, edi_element_number, normalized_qualifier)
        
        cursor.execute(
            """
            UPDATE item_properties
            SET edi_segment = ?, edi_element_number = ?, edi_qualifier = ?,
                TLI_value = ?, "850_RSX_tag" = ?, "850_TLI_tag" = ?,
                sourcing_group_properties_id = ?, is_on_detail_level = ?,
                is_partnumber = ?, "855_RSX_path" = ?, put_in_855_by_default = ?,
                "856_RSX_path" = ?, put_in_856_by_default = ?, "810_RSX_path" = ?, put_in_810_by_default = ?,
                extra_record_defining_rsx_tag = ?, extra_record_defining_qual = ?
            WHERE item_properties_id = ?
            """,
            (
                edi_segment,
                edi_element_number,
                normalized_qualifier or "",
                TLI_value,
                rsx_850_tag,
                tli_850_tag,
                sourcing_group_properties_id,
                1 if is_on_detail_level else 0,
                1 if is_partnumber else 0,
                rsx_855_path,
                1 if put_in_855_by_default else 0,
                rsx_856_path,
                1 if put_in_856_by_default else 0,
                rsx_810_path,
                1 if put_in_810_by_default else 0,
                extra_record_defining_rsx_tag,
                extra_record_defining_qual,
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

    # Metadata operations
    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value by key"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else None
    
    def get_db_version(self) -> str:
        """Get database content version"""
        version = self.get_metadata("db_content_version")
        return version if version else "1.0"
    
    def set_metadata(self, key: str, value: str) -> None:
        """Set metadata value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
        conn.close()
