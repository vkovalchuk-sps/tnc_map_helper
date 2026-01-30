# Installation and Build Guide

Детальна інструкція для встановлення, налаштування та побудови T&C Map Helper.

## Виставлення вимог

### Комп'ютер
- Windows 10/11 (64-bit)
- ~1 GB вільного місця на диску
- Інтернет-з'єднання (для завантаження Python та пакетів)

### Знання
- Базові знання командного рядка
- Розуміння git команд (опціонально)

---

## Крок 1: Встановлення Python 3.12

### Windows (Рекомендований метод)

1. Перейти на [python.org](https://www.python.org/downloads/)
2. Натиснути на "Downloads" → "Windows"
3. Завантажити "Windows installer (64-bit)"
4. Запустити installer (`.exe` файл)

**ВАЖЛИВО**: На екрані "Install Python 3.12":
- [ ] ✓ Перевірити: "Add Python 3.12 to PATH"
- Натиснути "Install Now"

5. Дочекатися завершення встановлення
6. Закрити installer

### Перевірка встановлення

Відкрити Command Prompt і набрати:
```cmd
python --version
```

Результат має бути:
```
Python 3.12.x (or higher)
```

Якщо бачите `'python' is not recognized`, то:
1. Перепропустити Python installer
2. Обрати "Modify installation"
3. Перевірити "Add Python to PATH"
4. Натиснути "Install"

---

## Крок 2: Завантаження Проекту

### Якщо маєте Git встановленим:

Відкрити Command Prompt у папці, де хочете зберігати проект:

```cmd
git clone <repository-url>
cd tnc_map_helper
```

### Якщо немаєте Git:

1. Натиснути "Code" → "Download ZIP" на GitHub
2. Розпакувати ZIP файл
3. Відкрити Command Prompt у розпакованій папці

---

## Крок 3: Налаштування Проекту

### 3.1 Відкрити Command Prompt

Перейти до папки проекту:
```cmd
cd C:\path\to\tnc_map_helper
```

Або натиснути:
- Windows + R
- Набрати: `cmd.exe`
- Натиснути Enter
- Набрати: `cd C:\path\to\tnc_map_helper`

### 3.2 Створити Virtual Environment

```cmd
python -m venv .venv
```

Це створить папку `.venv` з ізольованим Python середовищем.

### 3.3 Активувати Virtual Environment

На Windows:
```cmd
.venv\Scripts\activate
```

Успішна активація - в командному рядку з'явиться `(.venv)`:
```
(.venv) C:\path\to\tnc_map_helper>
```

### 3.4 Встановити Залежності

```cmd
pip install -r requirements.txt
```

Це встановить:
- PyQt6 (GUI)
- openpyxl (Excel)
- beautifulsoup4 (HTML/XML parsing)

Процес може зайняти 2-5 хвилин.

Перевірка:
```cmd
pip list
```

Повинні бути наявні PyQt6, openpyxl, beautifulsoup4.

---

## Крок 4: Запуск Програми

### Запуск з вихідного коду

```cmd
python main.py
```

Програма повинна запуститися з графічним вікном.

### Основні операції

1. **Завантажити Spreadsheet**: Натиснути кнопку вибору файла для `.xlsx`
2. **Завантажити CSV Template Archive**: Вибрати `.zip` файл
3. **Завантажити TOMMM Page**: Вибрати `.mhtml` файл
4. **Генерувати Артефакти**: Натиснути "Generate"
5. **Переглянути Результати**: Папка `output/`

### Вихід з Програми

- Закрити вікно програми
- Або натиснути Ctrl+Q

---

## Крок 5: Побудова Виконуваного Файла (EXE)

### Встановлення PyInstaller (якщо ще не встановлено)

```cmd
pip install pyinstaller
```

### Побудова

```cmd
python -m PyInstaller --clean --noconfirm TNCMapHelper.spec
```

**Опції:**
- `--clean` - видалити старі дані перед побудовою
- `--noconfirm` - не запитувати підтвердження
- `TNCMapHelper.spec` - файл конфігурації побудови

### Час побудови

- Перша побудова: 2-5 хвилин
- Наступні побудови: 30-60 секунд (без `--clean`)

### Результат

Виконуваний файл буде в:
```
dist\TnCMapHelper\TnCMapHelper.exe
```

Весь каталог `dist\TnCMapHelper\` потрібен для роботи.

### Запуск EXE файла

```cmd
dist\TnCMapHelper\TnCMapHelper.exe
```

Або подвійний клік на файл у File Explorer.

---

## Крок 6: Поширення

### Для внутрішнього використання

1. Скопіювати весь каталог `dist\TnCMapHelper\`
2. Розташувати на спільному сервері або хмарі
3. Користувачі запускають `TnCMapHelper.exe`

### Для зовнішнього користування

1. Архівувати `dist\TnCMapHelper\` в ZIP
2. Поділитися файлом
3. Користувачі розпаковують та запускають `.exe`

**Переваги распакованого варіанта:**
- ✓ Немає потреби в встановленні Python
- ✓ Быстрый запуск
- ✓ Портативний (kann на USB диску)

---

## Вирішення Проблем

### Проблема: Python не встановлений

```
'python' is not recognized as an internal or external command
```

**Рішення:**
1. Перевстановити Python
2. Обов'язково перевірити "Add Python to PATH" під час встановлення
3. Перезавантажити Command Prompt

### Проблема: Модуль не знайдений

```
ModuleNotFoundError: No module named 'PyQt6'
```

**Рішення:**
1. Перевірити, чи активований virtual environment (`(.venv)` має бути видимим)
2. Заново встановити залежності:
   ```cmd
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Проблема: База даних не знайдена

```
Error: database.db not found
```

**Рішення:**
- База даних створюється автоматично при першому запуску
- Якщо папка `application/database/` відсутня, створити її вручну
- Переконатися, що файл `requirements.txt` включає sqlite3 (він вже в Python)

### Проблема: GUI не з'являється

**Рішення:**
1. Перевірити версію Python: `python --version` (має бути 3.12+)
2. Перевірити встановлення PyQt6: `pip show PyQt6`
3. Спробувати запустити з більш детальним логуванням:
   ```cmd
   python -u main.py
   ```

### Проблема: PyInstaller побудова не вдається

```
ModuleNotFoundError during build
```

**Рішення:**
```cmd
# Видалити старі файли побудови
rmdir /s /q build dist __pycache__

# Переустановити PyInstaller
pip install --upgrade pyinstaller

# Спробувати заново
python -m PyInstaller --clean --noconfirm TNCMapHelper.spec
```

---

## Розвиток та Тестування

### Внесення змін

1. Активувати virtual environment: `.venv\Scripts\activate`
2. Редагувати файли Python
3. Тестувати: `python main.py`
4. Фіксити помилки
5. Повторити

### Контроль версій (Git)

```cmd
# Показати змінені файли
git status

# Додати файли для збереження
git add <file>

# Зберегти (commit)
git commit -m "Опис змін"

# Завантажити на сервер
git push origin main
```

---

## Швидка Довідка

### Встановлення з нуля
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Побудова EXE
```cmd
.venv\Scripts\activate
python -m PyInstaller --clean --noconfirm TNCMapHelper.spec
```

### Очистка
```cmd
rmdir /s /q build dist __pycache__ .venv
```

### Перевірка стану
```cmd
python --version
pip list
git status
```

---

## Додаткові Ресурси

- [Python Документація](https://docs.python.org/3/)
- [PyQt6 Документація](https://www.riverbankcomputing.com/software/pyqt/)
- [PyInstaller Документація](https://pyinstaller.org/)
- [Git Tutorial](https://git-scm.com/book/en/v2)

---

**Дата останнього оновлення**: 30 січня 2026
