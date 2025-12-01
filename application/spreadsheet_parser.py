"""Spreadsheet parser module for parsing Excel files and creating Item objects"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import openpyxl
from openpyxl import load_workbook

from application.translations import TRANSLATIONS


@dataclass
class Item:
    """Item class representing parsed spreadsheet data"""
    
    # Spreadsheet-related properties
    spreadsheet_label: str = ""
    spreadsheet_edi_info_text: str = ""
    spreadsheet_edi_info_text_cleared: str = ""
    spreadsheet_usage: str = ""
    spreadsheet_min_max_text: str = ""
    spreadsheet_min: Optional[int] = None
    spreadsheet_max: Optional[int] = None
    spreadsheet_description: str = ""
    
    # EDI-related properties
    edi_segment: str = ""
    edi_element_number: str = ""
    edi_qualifier: str = ""
    
    # Item properties from DB
    item_properties_id: Optional[int] = None
    tli_value: str = ""
    rsx_tag_850: str = ""
    tli_tag_850: str = ""
    is_on_detail_level: bool = False
    is_partnumber: bool = False
    rsx_path_855: str = ""
    rsx_path_856: str = ""
    rsx_path_810: str = ""
    put_in_855: bool = False
    put_in_856: bool = False
    put_in_810: bool = False
    
    # Sourcing group properties from DB
    sourcing_group_properties_id: Optional[int] = None
    populate_method_name: str = ""
    map_name: str = ""
    call_method_path: str = ""
    call_method_java_code: str = ""
    
    # Order path properties from DB
    order_path_properties_id: Optional[int] = None
    java_code_wrapper: str = ""
    
    # Parsing errors
    parsing_errors: List[str] = field(default_factory=list)
    
    @staticmethod
    def clear_edi_info(line: str) -> str:
        """
        Clear EDI info from line
        
        Args:
            line: Input line with EDI info
            
        Returns:
            Cleared EDI info string
        """
        line = line.strip()
        
        # Якщо немає двокрапки — це просте значення
        if ":" not in line:
            return line
        
        # Знаходимо всі ключі та їх значення
        # Ключ = непробільні символи, потім :, пробіли
        # Значення = все до наступного ключа або кінця рядка
        pairs = re.findall(
            r'(\S+):\s*([^:]+?)(?=\s*\S+:|$)',
            line
        )
        
        for key, value in pairs:
            if "850" in key:
                return value.strip()
        
        # Якщо ключ 850 не знайдено — повертаємо рядок
        return line
    
    @staticmethod
    def normalize_segment(seg: str) -> str:
        """
        Нормалізація сегмента:
        - перетворює P01 → PO1 (специфічна вимога)
        - можна додати інші правила, якщо буде потрібно
        """
        return seg.replace("P01", "PO1")
    
    @staticmethod
    def parse_edi_info(text: str) -> Tuple[str, str, str]:
        """
        Parse EDI info text
        
        Args:
            text: EDI info text to parse
            
        Returns:
            Tuple of (edi_segment, edi_element_number, edi_qualifier)
        """
        text = text.strip()
        
        if not text:
            return "", "", ""
        
        # Формат: SEGNN (SEGMM = QUAL)
        m = re.match(r'^(\S+?)(\d+)\s*\(\s*(\S+?)(\d+)\s*=\s*([A-Za-z0-9]+)\s*\)$', text)
        if m:
            seg_part, digits, qseg, qel, qual = m.groups()
            # Якщо номер елемента має 3+ цифри, перша цифра належить сегменту
            if len(digits) >= 3:
                # Беремо першу цифру для сегменту, останні 2 для номера
                # Наприклад, N403 -> seg = N4, el = 03
                seg = seg_part + digits[0]
                el = digits[-2:]  # Останні 2 цифри
            elif len(digits) == 2:
                # Якщо 2 цифри, перевіряємо довжину сегменту
                # Якщо сегмент довший за 1 символ (наприклад PID, N1, N2), то сегмент повний і обидві цифри - номер елемента
                # Якщо сегмент 1 символ (наприклад N), то перша цифра йде до сегменту, друга до номера
                if len(seg_part) > 1:
                    # Сегмент повний, обидві цифри - номер елемента
                    # Наприклад, PID05 (PID02=08) -> seg = PID, el = 05
                    seg = seg_part
                    el = digits.zfill(2)
                else:
                    # Сегмент 1 символ, перша цифра йде до сегменту
                    # Наприклад, N45 (N402=08) -> seg = N4, el = 05
                    seg = seg_part + digits[0]
                    el = digits[1].zfill(2)
            else:
                # Якщо 1 цифра, вона йде до номера
                seg = seg_part
                el = digits.zfill(2)
            seg = Item.normalize_segment(seg)
            return seg, el, qual
        
        # Формат: SEGNN (QUAL)
        m = re.match(r'^(\S+?)(\d+)\s*\(\s*([A-Za-z0-9]+)\s*\)$', text)
        if m:
            seg_part, digits, qual = m.groups()
            # Якщо номер елемента має 3+ цифри, перша цифра належить сегменту
            if len(digits) >= 3:
                # Беремо першу цифру для сегменту, останні 2 для номера
                # Наприклад, N403 -> seg = N4, el = 03
                seg = seg_part + digits[0]
                el = digits[-2:]  # Останні 2 цифри
            elif len(digits) == 2:
                # Якщо 2 цифри, перевіряємо довжину сегменту
                # Якщо сегмент довший за 1 символ (наприклад PID, N1, N2), то сегмент повний і обидві цифри - номер елемента
                # Якщо сегмент 1 символ (наприклад N), то перша цифра йде до сегменту, друга до номера
                if len(seg_part) > 1:
                    # Сегмент повний, обидві цифри - номер елемента
                    # Наприклад, PID05 (08) -> seg = PID, el = 05
                    seg = seg_part
                    el = digits.zfill(2)
                else:
                    # Сегмент 1 символ, перша цифра йде до сегменту
                    # Наприклад, N45 (08) -> seg = N4, el = 05
                    seg = seg_part + digits[0]
                    el = digits[1].zfill(2)
            else:
                # Якщо 1 цифра, вона йде до номера
                seg = seg_part
                el = digits.zfill(2)
            seg = Item.normalize_segment(seg)
            return seg, el, qual
        
        # Формат: SEGNN (наприклад N404 -> N4, 04)
        # Спочатку намагаємося знайти сегмент з цифрою на кінці (наприклад N4, PO1)
        # Якщо номер елемента має більше 2 цифр, беремо останні 2
        # Важливо: цей паттерн має спрацьовувати тільки якщо номер елемента має >= 2 цифри,
        # щоб уникнути неправильного парсингу "PID05" як "PID0" + "5"
        m = re.match(r'^([A-Za-z]+\d)(\d{2,})$', text)
        if m:
            seg, el = m.groups()
            seg = Item.normalize_segment(seg)
            # Обмежуємо edi_element_number до 2 цифр (беремо останні 2)
            # Наприклад, N404 -> N4, 04 (останні 2 цифри з 404)
            el = el[-2:].zfill(2) if len(el) > 2 else el.zfill(2)
            return seg, el, ""
        
        # Формат: SEGNN (якщо сегмент без цифри на кінці, наприклад N404 де N - сегмент, 404 - номер)
        # Але якщо номер має 3+ цифри, можливо це N4 + 04
        m = re.match(r'^([A-Za-z]+)(\d+)$', text)
        if m:
            seg_part, digits = m.groups()
            # Якщо номер елемента має 3+ цифри, перша цифра належить сегменту
            if len(digits) >= 3:
                # Беремо першу цифру для сегменту, останні 2 для номера
                # Наприклад, N404 -> seg = N4, el = 04
                seg = seg_part + digits[0]
                el = digits[-2:]  # Останні 2 цифри
            elif len(digits) == 2:
                # Якщо 2 цифри, перевіряємо довжину сегменту
                # Якщо сегмент довший за 1 символ (наприклад PID, N1, N2), то сегмент повний і обидві цифри - номер елемента
                # Якщо сегмент 1 символ (наприклад N), то перша цифра йде до сегменту, друга до номера
                if len(seg_part) > 1:
                    # Сегмент повний, обидві цифри - номер елемента
                    # Наприклад, PID05 -> seg = PID, el = 05
                    seg = seg_part
                    el = digits.zfill(2)
                else:
                    # Сегмент 1 символ, перша цифра йде до сегменту
                    # Наприклад, N45 -> seg = N4, el = 05
                    seg = seg_part + digits[0]
                    el = digits[1].zfill(2)
            else:
                # Якщо 1 цифра, вона йде до номера, але сегмент залишається без змін
                # Наприклад, N4 -> seg = N, el = 04
                seg = seg_part
                el = digits.zfill(2)
            seg = Item.normalize_segment(seg)
            return seg, el, ""
        
        # Нічого не підійшло → повертаємо пусті поля
        return "", "", ""


class SpreadsheetParser:
    """Parser for Excel spreadsheet files"""
    
    def __init__(self, database, language: str = "UA"):
        """
        Initialize parser
        
        Args:
            database: Database instance for matching items
            language: Language code ("UA" or "EN") for error messages
        """
        self.database = database
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])
    
    def parse(self, file_path: Path) -> Tuple[List[Item], bool, Optional[str]]:
        """
        Parse spreadsheet file and create Item objects
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Tuple of (items_list, success, error_message)
        """
        items: List[Item] = []
        all_errors: List[str] = []
        
        try:
            # Load workbook
            workbook = load_workbook(file_path, data_only=True)
            sheet = workbook.active
            
            # Get max column (starting from column B = 2)
            max_col = sheet.max_column
            
            # Iterate through columns starting from B (index 2)
            for col_idx in range(2, max_col + 1):
                item = Item()
                column_errors = []
                
                # Get values from rows 1-5
                row1_value = self._get_cell_value(sheet, 1, col_idx)
                row2_value = self._get_cell_value(sheet, 2, col_idx)
                row3_value = self._get_cell_value(sheet, 3, col_idx)
                row4_value = self._get_cell_value(sheet, 4, col_idx)
                row5_value = self._get_cell_value(sheet, 5, col_idx)
                
                # Row 1: spreadsheet_label (required)
                if not row1_value or str(row1_value).strip() == "":
                    column_errors.append(
                        f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                        f"{self.t['error_empty_field'].format(field='spreadsheet_label')}"
                    )
                else:
                    item.spreadsheet_label = str(row1_value).strip()
                
                # Row 2: spreadsheet_edi_info_text (required)
                if not row2_value or str(row2_value).strip() == "":
                    column_errors.append(
                        f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                        f"{self.t['error_empty_field'].format(field='spreadsheet_edi_info_text')}"
                    )
                else:
                    item.spreadsheet_edi_info_text = str(row2_value).strip()
                
                # Row 3: spreadsheet_usage (required)
                if not row3_value or str(row3_value).strip() == "":
                    column_errors.append(
                        f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                        f"{self.t['error_empty_field'].format(field='spreadsheet_usage')}"
                    )
                else:
                    item.spreadsheet_usage = str(row3_value).strip()
                
                # Row 4: spreadsheet_min_max_text (optional)
                if row4_value and str(row4_value).strip():
                    item.spreadsheet_min_max_text = str(row4_value).strip()
                    # Parse min/max only if field is not empty
                    min_max_errors = self._parse_min_max(item, col_idx)
                    column_errors.extend(min_max_errors)
                else:
                    # If field is empty and spreadsheet_label ends with "UOM", set min=2, max=2
                    if item.spreadsheet_label and item.spreadsheet_label.strip().upper().endswith("UOM"):
                        item.spreadsheet_min = 2
                        item.spreadsheet_max = 2
                
                # Row 5: spreadsheet_description (optional)
                if row5_value:
                    item.spreadsheet_description = str(row5_value).strip()
                
                # If there are errors in required fields, skip further processing
                if column_errors:
                    item.parsing_errors = column_errors
                    all_errors.extend(column_errors)
                    items.append(item)
                    continue
                
                # Parse spreadsheet_edi_info_text_cleared
                try:
                    item.spreadsheet_edi_info_text_cleared = Item.clear_edi_info(item.spreadsheet_edi_info_text)
                except Exception as e:
                    error_msg = (
                        f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                        f"{self.t['error_parse_spreadsheet_edi_info']}: {str(e)}"
                    )
                    column_errors.append(error_msg)
                    all_errors.append(error_msg)
                    item.parsing_errors = column_errors
                    items.append(item)
                    continue
                
                # Parse EDI info
                try:
                    edi_segment, edi_element_number, edi_qualifier = Item.parse_edi_info(
                        item.spreadsheet_edi_info_text_cleared
                    )
                    item.edi_segment = edi_segment
                    item.edi_element_number = edi_element_number
                    item.edi_qualifier = edi_qualifier
                except Exception as e:
                    error_msg = (
                        f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                        f"{self.t['error_parse_edi_info']}: {str(e)}"
                    )
                    column_errors.append(error_msg)
                    all_errors.append(error_msg)
                    item.parsing_errors = column_errors
                    items.append(item)
                    continue
                
                # Match with database
                if item.edi_segment and item.edi_element_number:
                    match_errors = self._match_with_database(item, col_idx)
                    column_errors.extend(match_errors)
                    all_errors.extend(match_errors)
                
                item.parsing_errors = column_errors
                items.append(item)
            
            workbook.close()
            
            # Check if parsing was successful
            success = len(all_errors) == 0
            error_message = "\n".join(all_errors) if all_errors else None
            
            return items, success, error_message
            
        except Exception as e:
            return [], False, f"{self.t['error_read_file']}: {str(e)}"
    
    def _get_cell_value(self, sheet, row: int, col: int) -> Optional[str]:
        """Get cell value as string"""
        cell = sheet.cell(row=row, column=col)
        if cell.value is None:
            return None
        return str(cell.value)
    
    def _column_letter(self, col_idx: int) -> str:
        """Convert column index to letter (1=A, 2=B, etc.)"""
        return openpyxl.utils.get_column_letter(col_idx)
    
    def _parse_min_max(self, item: Item, col_idx: int) -> List[str]:
        """Parse min/max from spreadsheet_min_max_text (optional field)"""
        errors = []
        text = item.spreadsheet_min_max_text.strip()
        
        # Format: "min=1, max=50" or similar
        min_match = re.search(r'min\s*=\s*(\d+)', text, re.IGNORECASE)
        max_match = re.search(r'max\s*=\s*(\d+)', text, re.IGNORECASE)
        
        # Check if text contains min= or max= keywords (field is optional, so only validate if keywords are present)
        has_min_keyword = bool(re.search(r'min\s*=', text, re.IGNORECASE))
        has_max_keyword = bool(re.search(r'max\s*=', text, re.IGNORECASE))
        
        if min_match:
            try:
                item.spreadsheet_min = int(min_match.group(1))
            except ValueError:
                errors.append(
                    f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                    f"{self.t['error_invalid_min_format']} '{text}'"
                )
        elif has_min_keyword:
            # Only show error if min= keyword is present but value is invalid
            errors.append(
                f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                f"{self.t['error_min_not_found']} '{text}'"
            )
        
        if max_match:
            try:
                item.spreadsheet_max = int(max_match.group(1))
            except ValueError:
                errors.append(
                    f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                    f"{self.t['error_invalid_max_format']} '{text}'"
                )
        elif has_max_keyword:
            # Only show error if max= keyword is present but value is invalid
            errors.append(
                f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                f"{self.t['error_max_not_found']} '{text}'"
            )
        
        return errors
    
    def _match_with_database(self, item: Item, col_idx: int) -> List[str]:
        """Match item with database records"""
        errors = []
        
        # Get all items from database
        db_items = self.database.get_all_items()
        
        # Normalize edi_element_number for matching
        edi_element_num = item.edi_element_number
        
        # Special case: if edi_segment=PO1 and edi_element_number>06, treat as 07
        if item.edi_segment == "PO1" and edi_element_num:
            try:
                if int(edi_element_num) > 6:
                    edi_element_num = "07"
            except ValueError:
                # If edi_element_number is not a valid number, keep original value
                pass
        
        # Find matches
        matches = []
        for db_item in db_items:
            db_segment = db_item.get("edi_segment", "")
            db_element_raw = db_item.get("edi_element_number", "")
            db_qualifier = db_item.get("edi_qualifier") or ""
            item_qualifier = item.edi_qualifier or ""
            
            # Normalize element numbers for comparison (convert both to int)
            # Database stores as INTEGER (e.g., 2), parser returns as string with leading zeros (e.g., "02")
            try:
                db_element_int = int(db_element_raw) if db_element_raw != "" else None
                item_element_int = int(edi_element_num) if edi_element_num else None
                element_match = db_element_int == item_element_int if (db_element_int is not None and item_element_int is not None) else False
            except (ValueError, TypeError):
                # If conversion fails, fall back to string comparison
                db_element = str(db_element_raw)
                element_match = db_element == edi_element_num
            
            if db_segment == item.edi_segment and element_match:
                # Match qualifier if both are present, or if both are empty
                if (db_qualifier and item_qualifier and db_qualifier == item_qualifier) or \
                   (not db_qualifier and not item_qualifier):
                    matches.append(db_item)
        
        if len(matches) == 0:
            errors.append(
                f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                f"{self.t['error_no_match']} "
                f"edi_segment={item.edi_segment}, edi_element_number={item.edi_element_number}, "
                f"edi_qualifier={item.edi_qualifier or self.t['error_empty_qualifier']}"
            )
        elif len(matches) > 1:
            errors.append(
                f"{self.t['error_column']} {self._column_letter(col_idx)}: "
                f"{self.t['error_multiple_matches']} "
                f"edi_segment={item.edi_segment}, edi_element_number={item.edi_element_number}, "
                f"edi_qualifier={item.edi_qualifier or self.t['error_empty_qualifier']}"
            )
        else:
            # Single match - fill item properties
            match = matches[0]
            item.item_properties_id = match.get("item_properties_id")
            item.tli_value = match.get("TLI_value", "")
            item.rsx_tag_850 = match.get("850_RSX_tag", "")
            item.tli_tag_850 = match.get("850_TLI_tag", "")
            item.is_on_detail_level = bool(match.get("is_on_detail_level", False))
            item.is_partnumber = bool(match.get("is_partnumber", False))
            item.rsx_path_855 = match.get("855_RSX_path", "")
            item.rsx_path_856 = match.get("856_RSX_path", "")
            item.rsx_path_810 = match.get("810_RSX_path", "")
            item.put_in_855 = bool(match.get("put_in_855_by_default", False))
            item.put_in_856 = bool(match.get("put_in_856_by_default", False))
            item.put_in_810 = bool(match.get("put_in_810_by_default", False))
            
            # Get sourcing group info
            sourcing_group_id = match.get("sourcing_group_properties_id")
            if sourcing_group_id:
                item.sourcing_group_properties_id = sourcing_group_id
                sourcing_group = self.database.get_sourcing_group(sourcing_group_id)
                if sourcing_group:
                    item.populate_method_name = sourcing_group.get("populate_method_name", "")
                    item.map_name = sourcing_group.get("map_name", "")
                    item.call_method_path = sourcing_group.get("order_path", sourcing_group.get("call_method_path", ""))
                    item.call_method_java_code = sourcing_group.get("call_method_java_code", "")
                    
                    # Get order path info
                    order_path_id = sourcing_group.get("order_path_properties_id")
                    if order_path_id:
                        item.order_path_properties_id = order_path_id
                        order_path = self.database.get_order_path(order_path_id)
                        if order_path:
                            item.java_code_wrapper = order_path.get("java_code_wrapper", "")
        
        return errors

