"""File handling module for processing various file types"""

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Tuple


class XTLParser:
    """Parser for .xtl files"""

    @staticmethod
    def parse(file_path: Path) -> Dict[str, str]:
        """
        Parse .xtl file and extract DOCUMENTDEF attributes

        Args:
            file_path: Path to .xtl file

        Returns:
            Dictionary with owner, javaPackageName, and lastModifiedBy
        """
        result = {
            "owner": "",
            "javaPackageName": "",
            "lastModifiedBy": "",
        }

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Find DOCUMENTDEF element
            document_def = root.find(".//DOCUMENTDEF")
            if document_def is not None:
                result["owner"] = document_def.get("owner", "")
                result["javaPackageName"] = document_def.get("javaPackageName", "")
                result["lastModifiedBy"] = document_def.get("lastModifiedBy", "")

        except Exception:
            pass  # Return empty values on error

        return result


class InputFileFinder:
    """Finds files in input directory"""

    @staticmethod
    def find_files(input_dir: Path) -> Tuple[Optional[Path], Optional[Path], Optional[Path], Optional[Path]]:
        """
        Find files in input directory

        Args:
            input_dir: Path to input directory

        Returns:
            Tuple of (spreadsheet_path, tnc_platform_path, csv_archive_path, xtl_path)
        """
        if not input_dir.exists():
            return None, None, None, None

        # Find Spreadsheet files (.xls, .xlsx)
        spreadsheet_files = list(input_dir.glob("*.xls")) + list(input_dir.glob("*.xlsx"))
        spreadsheet_path = spreadsheet_files[0] if len(spreadsheet_files) == 1 else None

        # Find T&C Platform files (.mhtml, .html, .htm)
        tnc_files = (
            list(input_dir.glob("*.mhtml"))
            + list(input_dir.glob("*.html"))
            + list(input_dir.glob("*.htm"))
        )
        tnc_platform_path = tnc_files[0] if len(tnc_files) == 1 else None

        # Find ZIP files (.zip)
        zip_files = list(input_dir.glob("*.zip"))
        csv_archive_path = zip_files[0] if len(zip_files) == 1 else None

        # Find .xtl files
        xtl_files = list(input_dir.glob("*.xtl"))
        xtl_path = xtl_files[0] if len(xtl_files) == 1 else None

        return spreadsheet_path, tnc_platform_path, csv_archive_path, xtl_path


class OutputFileWriter:
    """Handles writing output files"""

    @staticmethod
    def clear_output_directory(output_dir: Path) -> Optional[str]:
        """
        Clear all files from output directory

        Args:
            output_dir: Path to output directory

        Returns:
            Error message if any, None otherwise
        """
        try:
            for file_path in output_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
        except Exception as exc:
            return str(exc)
        return None

    @staticmethod
    def write_output_file(
        output_dir: Path, company_name: str, java_package: str, author: str
    ) -> Optional[str]:
        """
        Write output file with processed data

        Args:
            output_dir: Path to output directory
            company_name: Company name
            java_package: Java package name
            author: Author name

        Returns:
            Error message if any, None otherwise
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "output.txt"
        content = f"Company Name: {company_name}\n"
        content += f"Java Package Name: {java_package}\n"
        content += f"Author: {author}\n"

        try:
            output_file.write_text(content, encoding="utf-8")
        except Exception as exc:
            return str(exc)

        return None

