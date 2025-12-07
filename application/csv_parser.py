"""CSV archive parser module for parsing ZIP archives with CSV files and updating InboundDocScenario objects"""

import csv
import io
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from application.translations import TRANSLATIONS


class CSVArchiveParser:
    """Parser for CSV archive ZIP files"""
    
    def __init__(self, language: str = "UA"):
        """
        Initialize parser
        
        Args:
            language: Language code ("UA" or "EN") for error messages
        """
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])
    
    def parse(
        self, 
        archive_path: Path, 
        scenarios: List, 
        items: List
    ) -> Tuple[bool, Optional[str]]:
        """
        Parse CSV archive and update scenarios
        
        Args:
            archive_path: Path to ZIP archive file
            scenarios: List of InboundDocScenario objects to update
            items: List of Item objects from spreadsheet (for CSV test file generation)
            
        Returns:
            Tuple of (success, error_message)
        """
        if not archive_path.exists():
            return False, self.t.get("error_read_file", "Error reading file")
        
        errors: List[str] = []
        updated_scenarios = set()
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Get all CSV files from archive (both .csv and .txt extensions)
                csv_files = [f for f in zip_ref.namelist() 
                            if f.lower().endswith('.csv') or f.lower().endswith('.txt')]
                
                if not csv_files:
                    return False, self.t.get("csv_no_files", "No CSV files found in archive")
                
                # Process each CSV file
                for csv_filename in csv_files:
                    try:
                        # Read CSV content
                        csv_content = zip_ref.read(csv_filename).decode('utf-8', errors='ignore')
                        csv_reader = csv.reader(io.StringIO(csv_content))
                        csv_rows = list(csv_reader)
                        
                        # Find Header_OrderHeader row
                        header_row = None
                        for row in csv_rows:
                            if len(row) > 0 and row[0] == "Header_OrderHeader":
                                header_row = row
                                break
                        
                        if not header_row:
                            errors.append(
                                self.t.get("csv_no_header", "No Header_OrderHeader found in {file}").format(
                                    file=csv_filename
                                )
                            )
                            continue
                        
                        # Check if valid (has Header_OrderHeader)
                        if len(header_row) < 3 or not header_row[2]:
                            errors.append(
                                self.t.get("csv_invalid_version", 
                                    "CSV file {file} may contain information for version lower than RSX 7.7").format(
                                    file=csv_filename
                                )
                            )
                            continue
                        
                        # Get key from column 3 (index 2)
                        key = header_row[2].strip()
                        if not key:
                            errors.append(
                                self.t.get("csv_no_key", "No key found in {file}").format(file=csv_filename)
                            )
                            continue
                        
                        # Determine target scenario based on filename and key
                        target_scenario = self._find_target_scenario(
                            csv_filename, key, header_row, scenarios, errors
                        )
                        
                        if not target_scenario:
                            continue
                        
                        # Update scenario with CSV data
                        self._update_scenario_from_csv(
                            target_scenario, csv_rows, csv_content, items, errors,
                            csv_filename=Path(csv_filename).name
                        )
                        
                        updated_scenarios.add(id(target_scenario))
                        
                    except Exception as e:
                        errors.append(
                            self.t.get("csv_parse_error", "Error parsing {file}: {error}").format(
                                file=csv_filename, error=str(e)
                            )
                        )
                
                # Check if all scenarios were updated
                if len(updated_scenarios) != len(scenarios):
                    missing_count = len(scenarios) - len(updated_scenarios)
                    errors.append(
                        self.t.get("csv_not_all_updated", 
                            "Not all scenarios were updated. Missing: {count}").format(
                            count=missing_count
                        )
                    )
                
                if errors:
                    return False, "\n".join(errors)
                
                return True, None
                
        except zipfile.BadZipFile:
            return False, self.t.get("csv_invalid_archive", "Invalid ZIP archive")
        except Exception as e:
            return False, f"{self.t.get('error_read_file', 'Error reading file')}: {str(e)}"
    
    def _find_target_scenario(
        self,
        csv_filename: str,
        key: str,
        header_row: List[str],
        scenarios: List,
        errors: List[str]
    ) -> Optional:
        """Find target scenario based on filename and CSV data"""
        
        filename = Path(csv_filename).name
        
        # PO850 files
        if filename.startswith("PO850"):
            # Find scenarios with document_number=850 and matching key
            matching = [s for s in scenarios if s.document_number == 850 and s.key == key]
            
            if len(matching) == 1:
                return matching[0]
            
            if len(matching) == 2:
                # Check if both have is_changed_by_850_scenario=True
                changed_scenarios = [s for s in matching if s.is_changed_by_850_scenario]
                if len(changed_scenarios) == 2:
                    # Check column 5 (index 4) for version indicator
                    if len(header_row) > 4 and header_row[4]:
                        version = header_row[4].strip()
                        
                        if version == "00":
                            # Find scenario with is_changer_850=False
                            target = [s for s in matching if not s.is_changer_850]
                            if len(target) == 1:
                                return target[0]
                        
                        elif version in ["01", "05"]:
                            # Find scenario with is_changer_850=True
                            target = [s for s in matching if s.is_changer_850]
                            if len(target) == 1:
                                return target[0]
            
            errors.append(
                self.t.get("csv_scenario_not_found", 
                    "Could not find unique scenario for {file} with key {key}").format(
                    file=csv_filename, key=key
                )
            )
            return None
        
        # PC860 files
        elif filename.startswith("PC860"):
            # Find scenarios with document_number=860 and matching key
            matching = [s for s in scenarios if s.document_number == 860 and s.key == key]
            
            if len(matching) == 1:
                return matching[0]
            
            errors.append(
                self.t.get("csv_scenario_not_found", 
                    "Could not find unique scenario for {file} with key {key}").format(
                    file=csv_filename, key=key
                )
            )
            return None
        
        else:
            errors.append(
                self.t.get("csv_unknown_prefix", 
                    "Unknown file prefix in {file}. Expected PO850 or PC860").format(
                    file=csv_filename
                )
            )
            return None
    
    def _update_scenario_from_csv(
        self,
        scenario,
        csv_rows: List[List[str]],
        csv_content: str,
        items: List,
        errors: List[str],
        csv_filename: Optional[str] = None,
    ) -> None:
        """Update scenario with data from CSV file"""
        
        # Find Header_OrderHeader row
        header_row = None
        for row in csv_rows:
            if len(row) > 0 and row[0] == "Header_OrderHeader":
                header_row = row
                break
        
        if not header_row:
            return
        
        # Update tset_code from column 5 (index 4)
        if len(header_row) > 4:
            scenario.tset_code = header_row[4].strip()
        
        # Count TLI rows
        tli_count = sum(1 for row in csv_rows if len(row) > 0 and row[0] == "TLI")
        scenario.number_of_tli = tli_count
        
        # Count LineItem_OrderLine rows
        line_count = sum(1 for row in csv_rows if len(row) > 0 and row[0] == "LineItem_OrderLine")
        scenario.number_of_lines = line_count
        
        # Update csv_design with full CSV content
        scenario.csv_design = csv_content
        # Store CSV design filename if provided
        if csv_filename is not None:
            scenario.csv_design_filename = csv_filename
        
        # Generate csv_test_file (only if spreadsheet parsing was successful)
        if items:
            try:
                csv_test_content = self._generate_csv_test_file(csv_rows, items, errors)
                scenario.csv_test_file = csv_test_content
            except Exception as e:
                errors.append(
                    self.t.get("csv_test_generation_error", 
                        "Error generating test file: {error}").format(error=str(e))
                )
        else:
            # Leave csv_test_file empty if no items
            scenario.csv_test_file = ""
    
    def _generate_csv_test_file(
        self,
        csv_rows: List[List[str]],
        items: List,
        errors: List[str]
    ) -> str:
        """Generate CSV test file by replacing TLI rows with item values"""
        
        # Find all TLI rows
        tli_rows = []
        for i, row in enumerate(csv_rows):
            if len(row) > 0 and row[0] == "TLI":
                tli_rows.append((i, row))
        
        if not tli_rows:
            # No TLI rows, return original content as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            for row in csv_rows:
                writer.writerow(row)
            return output.getvalue()
        
        # Check if number of items matches number of empty values in each TLI row
        items_count = len(items)
        for tli_row_idx, (original_idx, row) in enumerate(tli_rows):
            # Count empty values in row (starting from index 1, excluding first column which is "TLI")
            empty_count = sum(1 for val in row[1:] if not val or not val.strip())
            
            if items_count != empty_count:
                raise ValueError(
                    self.t.get("csv_item_count_mismatch",
                        "Number of items ({items}) does not match number of empty TLI values ({empty})").format(
                        items=items_count, empty=empty_count
                    )
                )
        
        # Create a copy of CSV rows for modification
        result_rows = [row[:] for row in csv_rows]
        
        # Process each TLI row - each row should be filled with all items
        for tli_row_idx, (original_idx, tli_row) in enumerate(tli_rows):
            # Replace empty values in TLI row with item values
            new_row = list(tli_row)  # Make a copy
            item_index = 0  # Reset item index for each TLI row
            for col_idx in range(1, len(new_row)):
                # Check if value is empty (None, empty string, or whitespace)
                if (col_idx >= len(new_row) or not new_row[col_idx] or not new_row[col_idx].strip()):
                    if item_index < len(items):
                        item = items[item_index]
                        # Replace {sequential_number} placeholder with row number (1-based)
                        tli_value = item.tli_value.replace(
                            "{sequential_number}", 
                            str(tli_row_idx + 1)
                        )
                        # Ensure we have enough columns
                        while len(new_row) <= col_idx:
                            new_row.append("")
                        new_row[col_idx] = tli_value
                        item_index += 1
            
            result_rows[original_idx] = new_row
        
        # Convert back to CSV string
        output = io.StringIO()
        writer = csv.writer(output)
        for row in result_rows:
            writer.writerow(row)
        
        return output.getvalue()

