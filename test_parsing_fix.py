# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from application.parsers.tommm_parser import TOMMMParser

parser = TOMMMParser('UA')

# Test HTML file
html_path = Path('test files/test/2.html')
html_scenarios, html_company, html_error = parser.parse(html_path)
print('HTML file:')
print(f'  Error: {html_error}')
print(f'  Company: {html_company}')
print(f'  Scenarios found: {len(html_scenarios) if html_scenarios else 0}')

if html_scenarios:
    html_850 = [s for s in html_scenarios if s.document_number == 850]
    print(f'  850 scenarios: {len(html_850)}')
    print('  All scenarios:')
    for s in html_scenarios:
        print(f'    - {s.name[:60]} ({s.key}) - doc: {s.document_number}')

print()

# Test MHTML file
mhtml_path = Path('test files/test/1.mhtml')
mhtml_scenarios, mhtml_company, mhtml_error = parser.parse(mhtml_path)
print('MHTML file:')
print(f'  Error: {mhtml_error}')
print(f'  Company: {mhtml_company}')
print(f'  Scenarios found: {len(mhtml_scenarios) if mhtml_scenarios else 0}')

if mhtml_scenarios:
    mhtml_850 = [s for s in mhtml_scenarios if s.document_number == 850]
    print(f'  850 scenarios: {len(mhtml_850)}')

print()
print('Comparison:')
print(f'  Same company: {html_company == mhtml_company}')
print(f'  Same number of scenarios: {len(html_scenarios) == len(mhtml_scenarios) if html_scenarios and mhtml_scenarios else False}')
if html_scenarios and mhtml_scenarios:
    html_850 = [s for s in html_scenarios if s.document_number == 850]
    mhtml_850 = [s for s in mhtml_scenarios if s.document_number == 850]
    print(f'  Same number of 850 scenarios: {len(html_850) == len(mhtml_850)}')
