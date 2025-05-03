
import logging
import pandas as pd
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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
    df = df[['Наименование', 'Структура групп', 'Цена', 'Ед.изм.']]
    grouped = df.groupby('Структура групп').apply(
        lambda g: g[['Наименование', 'Цена', 'Ед.изм.']].values.tolist()).to_dict()
    category_data = {}
    for category, items in grouped.items():
        text = f"*{category}*\n"
        for name, price, unit in items:
            suffix = f" за {unit}" if pd.notna(unit) else ""
            text += f"- {name} — {int(price)}₽{suffix}\n"
        category_data[category] = text

load_catalog()

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📦 Каталог"))
main_menu.add(KeyboardButton("📞 Контакты"), KeyboardButton("🛒 Заказать в WhatsApp"))
main_menu.add(KeyboardButton("🎁 Акции"))

async def check_subscription(user_id):
    try:
        chat_member = await bot.get_chat_member(chat_id='@krabamoreblg', user_id=user_id)
        return chat_member.status in ['member', 'creator', 'administrator']
    except:
        return False

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            "❗ Чтобы пользоваться ботом, подпишитесь на наш канал: @krabamoreblg"
        )
        return

    await message.answer("Добро пожаловать! Выберите нужный раздел:", reply_markup=main_menu)

@dp.message_handler(commands=['обновить'])
async def update_cmd(message: types.Message):
    load_catalog()
    await message.answer("✅ Каталог обновлён!")

@dp.message_handler(lambda message: message.text == "📦 Каталог")
async def catalog_handler(message: types.Message):
    if not category_data:
        await message.answer("Каталог пока не загружен.")
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    row = []
    for i, category in enumerate(category_data.keys(), 1):
        row.append(KeyboardButton(category))
        if i % 2 == 0:
            keyboard.add(*row)
            row = []
    if row:
        keyboard.add(*row)
    keyboard.add(KeyboardButton("🔙 Назад в меню"))
    await message.answer("🗂 Выберите категорию товаров:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "📞 Контакты")
async def contacts_cmd(message: types.Message):
    await message.answer(
        "📍 Адрес: г. Благовещенск, ул. Калинина 1\n"
        "📱 Телефон: +7 963 814 36 34\n"
        "🔗 Telegram: @Krabamoreblg"
    )

@dp.message_handler(lambda message: message.text == "🛒 Заказать в WhatsApp")
async def whatsapp_cmd(message: types.Message):
    button = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Открыть WhatsApp", url="https://wa.me/message/J4K3D275FBZZF1")
    )
    await message.answer("Нажмите на кнопку ниже, чтобы оформить заказ в WhatsApp 👇", reply_markup=button)

@dp.message_handler(lambda message: message.text == "🎁 Акции")
async def promo_cmd(message: types.Message):
    await message.answer(
        "🎁 *Актуальные акции*\n"
        "Условия и наличие акций уточняйте, пожалуйста, в нашем WhatsApp: [нажмите здесь](https://wa.me/message/J4K3D275FBZZF1)",
        parse_mode="Markdown"
    )

@dp.message_handler(lambda message: message.text == "🔙 Назад в меню")
async def back_to_main(message: types.Message):
    await message.answer("⬅ Вернулись в главное меню", reply_markup=main_menu)

@dp.message_handler()
async def category_response(message: types.Message):
    cat = message.text.strip()
    if cat in category_data:
        await message.answer(category_data[cat], parse_mode="Markdown")
    else:
        await message.answer("Неизвестная команда. Пожалуйста, используйте кнопки меню.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
