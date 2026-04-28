import logging
import os
import pandas as pd
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook, start_polling
import asyncio

# ==================== НАСТРОЙКИ ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН")

# === КОНТАКТЫ МАГАЗИНА ===
SHOP_NAME = "Краба Море"
SHOP_ADDRESS = "ул. Калинина 1"
SHOP_PHONE = "+7 (963) 814-36-34"
WHATSAPP_NUMBER = "+79638143634"

# === ЗАКАЗЫ ===
MANAGER_TELEGRAM = "@krabamoreblg"
MAX_LINK = "https://max.ru/u/f9LHodD0cOKyWMZFNxZNIEc752Qto0d0WidvEMDukqVCdvuhBUu3bo_7_n0"

# ==================== ЛОГИРОВАНИЕ ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== ЗАГРУЗКА КАТАЛОГА ====================
def load_catalog():
    try:
        # Проверяем несколько путей (для Render и локальной разработки)
        possible_paths = ["catalog.xlsx", "/app/catalog.xlsx", "./catalog.xlsx", os.path.join(os.path.dirname(__file__), "catalog.xlsx")]
        catalog_path = None
        
        for path in possible_paths:
            if os.path.exists(path):
                catalog_path = path
                logger.info(f"Найден catalog.xlsx: {path}")
                break
        
        if not catalog_path:
            logger.error("Файл catalog.xlsx НЕ НАЙДЕН ни в одном из путей!")
            logger.error(f"Текущая директория: {os.getcwd()}")
            logger.error(f"Содержимое директории: {os.listdir('.')}")
            return {}
            
        df = pd.read_excel(catalog_path)
        df = df[df.iloc[:, 0] != df.columns[0]].reset_index(drop=True)

        emoji_map = {
            "Крабы": "🦀", "Креветки/Раки": "🦐", "Рулетики": "🍥", "Рыба": "🐟",
            "Гребешки/Мидии": "🐚", "Молюск": "🦑", "Супы/Вок": "🍜",
            "Кальмар/Осьминог": "🦑", "Котлеты": "🥩", "Шашлычки": "🍢",
            "Пресервы": "🥫", "Пельмени": "🥟", "Икра": "🥚"
        }

        categories = defaultdict(list)
        for _, row in df.iterrows():
            name = str(row.iloc[0]).strip()
            cat = str(row.iloc[1]).strip().replace("\\", "/")
            price = str(row.iloc[2]).strip()
            unit = str(row.iloc[3]).strip()
            if name and cat and price and name != "nan":
                categories[cat].append({"name": name, "price": price, "unit": unit})

        category_data = {}
        for cat, items in categories.items():
            emoji = emoji_map.get(cat, "📦")
            lines = [emoji + " <b>" + cat + "</b>\n"]
            for i, item in enumerate(items, 1):
                lines.append(str(i) + ". " + item["name"] + " — <b>" + item["price"] + "₽</b>/" + item["unit"])
            category_data[emoji + " " + cat] = "\n".join(lines)

        logger.info("Каталог загружен: " + str(len(category_data)) + " категорий, " + str(len(df)) + " товаров")
        return category_data
    except Exception as e:
        logger.error("Ошибка загрузки каталога: " + str(e), exc_info=True)
        return {}

category_data = load_catalog()

# ==================== ТЕКСТЫ ====================
WELCOME_TEXT = (
    "👋 <b>Добро пожаловать в магазин Краба Море!</b>\n\n"
    "🦀 Свежие морепродукты и деликатесы\n"
    "🚚 Доставка по городу\n"
    "💰 За лучшим — к нам. Остальное и так найдётся\n\n"
    "<b>Для начала работы нажмите кнопку ниже 👇</b>"
)

CONTACTS_TEXT = (
    "📞 <b>Контакты магазина Краба Море</b>\n\n"
    "☎️ Телефон: +7 (963) 814-36-34\n"
    "📍 Адрес: ул. Калинина 1\n"
    "💬 WhatsApp: +79638143634\n"
    "📱 Telegram: <a href=\"https://t.me/krabamoreblg\">@krabamoreblg</a>\n\n"
    "🕐 <b>Режим работы:</b>\n    10:00 — 21:00\n\n"
    "⚠️ <i>С 20:00 до 21:00 предварительно звоните — можем находиться на доставке</i>"
)

SALES_TEXT = (
    "🎁 <b>Акции и доставка</b>\n\n"
    "🚚 <b>Бесплатная доставка по городу при заказе от 5000₽</b>\n\n"
    "📍 <b>Доставка по тарифу такси:</b>\n"
    "Чигири, Моховая падь, Аэропорт, Астрахановка, Радиоцентр, Верхнеблаговещенск, Молокозавод\n\n"
    "💬 <b>Скидки и акции уточняйте у менеджера</b> в чате или по телефону\n\n"
    "📢 Следите за нашими поступлениями в <a href=\"https://t.me/krabamoreblg\">Telegram канале</a>"
)

