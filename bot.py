
import logging
import pandas as pd
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

API_TOKEN = '7606185382:AAEvBBq3oBgCw3cbbOxEWs74DK1IiCwfCKg'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

EXCEL_PATH = "catalog.xlsx"
category_data = {}

def load_catalog():
    global category_data
    if not os.path.exists(EXCEL_PATH):
        category_data = {}
        return
    df = pd.read_excel(EXCEL_PATH)
    df = df[df['Цена'].notna() & df['Структура групп'].notna()]
    df = df[['Наименование', 'Структура групп', 'Цена']]
    grouped = df.groupby('Структура групп').apply(lambda g: g[['Наименование', 'Цена']].values.tolist()).to_dict()
    category_data = {}
    for category, items in grouped.items():
        text = f"*{category}*\n"
        for name, price in items:
            text += f"- {name} — {int(price)}₽\n"
        category_data[category] = text

load_catalog()

def get_category_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    row = []
    for i, category in enumerate(category_data.keys(), 1):
        row.append(KeyboardButton(category))
        if i % 2 == 0:
            kb.add(*row)
            row = []
    if row:
        kb.add(*row)
    kb.add(KeyboardButton("📝 Оформить заказ"), KeyboardButton("📞 Контакты"))
    return kb

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    if not category_data:
        await message.answer("Каталог пока не загружен. Попробуйте позже.")
    else:
        await message.answer("🗂 Выберите категорию товаров:", reply_markup=get_category_keyboard())

@dp.message_handler(commands=['обновить'])
async def update_cmd(message: types.Message):
    load_catalog()
    await message.answer("✅ Каталог обновлён!", reply_markup=get_category_keyboard())

@dp.message_handler(lambda message: message.text == "📝 Оформить заказ")
async def order_cmd(message: types.Message):
    await message.answer(
        "📦 *Оформление заказа:*\n"
        "💬 Telegram: @Krabamoreblg\n"
        "📱 WhatsApp: +7 963 814 36 34\n"
        "☎ Связь с администратором: +7 909 815 52 57",
        parse_mode="Markdown"
    )

@dp.message_handler(lambda message: message.text == "📞 Контакты")
async def contacts_cmd(message: types.Message):
    await message.answer(
        "📍 Адрес: г. Благовещенск, ул. Калинина 1\n"
        "📱 Телефон: +7 963 814 36 34\n"
        "🔗 Telegram: @Krabamoreblg"
    )

@dp.message_handler()
async def category_response(message: types.Message):
    cat = message.text.strip()
    if cat in category_data:
        await message.answer(category_data[cat], parse_mode="Markdown")
    else:
        await message.answer("Неизвестная команда. Используйте меню.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
