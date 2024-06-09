from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton)

main_kb = [
    [KeyboardButton(text='Подписаться на рассылку')],
    [KeyboardButton(text='Отписаться от рассылки')],
    [KeyboardButton(text='Количество правильных ответов')]
]

moderator_kb = [
    [KeyboardButton(text='Подписаться на рассылку')],
    [KeyboardButton(text='Отписаться от рассылки')],
    [KeyboardButton(text='Количество правильных ответов')],
    [KeyboardButton(text='Отправить Рассылку')],
    [KeyboardButton(text='Создать Урок')],
]

main = ReplyKeyboardMarkup(keyboard=main_kb,
                           resize_keyboard=True,
                           input_field_placeholder="Выберите пункт ниже")
