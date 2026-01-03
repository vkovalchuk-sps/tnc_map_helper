# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from bs4 import BeautifulSoup
from application.parsers.tommm_parser import TOMMMParser

parser = TOMMMParser('UA')

# Test HTML file
html_path = Path('test files/test/2.html')
html_content = parser._extract_html_from_html(html_path)
html_soup = BeautifulSoup(html_content, 'html.parser')
html_table = html_soup.find('table', {'class': 'sps-table', 'data-testid': 'tnc-scenario-table'})

if html_table:
    rows = html_table.find('tbody', class_='sps-table__body')
    if rows:
        all_table_rows = rows.find_all('tr', {'data-testid': 'tnc-scenario-table-row__row'})
        
        # Check first row
        first_row = all_table_rows[0]
        print('First row direct children:')
        direct_cells = []
        for child in first_row.children:
            if hasattr(child, 'name'):
                print(f'  - {child.name}: {child.get("data-testid", "")} role={child.get("role", "")}')
                if child.name == 'td' and child.get('role') == 'cell':
                    direct_cells.append(child)
        
        print(f'\nDirect td cells with role="cell": {len(direct_cells)}')
        for i, cell in enumerate(direct_cells):
            print(f'  Cell {i}: data-testid="{cell.get("data-testid", "")}"')
            # Check if it has direct child text
            text = parser._extract_direct_text(cell)
            print(f'    Text: {text[:50]}')
