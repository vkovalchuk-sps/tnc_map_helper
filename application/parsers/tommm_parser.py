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
            elif file_path.suffix.lower() in [".html", ".htm"]:
                html_content = self._extract_html_from_html(file_path)
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
            
            # Get all tr elements
            # For malformed HTML where rows are nested, we need to process all rows
            # but extract data only from each row's direct children
            all_table_rows = rows.find_all("tr", {"data-testid": "tnc-scenario-table-row__row"})
            
            # For properly structured HTML (like MHTML), all rows are direct children
            # For malformed HTML (like some saved HTML files), rows may be nested
            # We'll process all rows, but when extracting data, we'll only use direct children
            table_rows = all_table_rows
            
            # First pass: collect all row data
            row_data = []
            for row in table_rows:
                # Try to find cells by data-testid first (more reliable for malformed HTML)
                name_cell_elem = row.find("td", {"data-testid": "tnc-scenario-name__cell"})
                key_cell_elem = row.find("td", {"data-testid": "tnc-scenario-key__cell"})
                documents_cell_elem = row.find("td", {"data-testid": "tnc-scenario-document-name__cell"})
                
                # Fallback to role="cell" if data-testid not found
                if not name_cell_elem or not key_cell_elem or not documents_cell_elem:
                    cells = row.find_all("td", {"role": "cell"})
                    if len(cells) < 3:
                        continue
                    if not name_cell_elem:
                        name_cell_elem = cells[0]
                    if not key_cell_elem:
                        key_cell_elem = cells[1]
                    if not documents_cell_elem:
                        documents_cell_elem = cells[2]
                
                # Extract text from cells, avoiding nested td text
                # Get only direct text content, not from nested elements
                name_cell = self._extract_direct_text(name_cell_elem)
                key_cell = self._extract_direct_text(key_cell_elem)
                documents_cell = documents_cell_elem
                
                # Extract document numbers from documents cell
                # Only get direct child spans to avoid nested td content (for malformed HTML)
                doc_spans = []
                for child in documents_cell.children:
                    if hasattr(child, 'name') and child.name == 'span':
                        # Direct child span
                        doc_spans.append(child)
                    elif hasattr(child, 'name') and child.name != 'td':
                        # Non-td child - get spans from it, but exclude nested td content
                        for span in child.find_all("span", recursive=True):
                            # Check if span is inside a nested td
                            parent = getattr(span, 'parent', None)
                            if parent:
                                current = parent
                                is_nested_td = False
                                while current and current != documents_cell:
                                    if hasattr(current, 'name') and current.name == 'td' and current != documents_cell:
                                        is_nested_td = True
                                        break
                                    current = getattr(current, 'parent', None)
                                if not is_nested_td:
                                    doc_spans.append(span)
                
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
            
            # Check for is_consolidated (856 with combined keys, e.g. "key_1 and key_2" or "key_1, key_2")
            for row_info in row_data:
                if "856" in row_info["documents"]:
                    key, _ = self._normalize_key(row_info["key"])
                    # Consolidated keys can be separated either by " and " or by ","
                    # Example formats:
                    #   "KEY1 and KEY2"
                    #   "KEY1, KEY2"
                    # Use regex split to handle both separators
                    if " and " in key or "," in key:
                        parts = [p.strip() for p in re.split(r"\s+and\s+|,", key) if p.strip()]
                        if len(parts) == 2:
                            key1, key2 = parts
                            # Mark related 850 scenarios as consolidated and as including 856
                            for scenario in scenarios:
                                if scenario.document_number == 850 and (scenario.key == key1 or scenario.key == key2):
                                    scenario.is_consolidated = True
                                    scenario.includes_856_docs = True
            
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
    
    def _extract_html_from_html(self, file_path: Path) -> Optional[str]:
        """Extract HTML content from HTML file, handling iframe content similar to MHTML"""
        try:
            content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, "html.parser")
            
            # First, check if table is directly in the HTML
            table = soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"})
            if table:
                return content
            
            # Look for iframe with data-testid="app-frame"
            iframe = soup.find("iframe", {"data-testid": "app-frame"})
            if iframe:
                # First, try to find table in srcdoc if present (this is common in saved HTML files)
                # Similar to how MHTML extracts HTML from parts - srcdoc contains the actual content
                srcdoc = iframe.get("srcdoc", "")
                if srcdoc:
                    # Parse srcdoc to check for table (similar to checking html_parts in MHTML)
                    srcdoc_soup = BeautifulSoup(srcdoc, "html.parser")
                    srcdoc_table = srcdoc_soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"})
                    if srcdoc_table:
                        # Return srcdoc as-is (it should be a complete HTML document)
                        # This is analogous to returning html_part from MHTML's all_html_parts
                        return srcdoc
                
                # Then try src attribute
                src = iframe.get("src", "")
                if src:
                    # Handle different iframe src formats
                    # Format 1: "l@test files/test/2.html" (relative path)
                    # Format 2: "cid:frame-...@mhtml.blink" (CID reference, similar to MHTML)
                    # Format 3: Full URL or file path
                    
                    # Try to resolve relative path if it's a file reference
                    if not src.startswith(("http://", "https://", "cid:", "data:")):
                        # It's likely a relative file path
                        # Try multiple path resolution strategies
                        possible_paths = [
                            file_path.parent / src,  # Direct relative path
                            file_path.parent / Path(src).name,  # Just filename in same directory
                        ]
                        
                        # Also try to find file by name in subdirectories
                        src_name = Path(src).name
                        if src_name and src_name != src:
                            # Search in subdirectories
                            for subdir in file_path.parent.rglob("*"):
                                if subdir.is_dir():
                                    possible_file = subdir / src_name
                                    if possible_file.exists() and possible_file.is_file():
                                        possible_paths.append(possible_file)
                        
                        # Try each possible path
                        for iframe_file in possible_paths:
                            if iframe_file.exists() and iframe_file.is_file():
                                try:
                                    # Read the iframe content
                                    iframe_content = iframe_file.read_text(encoding="utf-8")
                                    iframe_soup = BeautifulSoup(iframe_content, "html.parser")
                                    # Check if table is in iframe content
                                    iframe_table = iframe_soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"})
                                    if iframe_table:
                                        return iframe_content
                                except Exception:
                                    # If reading fails, try next path
                                    continue
                    
                    # Handle CID references (similar to MHTML)
                    if src.startswith("cid:"):
                        # For HTML files with CID, we might need to search in the same file
                        # or in related files. For now, try to find table in current content
                        # by searching for embedded HTML
                        pass
            
            # If no iframe or table not found, try to search for embedded HTML content
            # Some HTML files might have embedded content in script tags or comments
            scripts = soup.find_all("script")
            for script in scripts:
                script_content = script.string
                if script_content and "tnc-scenario-table" in script_content:
                    # Try to extract HTML from script
                    html_match = re.search(r'<html[^>]*>.*?</html>', script_content, re.DOTALL | re.IGNORECASE)
                    if html_match:
                        extracted_html = html_match.group(0)
                        extracted_soup = BeautifulSoup(extracted_html, "html.parser")
                        if extracted_soup.find("table", {"class": "sps-table", "data-testid": "tnc-scenario-table"}):
                            return extracted_html
            
            # Fallback: return original content
            return content
            
        except Exception as e:
            # If extraction fails, try to return original content
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception:
                return None
    
    def _extract_direct_text(self, element) -> str:
        """
        Extract direct text from element, avoiding text from nested td elements
        
        This is needed for malformed HTML where td elements are nested instead of being siblings.
        We only want text that is directly in the element or in non-td children.
        
        Args:
            element: BeautifulSoup element to extract text from
            
        Returns:
            Extracted text string
        """
        if not element:
            return ""
        
        text_parts = []
        
        # Iterate through direct children only
        for child in element.children:
            if isinstance(child, str):
                # Direct text node - add it
                text_parts.append(child.strip())
            elif hasattr(child, 'name'):
                # Element node - only process if it's not a nested td
                if child.name != 'td':
                    # Get text from this element, but exclude any nested td elements
                    for text_node in child.stripped_strings:
                        # Check if this text node is inside a nested td
                        parent = getattr(text_node, 'parent', None)
                        if parent:
                            # Walk up the tree to see if we're inside a nested td
                            current = parent
                            is_nested_td = False
                            while current and current != element:
                                if hasattr(current, 'name') and current.name == 'td' and current != element:
                                    is_nested_td = True
                                    break
                                current = getattr(current, 'parent', None)
                            
                            if not is_nested_td:
                                text_parts.append(text_node.strip())
        
        result = ' '.join(text_parts).strip()
        
        # Fallback: if we got nothing or suspiciously long text, try simpler approach
        if not result or len(result) > 300:
            # Try getting text but stopping at first nested td
            all_text = element.get_text(separator=' ', strip=True)
            # If text seems too long, it might include nested content
            # For now, return as-is and let the caller handle it
            # (The data-testid selector should help ensure we get the right cell)
            if not result:
                result = all_text
        
        return result
    
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

