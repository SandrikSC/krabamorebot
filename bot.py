
import logging
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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
def load_catalog():
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH)
        df = df[df['Цена'].notna() & df['Структура групп'].notna()]
        grouped = df.groupby('Структура групп', group_keys=False).apply(
            lambda g: g[['Наименование', 'Цена', 'Ед.изм.']].to_dict('records')).to_dict()
        return {k: '\n'.join([f"- {item['Наименование']} — {int(item['Цена'])}₽ за {item['Ед.изм.']}" for item in v]) for k, v in grouped.items()}
    return {}

category_data = load_catalog()

main_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("📦 Каталог"), KeyboardButton("📞 Контакты"),
    KeyboardButton("🛒 Заказать в WhatsApp"), KeyboardButton("🎁 Акции"),
    KeyboardButton("🛍 Магазин")
)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("👋 <b>Приветствуем в 🦀 Краба Море!</b>\nЧем бы вы хотели себя порадовать сегодня?", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text.strip() == "📦 Каталог")
async def catalog_handler(msg: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    [keyboard.add(cat) for cat in category_data.keys()]
    keyboard.add("🔙 Назад в меню")
    await msg.answer("🗂 Выберите категорию товаров:", reply_markup=keyboard)

@dp.message_handler(lambda msg: msg.text.strip() in category_data)
async def category_items(msg: types.Message):
    await msg.answer(category_data[msg.text.strip()])

@dp.message_handler(lambda msg: msg.text.strip() == "📞 Контакты")
async def contacts_cmd(msg: types.Message):
    await msg.answer("📍 Адрес: г. Благовещенск, ул. Калинина 1\n📱 Телефон: +7 963 814 36 34\n🔗 Telegram: @Krabamoreblg")

@dp.message_handler(lambda msg: msg.text.strip() == "🛒 Заказать в WhatsApp")
async def whatsapp_cmd(msg: types.Message):
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Открыть WhatsApp", url="https://wa.me/message/J4K3D275FBZZF1"))
    await msg.answer("Для заказа перейдите в WhatsApp 👇", reply_markup=markup)

async def handle_webhook(request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return web.Response()

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