START_TEXT = (
    "👋 Добро пожаловать в <b>Краба Море</b>!\n\n"
    "🦀 Свежие морепродукты и деликатесы\n"
    "🚚 Доставка по городу\n"
    "💰 За лучшим — к нам. Остальное и так найдётся\n\n"
    "Выберите действие в меню ниже 👇"
)

ORDER_TEXT = (
    "🛒 <b>Оформить заказ</b>\n\n"
    "Выберите удобный способ связи:\n\n"
    "💬 <b>Telegram</b> — быстрый ответ\n"
    "📱 <b>WhatsApp</b> — быстрый ответ\n"
    "🌐 <b>Max</b> — онлайн-оформление\n"
    "📞 <b>Телефон</b> — проконсультируем"
)

# ==================== WEBHOOK НАСТРОЙКИ (для Render) ====================
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))
WEBHOOK_PATH = "/webhook/bot"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ==================== КЛАВИАТУРЫ ====================
# Клавиатура для новых пользователей (до /start)
welcome_keyboard = types.InlineKeyboardMarkup()
welcome_keyboard.add(types.InlineKeyboardButton("🚀 Запустить бота", callback_data="start_bot"))

def get_main_menu():
    """Создаём меню заново при каждом вызове — надёжнее"""
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    menu.add("📋 Каталог", "📞 Контакты")
    menu.add("🛒 Оформить заказ", "🎁 Акции")
    return menu

def get_catalog_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for category in category_data.keys():
        menu.add(category)
    menu.add("🔙 Назад в меню")
    return menu

def get_order_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    menu.add("💬 Написать в Telegram", "📱 Написать в WhatsApp")
    menu.add("🌐 Заказать через Max", "📞 Позвонить")
    menu.add("🔙 Назад в меню")
    return menu

def get_back_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add("🔙 Назад в меню")
    return menu

# ==================== КОМАНДЫ ====================
async def welcome_cmd(msg: types.Message):
    """Приветствие для новых пользователей"""
    await msg.answer(WELCOME_TEXT, reply_markup=welcome_keyboard)

async def start_cmd(msg: types.Message):
    await msg.answer(START_TEXT, reply_markup=get_main_menu())

async def catalog_cmd(msg: types.Message):
    if not category_data:
        await msg.answer("⚠️ Каталог временно недоступен. Попробуйте позже.")
        return
    await msg.answer("📋 <b>Выберите категорию:</b>", reply_markup=get_catalog_menu())

async def contacts_cmd(msg: types.Message):
    await msg.answer(CONTACTS_TEXT, reply_markup=get_back_menu())

async def order_cmd(msg: types.Message):
    await msg.answer(ORDER_TEXT, reply_markup=get_order_menu())

async def order_telegram(msg: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/krabamoreblg"))
    await msg.answer(
        "💬 <b>Заказ через Telegram</b>\n\n"
        "Нажмите кнопку ниже, чтобы связаться с нами напрямую.\n\n"
        "Канал: @krabamoreblg",
        reply_markup=keyboard
    )

async def order_whatsapp(msg: types.Message):
    wa_link = "https://wa.me/79638143634"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📱 Написать в WhatsApp", url=wa_link))
    await msg.answer(
        "📱 <b>Заказ через WhatsApp</b>\n\n"
        "Нажмите кнопку ниже, чтобы перейти в WhatsApp.\n\n"
        "Номер: +7 (963) 814-36-34",
        reply_markup=keyboard
    )

async def order_max(msg: types.Message):
    # Пробуем несколько форматов ссылок для Max
    max_links = [
        "https://max.ru/u/f9LHodD0cOKyWMZFNxZNIEc752Qto0d0WidvEMDukqVCdvuhBUu3bo_7_n0",
        "max://u/f9LHodD0cOKyWMZFNxZNIEc752Qto0d0WidvEMDukqVCdvuhBUu3bo_7_n0",
        "https://max.ru/join?invite=f9LHodD0cOKyWMZFNxZNIEc752Qto0d0WidvEMDukqVCdvuhBUu3bo_7_n0"
    ]
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("🌐 Открыть в браузере", url=max_links[0]))
    keyboard.add(types.InlineKeyboardButton("🌐 Открыть в приложении Max", url=max_links[1]))
    
    await msg.answer(
        "🌐 <b>Заказ через Max</b>\n\n"
        "Выберите способ открытия:\n"
        "• <b>В браузере</b> — если приложение не установлено\n"
        "• <b>В приложении</b> — если Max установлен\n\n"
        "Или свяжитесь с нами через Telegram/WhatsApp.",
        reply_markup=keyboard
    )

