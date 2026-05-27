# test_sheets.py
from services.sheets import sheet_manager

# Пробуем подключиться
print("Подключаемся...")
sheet_manager.connect()

# Пробуем найти слоты для промо-кода (убедитесь, что в таблице есть данные!)
slots = sheet_manager.get_available_slots("promo_exam")
print("Доступные слоты:", slots)