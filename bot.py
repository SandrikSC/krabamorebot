
import logging
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook
from aiohttp import web

API_TOKEN = '7606185382:AAEvBBq3oBgCw3cbbOxEWs74DK1IiCwfCKg'

WEBHOOK_HOST = 'https://krabamorebot.onrender.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.environ.get('PORT', 5000))

bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

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

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📦 Каталог"))
main_menu.add(KeyboardButton("📞 Контакты"), KeyboardButton("🛒 Заказать в WhatsApp"))
main_menu.add(KeyboardButton("🎁 Акции"))

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 <b>Приветствуем в 🦀 Краба Море!</b>\n"
        "Чем бы вы хотели себя порадовать сегодня?\n\n"
        "Смотрите наш каталог — крабы, креветки, раки, гребешки и многое другое уже ждут вас!\n\n"
        "Выберите нужный раздел в меню:",
        reply_markup=main_menu
    )

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
        "🎁 <b>Актуальные акции</b>\n"
        "Условия и наличие акций уточняйте, пожалуйста, в нашем WhatsApp: <a href='https://wa.me/message/J4K3D275FBZZF1'>нажмите здесь</a>",
        parse_mode="HTML"
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

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, lambda request: dp.process_update(types.Update(**await request.json())))
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT
    )
