# services/sheets.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from typing import List, Dict, Optional

# Настройки доступа
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetManager:
    def __init__(self, credentials_file: str, sheet_id: str):
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.client = None
        self.sheet = None

    def connect(self) -> bool:
        """Подключается к Google Таблице"""
        if self.sheet:
            return True
            
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, SCOPE)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.sheet_id)
            return True
        except Exception as e:
            logging.error(f"Ошибка подключения к Google Таблице: {e}")
            return False

    def get_available_slots(self, course_deep_link: str = None) -> List[Dict]:
        """Возвращает список свободных слотов. Если deep_link не указан, возвращает все доступные."""
        if not self.connect():
            return []
            
        try:
            worksheet = self.sheet.worksheet("Расписание")
            records = worksheet.get_all_records()
            
            available_slots = []
            for row in records:
                # Фильтрация по промо-коду, если он передан
                if course_deep_link and str(row.get('Промо-код (Deep Link)', '')).strip() != str(course_deep_link).strip():
                    continue
                    
                try:
                    limit = int(row.get('Лимит мест', 0))
                    occupied = int(row.get('Занято (Формула)', 0))
                    
                    if occupied < limit:
                        available_slots.append({
                            'date': row.get('Дата'),
                            'time': row.get('Время'),
                            'course_name': row.get('Название курса'),
                            'teacher': row.get('Преподаватель')
                        })
                except (ValueError, TypeError):
                    continue 

            return available_slots
        except Exception as e:
            logging.error(f"Ошибка при получении слотов: {e}")
            return []

    def book_slot(self, user_id: int, user_name: str, course_name: str, date: str, time: str, contact: str, role: str) -> bool:
        """Записывает пользователя на лист 'Записи'"""
        if not self.connect():
            return False
            
        try:
            worksheet = self.sheet.worksheet("Записи")
            # Добавляем строку: TG ID | Имя | Выбранный курс | Дата | Время | Контакт | Роль
            worksheet.append_row([user_id, user_name, course_name, date, time, contact, role])
            return True
        except Exception as e:
            logging.error(f"Ошибка при записи в таблицу: {e}")
            return False
            
    def get_user_name(self, user_id: int) -> Optional[str]:
        """Пытается найти имя пользователя на листе 'Пользователи'"""
        if not self.connect():
             return None
             
        try:
            worksheet = self.sheet.worksheet("Пользователи")
            ids = worksheet.col_values(1)
            names = worksheet.col_values(2)
            
            if str(user_id) in ids:
                index = ids.index(str(user_id))
                return names[index] if index < len(names) else None
            return None
        except Exception as e:
             logging.error(f"Ошибка при поиске пользователя: {e}")
             return None
             
    def save_user(self, user_id: int, user_name: str, phone: str = "") -> bool:
        """Сохраняет нового пользователя на лист 'Пользователи'"""
        if self.get_user_name(user_id):
             return True
             
        if not self.connect():
             return False
             
        try:
             worksheet = self.sheet.worksheet("Пользователи")
             worksheet.append_row([user_id, user_name, phone])
             return True
        except Exception as e:
             logging.error(f"Ошибка при сохранении пользователя: {e}")
             return False

# Создаем глобальный объект
sheet_manager = GoogleSheetManager(
    credentials_file="credentials.json", 
    sheet_id="1M2xHaH5eEKWSISlvqjBg1awSNjXKKM1RsfzJMss3Zcs"
)