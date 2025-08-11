import logging
import os
import pandas as pd
from functools import wraps
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.utils.executor import start_webhook
from aiogram.utils.exceptions import ChatNotFound, BadRequest

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Не задан токен бота в переменной TELEGRAM_TOKEN")

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://krabamorebot.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 5000))

CHANNEL_USERNAME = "krabamoreblg"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME}"
CHANNEL_ID = f"@{CHANNEL_USERNAME}"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("krabamore")

bot = Bot(API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

EXCEL_PATH = "catalog.xlsx"
REQUIRED_COLUMNS = {"Наименование", "Цена", "Ед.изм.", "Структура групп"}

def load_catalog() -> dict:
    if not os.path.exists(EXCEL_PATH):
        log.warning("Каталог %s не найден", EXCEL_PATH)
        return {}
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        log.exception("Ошибка чтения каталога: %s", e)
        return {}
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        log.warning("Отсутствуют колонки: %s", ", ".join(missing))
        return {}
    df = df[df["Цена"].notna() & df["Структура групп"].notna()]
    catalog = {}
    for group, items in df.groupby("Структура групп"):
        lines = []
        for _, row in items.iterrows():
            try:
                price = int(float(row["Цена"]))
            except Exception:
                continue
            lines.append(f"- {row['Наименование']} — {price}₽ за {row['Ед.изм.']}")
        if lines:
            catalog[group] = "\n".join(lines)
    log.info("Каталог загружен. Групп: %d", len(catalog))
    return catalog

category_data = load_catalog()

main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("📦 Каталог", "📞 Контакты")
main_menu.add("🛒 Заказать в WhatsApp", "🎁 Акции")

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("creator", "administrator", "member")
    except (ChatNotFound, BadRequest):
        log.warning("Бот не видит канал %s. Добавь бота в канал как администратора.", CHANNEL_ID)
        return False

def subscription_required():
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: types.Message, *args, **kwargs):
            if await is_subscribed(message.from_user.id):
                return await handler(message, *args, **kwargs)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔔 Подписаться на канал", url=CHANNEL_LINK))
            kb.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
            await message.answer(
                "Чтобы пользоваться ботом, подпишитесь на наш канал:\n"
                f"👉 <a href='{CHANNEL_LINK}'>@{CHANNEL_USERNAME}</a>\n\n"
                "После подписки нажмите «Проверить подписку».",
                reply_markup=kb,
                disable_web_page_preview=True
            )
        return wrapper
    return decorator

@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def on_check_sub(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.answer("Подписка подтверждена!", show_alert=True)
        await call.message.answer("Отлично! Чем могу помочь? 👇", reply_markup=main_menu)
    else:
        await call.answer("Вы ещё не подписаны. Подпишитесь и повторите.", show_alert=True)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("👋 Добро пожаловать в 🦀 Краба Море! Чем бы вы хотели себя порадовать сегодня?", reply_markup=main_menu)

@dp.message_handler(commands=["catalog"])
@subscription_required()
async def catalog_cmd(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in category_data.keys():
        keyboard.add(cat)
    keyboard.add("🔙 Назад в меню")
    await msg.answer("🗂 Выберите категорию товаров:", reply_markup=keyboard)

@dp.message_handler(commands=["contacts"])
@subscription_required()
async def contacts_cmd(msg: types.Message):
    await msg.answer("📍 г. Благовещенск, ул. Калинина 1\n📱 +7 963 814 36 34\n🔗 @Krabamoreblg")

@dp.message_handler(commands=["order"])
@subscription_required()
async def order_cmd(msg: types.Message):
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("Открыть WhatsApp", url="https://wa.me/message/J4K3D275FBZZF1")
    )
    await msg.answer("Перейдите в WhatsApp 👇", reply_markup=markup)

@dp.message_handler(commands=["sales"])
@subscription_required()
async def sales_cmd(msg: types.Message):
    await msg.answer("🎁 Актуальные акции уточняйте в WhatsApp: https://wa.me/message/J4K3D275FBZZF1")

@dp.message_handler(Text(equals="📦 Каталог", ignore_case=True))
@subscription_required()
async def catalog_btn(msg: types.Message):
    await catalog_cmd(msg)

@dp.message_handler(Text(equals="📞 Контакты", ignore_case=True))
@subscription_required()
async def contacts_btn(msg: types.Message):
    await contacts_cmd(msg)

@dp.message_handler(Text(equals="🛒 Заказать в WhatsApp", ignore_case=True))
@subscription_required()
async def order_btn(msg: types.Message):
    await order_cmd(msg)

@dp.message_handler(Text(equals="🎁 Акции", ignore_case=True))
@subscription_required()
async def sales_btn(msg: types.Message):
    await sales_cmd(msg)

@dp.message_handler(Text(equals="🔙 Назад в меню", ignore_case=True))
@subscription_required()
async def back_menu(msg: types.Message):
    await msg.answer("⬅️ Главное меню", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text in category_data)
@subscription_required()
async def category_items(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Назад в меню")
    await msg.answer(category_data[msg.text], reply_markup=keyboard)

async def on_startup(dp):
    logging.info("Устанавливаю webhook: %s", WEBHOOK_URL)
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logging.info("Удаляю webhook")
    await bot.delete_webhook()

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
