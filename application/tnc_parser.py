"""TOMMM parser module for parsing HTML/MHTML files and creating InboundDocScenario objects"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
from email import message_from_string

from application.translations import TRANSLATIONS


@dataclass
class InboundDocScenario:
    """InboundDocScenario class representing parsed TOMMM scenario data"""
    
    name: str = ""
    key: str = ""
    key_with_date: str = ""
    document_number: int = 0
    tset_code: str = ""
    number_of_tli: int = 0
    number_of_lines: int = 0
    includes_855_docs: bool = False
    includes_856_docs: bool = False
    includes_810_docs: bool = False
    is_changed_by_850_scenario: bool = False
    is_changer_850: bool = False
    is_consolidated: bool = False
    csv_design_filename: str = ""
    csv_design: str = ""
    csv_test_file: str = ""
    
    # Parsing errors
    parsing_errors: List[str] = field(default_factory=list)


class TOMMMParser:
    """Parser for TOMMM HTML/MHTML files"""
    
    def __init__(self, language: str = "UA"):
        """
        Initialize parser
        
        Args:
            language: Language code ("UA" or "EN") for error messages
        """
        self.language = language
        self.t = TRANSLATIONS.get(language, TRANSLATIONS["UA"])
    
    def _normalize_key(self, key: str) -> Tuple[str, str]:
        """
        Remove date prefixes from key if present
        
        Removes literal prefixes:
        - POYYMMDD (literal string "POYYMMDD")
        - YYMMDD (literal string "YYMMDD")
        - YY (literal string "YY")
        
        Args:
            key: Original key string
            
        Returns:
            Tuple of (normalized_key, key_with_date):
            - normalized_key: Key without date prefix
            - key_with_date: Original key if it had a date prefix, empty string otherwise
        """
        if not key:
            return key, ""
        
        # Pattern 1: POYYMMDD (literal string "POYYMMDD")
        if key.startswith("POYYMMDD"):
            return key[8:], key  # Return normalized key and original with prefix
        
        # Pattern 2: YYMMDD (literal string "YYMMDD")
        if key.startswith("YYMMDD"):
            return key[6:], key  # Return normalized key and original with prefix
        
        # Pattern 3: YY (literal string "YY")
        if key.startswith("YY"):
            return key[2:], key  # Return normalized key and original with prefix
        
        return key, ""  # No prefix found, return original key and empty string
    
    def parse(self, file_path: Path) -> Tuple[List[InboundDocScenario], Optional[str], Optional[str]]:
        """
        Parse TOMMM file and create InboundDocScenario objects
        
        Args:
            file_path: Path to HTML/MHTML file
            
        Returns:
            Tuple of (scenarios_list, company_name, error_message)
        """
        scenarios: List[InboundDocScenario] = []
        all_errors: List[str] = []
        company_name: Optional[str] = None
        
        try:
            # Read file content
            if file_path.suffix.lower() == ".mhtml":
                html_content = self._extract_html_from_mhtml(file_path)
            else:
                html_content = file_path.read_text(encoding="utf-8")
            
            if not html_content:
                return [], None, self.t.get("error_read_file", "Error reading file")
            
            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract company name from <h4> inside <section class="sps-main-content sps-column-layout">
            company_name = self._extract_company_name(soup)
            
            # Find the scenario table
            table = soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"})
            if not table:
                return scenarios, company_name, self.t.get("error_table_not_found", "Scenario table not found")
            
            # Extract all rows from table
            rows = table.find("tbody", class_="sps-table__body")
            if not rows:
                return scenarios, company_name, self.t.get("error_table_empty", "Scenario table is empty")
            
            table_rows = rows.find_all("tr", {"data-testid": "tnc-scenario-table-row__row"})
            
            # First pass: collect all row data
            row_data = []
            for row in table_rows:
                cells = row.find_all("td", {"role": "cell"})
                if len(cells) < 3:
                    continue
                
                name_cell = cells[0].get_text(strip=True)
                key_cell = cells[1].get_text(strip=True)
                documents_cell = cells[2]
                
                # Extract document numbers from documents cell
                doc_spans = documents_cell.find_all("span")
                documents = [span.get_text(strip=True).rstrip(",") for span in doc_spans if span.get_text(strip=True)]
                
                row_data.append({
                    "name": name_cell,
                    "key": key_cell,
                    "documents": documents
                })
            
            # Process rows and create scenarios, keeping track of row info
            row_to_scenario = {}  # Map row index to scenario for 850 documents
            for idx, row_info in enumerate(row_data):
                name = row_info["name"]
                original_key = row_info["key"]
                # Normalize key by removing date prefixes
                key, key_with_date = self._normalize_key(original_key)
                documents = row_info["documents"]
                
                # Check for 850 document
                if "850" in documents:
                    scenario = InboundDocScenario()
                    scenario.name = name
                    scenario.key = key
                    scenario.key_with_date = key_with_date
                    scenario.document_number = 850
                    
                    # Filter document numbers (only numeric ones like "850", "855", etc.)
                    doc_numbers = [d for d in documents if d.isdigit()]
                    
                    # Check for related documents (855, 856, 810) in current row or other rows with same key
                    # Use normalized keys for comparison
                    scenario.includes_855_docs = "855" in doc_numbers or any(
                        self._normalize_key(r["key"])[0] == key and "855" in [d for d in r["documents"] if d.isdigit()]
                        for r in row_data
                    )
                    scenario.includes_856_docs = "856" in doc_numbers or any(
                        self._normalize_key(r["key"])[0] == key and "856" in [d for d in r["documents"] if d.isdigit()]
                        for r in row_data
                    )
                    scenario.includes_810_docs = "810" in doc_numbers or any(
                        self._normalize_key(r["key"])[0] == key and "810" in [d for d in r["documents"] if d.isdigit()]
                        for r in row_data
                    )
                    
                    scenarios.append(scenario)
                    row_to_scenario[idx] = scenario
                
                # Check for 860 document
                if "860" in documents:
                    scenario = InboundDocScenario()
                    scenario.name = name
                    scenario.key = key
                    scenario.key_with_date = key_with_date
                    scenario.document_number = 860
                    scenario.includes_855_docs = False
                    scenario.includes_856_docs = False
                    scenario.includes_810_docs = False
                    
                    scenarios.append(scenario)
            
            # Check for is_changed_by_850_scenario (multiple rows with same key and 850)
            # Use normalized keys for grouping
            keys_with_850_rows = {}
            for idx, row_info in enumerate(row_data):
                if "850" in row_info["documents"]:
                    key, _ = self._normalize_key(row_info["key"])
                    if key not in keys_with_850_rows:
                        keys_with_850_rows[key] = []
                    keys_with_850_rows[key].append(idx)
            
            # Mark scenarios with is_changed_by_850_scenario
            for key, row_indices in keys_with_850_rows.items():
                if len(row_indices) > 1:
                    # Multiple rows with same key and 850 document
                    for row_idx in row_indices:
                        if row_idx in row_to_scenario:
                            row_to_scenario[row_idx].is_changed_by_850_scenario = True
            
            # Process is_changed_by_850_scenario: check if one has only 850
            for key, row_indices in keys_with_850_rows.items():
                if len(row_indices) == 2:
                    # Two rows with same key and 850 - check if one has only 850
                    changed_scenarios = [row_to_scenario[idx] for idx in row_indices if idx in row_to_scenario]
                    if len(changed_scenarios) == 2:
                        # Check each row - if one has only 850 document
                        for row_idx in row_indices:
                            row_info = row_data[row_idx]
                            doc_numbers = [d for d in row_info["documents"] if d.isdigit()]
                            if len(doc_numbers) == 1 and doc_numbers[0] == "850":
                                # This row has only 850 - find corresponding scenario
                                scenario = row_to_scenario.get(row_idx)
                                if scenario:
                                    scenario.includes_855_docs = False
                                    scenario.includes_856_docs = False
                                    scenario.includes_810_docs = False
                                    # Mark the other scenario as is_changer_850
                                    other_scenario = [s for s in changed_scenarios if s != scenario]
                                    if other_scenario:
                                        other_scenario[0].is_changer_850 = True
                                break
            
            # Check for is_consolidated (856 with key format "key_1 and key_2")
            for row_info in row_data:
                if "856" in row_info["documents"]:
                    key, _ = self._normalize_key(row_info["key"])
                    # Check if key contains " and " (format: "key_1 and key_2")
                    if " and " in key:
                        parts = key.split(" and ")
                        if len(parts) == 2:
                            key1 = parts[0].strip()
                            key2 = parts[1].strip()
                            # Mark scenarios with these keys as consolidated
                            for scenario in scenarios:
                                if scenario.key == key1 or scenario.key == key2:
                                    scenario.is_consolidated = True
            
            # Check for success
            if len(scenarios) == 0:
                error_msg = self.t.get("error_no_scenarios", "No scenarios found in table")
                return scenarios, company_name, error_msg
            
            return scenarios, company_name, None
            
        except Exception as e:
            error_msg = f"{self.t.get('error_read_file', 'Error reading file')}: {str(e)}"
            return [], None, error_msg
    
    def _extract_html_from_mhtml(self, file_path: Path) -> Optional[str]:
        """Extract HTML content from MHTML file, handling iframe content via CID"""
        try:
            content = file_path.read_text(encoding="utf-8")
            # Parse MHTML format
            msg = message_from_string(content)
            
            # First, try to get the main HTML document
            main_html = None
            html_parts = {}  # Store all HTML parts by their Content-ID
            all_html_parts = []  # Store all HTML parts in order
            
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    all_html_parts.append(html_content)
                    
                    # Get Content-ID if present (can be in Content-ID or Content-Location header)
                    content_id = part.get("Content-ID", "") or part.get("Content-Location", "")
                    if content_id:
                        # Remove angle brackets and protocol prefix if present
                        content_id = content_id.strip("<>").replace("cid:", "")
                        html_parts[content_id] = html_content
                    
                    # The first HTML part is usually the main document
                    if main_html is None:
                        main_html = html_content
            
            # If we have a main HTML, check for iframe with CID reference
            if main_html:
                soup = BeautifulSoup(main_html, "html.parser")
                
                # Look for iframe with CID reference
                iframe = soup.find("iframe", {"data-testid": "app-frame"})
                if iframe:
                    src = iframe.get("src", "")
                    # Extract CID from src (format: "cid:frame-...@mhtml.blink")
                    # Match cid: followed by content until quote, space, or end
                    cid_match = re.search(r'cid:([^"\s]+)', src)
                    if cid_match:
                        cid = cid_match.group(1)
                        # Try to find the corresponding HTML part
                        # First try exact match
                        if cid in html_parts:
                            return html_parts[cid]
                        
                        # Try with @mhtml.blink suffix
                        cid_with_suffix = f"{cid}@mhtml.blink"
                        if cid_with_suffix in html_parts:
                            return html_parts[cid_with_suffix]
                        
                        # Try partial match (CID base without suffix)
                        cid_base = cid.split("@")[0] if "@" in cid else cid
                        for stored_cid, html_part in html_parts.items():
                            stored_base = stored_cid.split("@")[0] if "@" in stored_cid else stored_cid
                            if stored_base == cid_base or cid_base in stored_cid or stored_cid in cid:
                                return html_part
                        
                        # Last resort: try to find any HTML part that contains the table
                        for html_part in all_html_parts:
                            part_soup = BeautifulSoup(html_part, "html.parser")
                            if part_soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"}):
                                return html_part
                
                # If no iframe found or iframe content not available, try to find table in main HTML
                table = soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"})
                if table:
                    return main_html
                
                # If table not in main HTML, search all HTML parts
                for html_part in all_html_parts:
                    part_soup = BeautifulSoup(html_part, "html.parser")
                    table = part_soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"})
                    if table:
                        return html_part
            
            # Fallback: search all HTML parts for table
            for html_part in all_html_parts:
                part_soup = BeautifulSoup(html_part, "html.parser")
                table = part_soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"})
                if table:
                    return html_part
            
            # Last fallback: return first HTML part found
            if main_html:
                return main_html
            
            # If no HTML part found via email parser, try manual extraction
            if "text/html" in content:
                # Try to extract between boundaries
                parts = re.split(r'------=_NextPart_[^\n]+', content)
                for part in parts:
                    if "text/html" in part or "<html" in part.lower():
                        # Extract HTML portion
                        html_match = re.search(r'<html[^>]*>.*</html>', part, re.DOTALL | re.IGNORECASE)
                        if html_match:
                            return html_match.group(0)
            
            return content  # Return full content as fallback
            
        except Exception as e:
            return None
    
    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from <h4> inside <section class="sps-main-content sps-column-layout">"""
        try:
            section = soup.find("section", class_="sps-main-content sps-column-layout")
            if section:
                h4 = section.find("h4")
                if h4:
                    return h4.get_text(strip=True)
        except Exception:
            pass
        return None

