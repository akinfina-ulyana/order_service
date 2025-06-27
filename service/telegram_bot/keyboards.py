from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def request_phone_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )