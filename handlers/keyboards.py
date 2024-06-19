from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

teacher_register_button = InlineKeyboardButton(
    text="Преподаватель",
    callback_data="register_teacher",  # Обратный вызов для преподавателя
)

listen_register_button = InlineKeyboardButton(
    text="Слушатель",
    callback_data="register_listener",  # Обратный вызов для слушателя
)

keyboard_register = InlineKeyboardMarkup(inline_keyboard=[[teacher_register_button, listen_register_button]])
