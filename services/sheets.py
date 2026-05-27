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
            logging.info("Успешное подключение к Google Таблице.")
            return True
        except Exception as e:
            logging.error(f"Ошибка подключения к Google Таблице: {e}")
            return False

    def get_available_slots(self, course_deep_link: str) -> List[Dict]:
        """Возвращает список свободных слотов для выбранного промо-кода курса"""
        if not self.connect():
            return []
            
        try:
            # Получаем все данные с листа "Расписание"
            worksheet = self.sheet.worksheet("Расписание")
            records = worksheet.get_all_records()
            
            available_slots = []
            for row in records:
                # Ищем нужный курс по deep_link и проверяем наличие мест
                if row.get('Промо-код (Deep Link)') == course_deep_link:
                    try:
                        limit = int(row.get('Лимит мест', 0))
                        occupied = int(row.get('Занято (Формула)', 0))
                        
                        if occupied < limit:
                            available_slots.append({
                                'date': row.get('Дата'),
                                'time': row.get('Время'),
                                'course_name': row.get('Название курса'),
                                'teacher': row.get('Преподаватель'),
                                'available_places': limit - occupied
                            })
                    except ValueError:
                         continue # Пропускаем строки с кривыми лимитами

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
            # Берем первый столбец (ID) и второй (Имя)
            ids = worksheet.col_values(1)
            names = worksheet.col_values(2)
            
            # col_values возвращает список строк, ищем строковое представление ID
            try:
                index = ids.index(str(user_id))
                # Индексы в gspread с 1, но в списках python с 0.
                # Если нашли ID на 3-й строке, его индекс в списке ids будет 2.
                # Имя будет под тем же индексом в списке names (если он достаточно длинный)
                if index < len(names):
                     return names[index]
            except ValueError:
                 return None # ID не найден
                 
        except Exception as e:
             logging.error(f"Ошибка при поиске пользователя: {e}")
             return None
             
    def save_user(self, user_id: int, user_name: str, phone: str = "") -> bool:
        """Сохраняет нового пользователя на лист 'Пользователи'"""
        # Сначала проверяем, нет ли его уже там
        if self.get_user_name(user_id):
             return True # Уже есть
             
        if not self.connect():
             return False
             
        try:
             worksheet = self.sheet.worksheet("Пользователи")
             worksheet.append_row([user_id, user_name, phone])
             return True
        except Exception as e:
             logging.error(f"Ошибка при сохранении пользователя: {e}")
             return False

# Создаем глобальный объект (синглтон) для использования в хэндлерах
sheet_manager = GoogleSheetManager(
    credentials_file="credentials.json", 
    sheet_id="1M2xHaH5eEKWSISlvqjBg1awSNjXKKM1RsfzJMss3Zcs"
)