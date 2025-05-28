import logging
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook

API_TOKEN = '7606185382:AAEvBBq3oBgCw3cbbOxEWs74DK1IiCwfCKg'
WEBHOOK_HOST = 'https://krabamorebot.onrender.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 5000))

bot = Bot(API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

EXCEL_PATH = "catalog.xlsx"

def load_catalog():
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH)
        df = df[df['Цена'].notna() & df['Структура групп'].notna()]
        grouped = df.groupby('Структура групп', group_keys=False).apply(
            lambda g: g[['Наименование', 'Цена', 'Ед.изм.']].to_dict('records'),
            include_groups=False
        ).to_dict()
        return {k: '\n'.join([f"- {item['Наименование']} — {int(item['Цена'])}₽ за {item['Ед.изм.']}" for item in v]) for k, v in grouped.items()}
    return {}

category_data = load_catalog()

main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    "📦 Каталог", "📞 Контакты", "🛒 Заказать в WhatsApp", "🎁 Акции"
)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("👋 Добро пожаловать в 🦀 Краба Море!", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text == "📦 Каталог")
async def catalog_handler(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    [keyboard.add(cat) for cat in category_data.keys()]
    keyboard.add("🔙 Назад в меню")
    await msg.answer("🗂 Выберите категорию товаров:", reply_markup=keyboard)

@dp.message_handler(lambda msg: msg.text in category_data)
async def category_items(msg: types.Message):
    await msg.answer(category_data[msg.text])

@dp.message_handler(lambda msg: msg.text == "📞 Контакты")
async def contacts_cmd(msg: types.Message):
    await msg.answer("📍 г. Благовещенск, ул. Калинина 1\n📱 +7 963 814 36 34\n🔗 @Krabamoreblg")

@dp.message_handler(lambda msg: msg.text == "🛒 Заказать в WhatsApp")
async def whatsapp_cmd(msg: types.Message):
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("WhatsApp", url="https://wa.me/message/J4K3D275FBZZF1"))
    await msg.answer("Перейдите в WhatsApp 👇", reply_markup=markup)

@dp.message_handler(lambda msg: msg.text == "🎁 Акции")
async def promo_cmd(msg: types.Message):
    await msg.answer("🎁 Актуальные акции уточняйте в WhatsApp: https://wa.me/message/J4K3D275FBZZF1")

@dp.message_handler(lambda msg: msg.text == "🔙 Назад в меню")
async def back_menu(msg: types.Message):
    await msg.answer("⬅️ Главное меню", reply_markup=main_menu)

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

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
