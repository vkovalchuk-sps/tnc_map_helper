import sys
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QGroupBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TNC Map Helper")
        self.setMinimumWidth(600)

        # Шляхи до файлів
        self.spreadsheet_path: Optional[Path] = None
        self.tnc_platform_path: Optional[Path] = None
        self.xtl_path: Optional[Path] = None

        # Шлях до папки з налаштуваннями
        self.config_dir = Path(__file__).parent / ".config"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"

        # Поточна мова (за замовчуванням UA)
        self.current_language = "EN"

        # Словники перекладів
        self.translations = {
            "UA": {
                "window_title": "TNC Map Helper",
                "spreadsheet": "Spreadsheet *",
                "tnc_platform": "Збережена сторінка TOMMM",
                "xtl": "poRsxRead.xtl",
                "not_selected": "Не обрано",
                "select_file": "Обрати файл",
                "company_name": "Назва компанії:",
                "java_package": "Java Package Name:",
                "author": "Автор:",
                "process_data": "Обробити дані",
                "select_spreadsheet": "Оберіть Spreadsheet файл",
                "select_tnc": "Оберіть файл збереженої сторінки TOMMM",
                "select_xtl": "Оберіть poRsxRead.xtl файл",
                "error": "Помилка",
                "warning": "Попередження",
                "success": "Готово",
                "select_spreadsheet_file": "Оберіть Spreadsheet файл",
                "fill_all_fields": "Заповніть всі обов'язкові поля",
                "read_xtl_error": "Не вдалося прочитати .xtl файл",
                "delete_files_warning": "Не вдалося видалити деякі попередні файли в папці output",
                "data_saved": "Дані збережено у файл",
                "save_error": "Не вдалося зберегти файл",
            },
            "EN": {
                "window_title": "TNC Map Helper",
                "spreadsheet": "Spreadsheet *",
                "tnc_platform": "TOMMM saved page",
                "xtl": "poRsxRead.xtl",
                "not_selected": "Not selected",
                "select_file": "Select file",
                "company_name": "Company Name:",
                "java_package": "Java Package Name:",
                "author": "Author:",
                "process_data": "Process Data",
                "select_spreadsheet": "Select Spreadsheet file",
                "select_tnc": "Select TOMMM saved page file",
                "select_xtl": "Select poRsxRead.xtl file",
                "error": "Error",
                "warning": "Warning",
                "success": "Done",
                "select_spreadsheet_file": "Select Spreadsheet file",
                "fill_all_fields": "Fill all required fields",
                "read_xtl_error": "Failed to read .xtl file",
                "delete_files_warning": "Failed to delete some previous files in output folder",
                "data_saved": "Data saved to file",
                "save_error": "Failed to save file",
            },
        }

        # Посилання на UI елементи для перекладу
        self.ui_elements = {}

        # Створення UI
        self.create_ui()

        # Завантаження останньої мови
        self.load_language()
        # Оновлюємо тексти (якщо мова не була завантажена, використовується мова за замовчуванням)
        self.update_ui_texts()

        # Завантаження останнього значення Author
        self.load_last_author()

        # Автозаповнення з папки input
        self.auto_fill_from_input()

        # Оновлення стану кнопки Process Data
        self.update_process_button_state()

    def create_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Вибір мови зверху
        language_layout = QHBoxLayout()
        language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["UA", "EN"])
        self.language_combo.currentTextChanged.connect(self.change_language)  # type: ignore[arg-type]
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        layout.addLayout(language_layout)

        # Поле Spreadsheet (обов'язкове)
        spreadsheet_group = QGroupBox("Spreadsheet *")
        self.ui_elements["spreadsheet_group"] = spreadsheet_group
        spreadsheet_layout = QHBoxLayout()
        self.spreadsheet_label = QLabel("Не обрано")
        # Встановлюємо жирний шрифт для назви обраного файлу
        font = QFont()
        font.setBold(True)
        self.spreadsheet_label.setFont(font)
        self.spreadsheet_button = QPushButton("Обрати файл")
        self.ui_elements["spreadsheet_button"] = self.spreadsheet_button
        self.spreadsheet_button.clicked.connect(self.select_spreadsheet)  # type: ignore[arg-type]
        spreadsheet_layout.addWidget(self.spreadsheet_label)
        spreadsheet_layout.addWidget(self.spreadsheet_button)
        spreadsheet_group.setLayout(spreadsheet_layout)
        layout.addWidget(spreadsheet_group)

        # Поле T&C Platform page (опційне)
        tnc_group = QGroupBox("TnC Platform page")
        self.ui_elements["tnc_group"] = tnc_group
        tnc_layout = QHBoxLayout()
        self.tnc_label = QLabel("Не обрано")
        # Встановлюємо жирний шрифт для назви обраного файлу
        self.tnc_label.setFont(font)
        self.tnc_button = QPushButton("Обрати файл")
        self.ui_elements["tnc_button"] = self.tnc_button
        self.tnc_button.clicked.connect(self.select_tnc_platform)  # type: ignore[arg-type]
        tnc_layout.addWidget(self.tnc_label)
        tnc_layout.addWidget(self.tnc_button)
        tnc_group.setLayout(tnc_layout)
        layout.addWidget(tnc_group)

        # Об'єднаний блок: poRsxRead.xtl та обов'язкові поля
        combined_group = QGroupBox("poRsxRead.xtl")
        self.ui_elements["xtl_group"] = combined_group
        combined_layout = QVBoxLayout()

        # Поле poRsxRead.xtl (опційне)
        xtl_layout = QHBoxLayout()
        self.xtl_label = QLabel("Не обрано")
        # Встановлюємо жирний шрифт для назви обраного файлу
        self.xtl_label.setFont(font)
        self.xtl_button = QPushButton("Обрати файл")
        self.ui_elements["xtl_button"] = self.xtl_button
        self.xtl_button.clicked.connect(self.select_xtl)  # type: ignore[arg-type]
        xtl_layout.addWidget(self.xtl_label)
        xtl_layout.addWidget(self.xtl_button)
        combined_layout.addLayout(xtl_layout)

        # Три обов'язкові поля з однаковою шириною
        # Company Name
        company_layout = QHBoxLayout()
        company_label = QLabel("Company Name:")
        self.ui_elements["company_label"] = company_label
        company_label.setMinimumWidth(150)
        self.company_name_field = QLineEdit()
        self.company_name_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        company_layout.addWidget(company_label)
        company_layout.addWidget(self.company_name_field)
        combined_layout.addLayout(company_layout)

        # Java Package Name
        package_layout = QHBoxLayout()
        package_label = QLabel("Java Package Name:")
        self.ui_elements["package_label"] = package_label
        package_label.setMinimumWidth(150)
        self.java_package_field = QLineEdit()
        self.java_package_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        package_layout.addWidget(package_label)
        package_layout.addWidget(self.java_package_field)
        combined_layout.addLayout(package_layout)

        # Author
        author_layout = QHBoxLayout()
        author_label = QLabel("Author:")
        self.ui_elements["author_label"] = author_label
        author_label.setMinimumWidth(150)
        self.author_field = QLineEdit()
        self.author_field.textChanged.connect(self.update_process_button_state)  # type: ignore[arg-type]
        self.author_field.textChanged.connect(self.save_last_author)  # type: ignore[arg-type]
        author_layout.addWidget(author_label)
        author_layout.addWidget(self.author_field)
        combined_layout.addLayout(author_layout)

        # Встановлюємо однакову мінімальну ширину для всіх текстових полів
        min_field_width = 300
        self.company_name_field.setMinimumWidth(min_field_width)
        self.java_package_field.setMinimumWidth(min_field_width)
        self.author_field.setMinimumWidth(min_field_width)

        combined_group.setLayout(combined_layout)
        layout.addWidget(combined_group)

        # Кнопка Process Data
        self.process_button = QPushButton("Process Data")
        self.ui_elements["process_button"] = self.process_button
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_data)  # type: ignore[arg-type]
        layout.addWidget(self.process_button)

        layout.addStretch()
        self.setCentralWidget(container)

        # Стилізація: жирний шрифт для заголовків QGroupBox (поля вибору файлів)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
            }
        """)

    def select_spreadsheet(self) -> None:
        t = self.translations[self.current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t["select_spreadsheet"],
            "",
            "Excel Files (*.xls *.xlsx)",
        )
        if file_path:
            self.spreadsheet_path = Path(file_path)
            self.spreadsheet_label.setText(self.spreadsheet_path.name)
            self.update_process_button_state()

    def select_tnc_platform(self) -> None:
        t = self.translations[self.current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t["select_tnc"],
            "",
            "Web Files (*.mhtml *.html *.htm)",
        )
        if file_path:
            self.tnc_platform_path = Path(file_path)
            self.tnc_label.setText(self.tnc_platform_path.name)
        else:
            self.tnc_platform_path = None
            self.tnc_label.setText(t["not_selected"])

    def select_xtl(self) -> None:
        t = self.translations[self.current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t["select_xtl"],
            "",
            "XTL Files (*.xtl)",
        )
        if file_path:
            self.xtl_path = Path(file_path)
            self.xtl_label.setText(self.xtl_path.name)
            self.parse_xtl_file(self.xtl_path)
        else:
            self.xtl_path = None
            self.xtl_label.setText(t["not_selected"])

    def parse_xtl_file(self, file_path: Path) -> None:
        """Парсить .xtl файл та заповнює поля з атрибутів DOCUMENTDEF"""
        t = self.translations[self.current_language]
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Знаходимо елемент DOCUMENTDEF
            document_def = root.find(".//DOCUMENTDEF")
            if document_def is not None:
                # Заповнюємо поля з атрибутів
                owner = document_def.get("owner", "")
                java_package = document_def.get("javaPackageName", "")
                last_modified_by = document_def.get("lastModifiedBy", "")

                if owner:
                    self.company_name_field.setText(owner)
                if java_package:
                    self.java_package_field.setText(java_package)
                if last_modified_by:
                    self.author_field.setText(last_modified_by)
        except Exception as exc:
            QMessageBox.warning(
                self,
                t["error"],
                f"{t['read_xtl_error']}:\n{exc}",
            )

    def auto_fill_from_input(self) -> None:
        """Автоматично заповнює поля з папки input, якщо там є один відповідний файл"""
        input_dir = Path(__file__).parent / "input"
        if not input_dir.exists():
            return

        # Пошук Spreadsheet файлів (.xls, .xlsx)
        spreadsheet_files = list(input_dir.glob("*.xls")) + list(input_dir.glob("*.xlsx"))
        if len(spreadsheet_files) == 1:
            self.spreadsheet_path = spreadsheet_files[0]
            self.spreadsheet_label.setText(self.spreadsheet_path.name)

        # Пошук T&C Platform файлів (.mhtml, .html, .htm)
        tnc_files = list(input_dir.glob("*.mhtml")) + list(input_dir.glob("*.html")) + list(input_dir.glob("*.htm"))
        if len(tnc_files) == 1:
            self.tnc_platform_path = tnc_files[0]
            self.tnc_label.setText(self.tnc_platform_path.name)

        # Пошук .xtl файлів
        xtl_files = list(input_dir.glob("*.xtl"))
        if len(xtl_files) == 1:
            self.xtl_path = xtl_files[0]
            self.xtl_label.setText(self.xtl_path.name)
            self.parse_xtl_file(self.xtl_path)

        # Оновлюємо текст "Не обрано" для необраних полів
        t = self.translations[self.current_language]
        if self.spreadsheet_path is None:
            self.spreadsheet_label.setText(t["not_selected"])
        if self.tnc_platform_path is None:
            self.tnc_label.setText(t["not_selected"])
        if self.xtl_path is None:
            self.xtl_label.setText(t["not_selected"])

        self.update_process_button_state()

    def update_process_button_state(self) -> None:
        """Оновлює стан кнопки Process Data"""
        # Перевірка обов'язкових полів
        has_spreadsheet = self.spreadsheet_path is not None
        has_company_name = bool(self.company_name_field.text().strip())
        has_java_package = bool(self.java_package_field.text().strip())
        has_author = bool(self.author_field.text().strip())

        self.process_button.setEnabled(
            has_spreadsheet and has_company_name and has_java_package and has_author
        )

    def load_last_author(self) -> None:
        """Завантажує останнє значення Author з конфігурації"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    author = config.get("last_author", "")
                    if author:
                        self.author_field.setText(author)
            except Exception:
                pass  # Якщо не вдалося завантажити, залишаємо поле порожнім

    def save_last_author(self) -> None:
        """Зберігає останнє значення Author у конфігурацію"""
        author = self.author_field.text().strip()
        if author:
            try:
                config = {}
                if self.config_file.exists():
                    try:
                        with open(self.config_file, "r", encoding="utf-8") as f:
                            config = json.load(f)
                    except Exception:
                        pass

                config["last_author"] = author
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            except Exception:
                pass  # Якщо не вдалося зберегти, продовжуємо роботу

    def process_data(self) -> None:
        """Обробляє дані та зберігає результат у папку output"""
        t = self.translations[self.current_language]
        # Перевірка обов'язкових полів
        if not self.spreadsheet_path:
            QMessageBox.warning(self, t["error"], t["select_spreadsheet_file"])
            return

        company_name = self.company_name_field.text().strip()
        java_package = self.java_package_field.text().strip()
        author = self.author_field.text().strip()

        if not all([company_name, java_package, author]):
            QMessageBox.warning(self, t["error"], t["fill_all_fields"])
            return

        # Створення папки output
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Видалення всіх попередніх файлів з папки output
        try:
            for file_path in output_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
        except Exception as exc:
            QMessageBox.warning(
                self,
                t["warning"],
                f"{t['delete_files_warning']}:\n{exc}",
            )

        # Збереження текстового файлу
        output_file = output_dir / "output.txt"
        content = f"Company Name: {company_name}\n"
        content += f"Java Package Name: {java_package}\n"
        content += f"Author: {author}\n"

        try:
            output_file.write_text(content, encoding="utf-8")
            QMessageBox.information(
                self,
                t["success"],
                f"{t['data_saved']}:\n{output_file}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                t["error"],
                f"{t['save_error']}:\n{exc}",
            )

    def change_language(self, language: str) -> None:
        """Змінює мову інтерфейсу"""
        if language != self.current_language:
            self.current_language = language
            self.update_ui_texts()
            self.save_language()

    def _get_config(self) -> dict:
        """Отримує конфігурацію з файлу"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def update_ui_texts(self) -> None:
        """Оновлює всі тексти інтерфейсу відповідно до вибраної мови"""
        t = self.translations[self.current_language]
        
        # Заголовок вікна
        self.setWindowTitle(t["window_title"])
        
        # Назви груп
        self.ui_elements["spreadsheet_group"].setTitle(t["spreadsheet"])
        self.ui_elements["tnc_group"].setTitle(t["tnc_platform"])
        self.ui_elements["xtl_group"].setTitle(t["xtl"])
        
        # Кнопки
        self.ui_elements["spreadsheet_button"].setText(t["select_file"])
        self.ui_elements["tnc_button"].setText(t["select_file"])
        self.ui_elements["xtl_button"].setText(t["select_file"])
        self.ui_elements["process_button"].setText(t["process_data"])
        
        # Labels
        self.ui_elements["company_label"].setText(t["company_name"])
        self.ui_elements["package_label"].setText(t["java_package"])
        self.ui_elements["author_label"].setText(t["author"])
        
        # Оновлюємо тексти "Не обрано" для необраних полів
        if self.spreadsheet_path is None:
            self.spreadsheet_label.setText(t["not_selected"])
        if self.tnc_platform_path is None:
            self.tnc_label.setText(t["not_selected"])
        if self.xtl_path is None:
            self.xtl_label.setText(t["not_selected"])

    def load_language(self) -> None:
        """Завантажує останню вибрану мову з конфігурації"""
        config = self._get_config()
        language = config.get("language", "UA")
        if language in ["UA", "EN"]:
            self.current_language = language
            # Тимчасово відключаємо сигнал, щоб уникнути подвійного виклику
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentText(language)
            self.language_combo.blockSignals(False)

    def save_language(self) -> None:
        """Зберігає вибрану мову у конфігурацію"""
        try:
            config = {}
            if self.config_file.exists():
                try:
                    with open(self.config_file, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except Exception:
                    pass

            config["language"] = self.current_language
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Якщо не вдалося зберегти, продовжуємо роботу


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