async def order_phone(msg: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📞 Позвонить", url="tel:+79638143634"))
    await msg.answer(
        "📞 <b>Позвонить нам</b>\n\n"
        "Телефон: +7 (963) 814-36-34\n"
        "Режим работы: 10:00 — 21:00\n"
        "⚠️ С 20:00 до 21:00 предварительно звоните — можем быть на доставке",
        reply_markup=keyboard
    )

async def sales_cmd(msg: types.Message):
    await msg.answer(SALES_TEXT, reply_markup=get_back_menu())

async def back_to_menu(msg: types.Message):
    await msg.answer("⬅️ Главное меню", reply_markup=get_main_menu())

# ==================== ХЕНДЛЕРЫ ====================
# 1. Команда /start
@dp.message_handler(commands=["start"])
async def start_handler(msg: types.Message):
    await start_cmd(msg)

# 2. Команды
@dp.message_handler(commands=["catalog", "contacts", "order", "sales"])
async def commands_handler(msg: types.Message):
    if msg.text == "/catalog":
        await catalog_cmd(msg)
    elif msg.text == "/contacts":
        await contacts_cmd(msg)
    elif msg.text == "/order":
        await order_cmd(msg)
    elif msg.text == "/sales":
        await sales_cmd(msg)

# 3. Callback от inline-кнопки "Запустить бота"
@dp.callback_query_handler(lambda c: c.data == "start_bot")
async def process_callback_start(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await start_cmd(callback_query.message)

# 4. УНИВЕРСАЛЬНЫЙ ХЕНДЛЕР ДЛЯ ВСЕХ КНОПОК
@dp.message_handler()
async def all_buttons_handler(msg: types.Message):
    text = msg.text.lower()
    original_text = msg.text

    logger.info("Получено сообщение: '" + original_text + "' от user=" + str(msg.from_user.id))

    # Назад в меню — ПРИОРИТЕТНАЯ ПРОВЕРКА
    if "назад" in text or "меню" in text or text == "🔙 назад в меню":
        logger.info("ОБНАРУЖЕНО 'назад' или 'меню'")
        await back_to_menu(msg)
        return

    # Каталог
    elif "каталог" in text:
        await catalog_cmd(msg)
        return

    # Контакты
    elif "контакт" in text:
        await contacts_cmd(msg)
        return

    # Оформить заказ
    elif "заказ" in text or "оформить" in text:
        await order_cmd(msg)
        return

    # Акции
    elif "акци" in text:
        await sales_cmd(msg)
        return

    # Telegram
    elif "telegram" in text or "телеграм" in text:
        await order_telegram(msg)
        return

    # WhatsApp
    elif "whatsapp" in text or "ватсап" in text:
        await order_whatsapp(msg)
        return

    # Max
    elif "max" in text:
        await order_max(msg)
        return

    # Позвонить
    elif "позвонить" in text or "телефон" in text:
        await order_phone(msg)
        return

    # Категории товаров
    elif original_text in category_data:
        logger.info("Пользователь выбрал категорию: " + original_text)
        await msg.answer(category_data[original_text], reply_markup=get_back_menu())
        return

    # Неизвестная команда — показываем приветствие
    else:
        logger.warning("Необработанное: '" + original_text + "'")
        await welcome_cmd(msg)

@dp.errors_handler()
async def error_handler(update, exception):
    logger.error("Ошибка: " + str(exception), exc_info=True)
    if update and hasattr(update, 'message') and update.message:
        try:
            await update.message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
        except:
            pass
    return True

# ==================== KEEP-ALIVE (чтобы Render не усыплял бота) ====================
async def keep_alive():
    """Отправляем себе пинг каждые 5 минут, чтобы бот не засыпал на Render"""
    while True:
        await asyncio.sleep(300)  # 5 минут
        logger.info("Keep-alive ping")

async def on_startup(dp):
    logger.info("Бот Краба Море запущен. Webhook: " + str(WEBHOOK_URL))
    logger.info("Категорий: " + str(len(category_data)))
    
    # Запускаем keep-alive
    asyncio.create_task(keep_alive())
    
    try:
        await bot.set_my_commands([
            types.BotCommand("start", "🚀 Запустить бота"),
            types.BotCommand("catalog", "📋 Каталог"),
            types.BotCommand("contacts", "📞 Контакты"),
            types.BotCommand("order", "🛒 Оформить заказ"),
            types.BotCommand("sales", "🎁 Акции"),
        ])
        logger.info("Команды установлены")
    except Exception as e:
        logger.error("Команды не установлены: " + str(e))
    
    if WEBHOOK_URL and "render" in WEBHOOK_URL:
        try:
            await bot.set_webhook(WEBHOOK_URL)
            logger.info("Webhook установлен: " + WEBHOOK_URL)
        except Exception as e:
            logger.error("Webhook не установлен: " + str(e))
    else:
        logger.warning("WEBHOOK_URL не задан! Используется polling.")

async def on_shutdown(dp):
    logger.info("Удаляю webhook...")
    try:
        await bot.delete_webhook()
    except:
        pass
    await storage.close()
    await bot.session.close()
    logger.info("Бот остановлен")

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    if not TOKEN or TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН":
        logger.error("❌ TELEGRAM_TOKEN не задан!")
        exit(1)

    if WEBHOOK_URL and "render" in WEBHOOK_URL:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
    else:
        logger.info("Запуск polling...")
        start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
