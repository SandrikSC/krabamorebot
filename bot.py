import logging
import os
import pandas as pd
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.utils.executor import start_webhook

# ==================== НАСТРОЙКИ ====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН")
CHANNEL_ID = None  # Укажи @канал, если нужна проверка подписки

# === КОНТАКТЫ МАГАЗИНА ===
SHOP_NAME = "Краба Море"
SHOP_ADDRESS = "ул. Калинина 1"
SHOP_PHONE = "+7 (963) 814-36-34"
WHATSAPP_NUMBER = "+79638143634"

# === ЗАКАЗЫ: куда писать ===
MANAGER_TELEGRAM = "@krabamoreblg"
MAX_LINK = "https://max.ru"

# ==================== ЛОГИРОВАНИЕ (ДОЛЖНО БЫТЬ ДО load_catalog) ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== ЗАГРУЗКА КАТАЛОГА ИЗ EXCEL ====================
def load_catalog():
    """Загружает каталог из catalog.xlsx"""
    try:
        if not os.path.exists("catalog.xlsx"):
            logger.error("Файл catalog.xlsx НЕ НАЙДЕН!")
            return {}
        df = pd.read_excel("catalog.xlsx")
        # Убираем строку-дубль заголовка если есть
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
        logger.error("Ошибка загрузки каталога: " + str(e))
        return {}

category_data = load_catalog()

# ==================== ТЕКСТЫ ====================
CONTACTS_TEXT = (
    "📞 <b>Контакты магазина Краба Море</b>\n\n"
    "☎️ Телефон: +7 (963) 814-36-34\n"
    "📍 Адрес: ул. Калинина 1\n"
    "💬 WhatsApp: +79638143634\n"
    "📱 Telegram: <a href=\"https://t.me/krabamoreblg\">@krabamoreblg</a>\n\n"
    "🕐 Режим работы: 10:00 — 22:00\n"
    "🚗 Доставка по городу от 500₽"
)

SALES_TEXT = (
    "🎁 <b>Акции и спецпредложения</b>\n\n"
    "🔥 При заказе от 5000₽ — доставка бесплатно!\n"
    "🎉 Скидка 10% на первый заказ по промокоду: <code>WELCOME10</code>\n"
    "💝 Подарочная упаковка — бесплатно при заказе от 3000₽\n\n"
    "Следите за новыми акциями в нашем канале!"
)

START_TEXT = (
    "👋 Добро пожаловать в <b>Краба Море</b>!\n\n"
    "🦀 Свежие морепродукты и деликатесы\n"
    "🚚 Доставка по городу\n"
    "💰 Цены от производителя\n\n"
    "Выберите действие в меню ниже 👇"
)

ORDER_TEXT = (
    "🛒 <b>Оформить заказ</b>\n\n"
    "Выберите удобный способ связи:\n\n"
    "💬 <b>Telegram</b> — быстрый ответ\n"
    "📱 <b>WhatsApp</b> — пришлём каталог\n"
    "🌐 <b>Max</b> — онлайн-оформление\n"
    "📞 <b>Телефон</b> — проконсультируем"
)

# ==================== WEBHOOK НАСТРОЙКИ (Render) ====================
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))
WEBHOOK_PATH = "/webhook/bot"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ==================== КЛАВИАТУРЫ ====================
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_menu.add("📋 Каталог", "📞 Контакты")
main_menu.add("🛒 Оформить заказ", "🎁 Акции")

catalog_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
for category in category_data.keys():
    catalog_menu.add(category)
catalog_menu.add("🔙 Назад в меню")

order_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
order_menu.add("💬 Написать в Telegram", "📱 Написать в WhatsApp")
order_menu.add("🌐 Заказать через Max", "📞 Позвонить")
order_menu.add("🔙 Назад в меню")

back_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_menu.add("🔙 Назад в меню")

# ==================== ПРОВЕРКА ПОДПИСКИ ====================
def subscription_required(channel=CHANNEL_ID):
    def decorator(handler):
        async def wrapper(*args, **kwargs):
            msg = None
            for arg in args:
                if isinstance(arg, types.Message):
                    msg = arg
                    break
            if not msg:
                return await handler(*args, **kwargs)
            if not channel:
                return await handler(*args, **kwargs)
            try:
                member = await bot.get_chat_member(channel, msg.from_user.id)
                if member.status in ["member", "administrator", "creator"]:
                    return await handler(*args, **kwargs)
                else:
                    await msg.answer(
                        "❗ Для использования бота подпишись на канал: " + str(channel),
                        reply_markup=types.ReplyKeyboardRemove()
                    )
            except Exception as e:
                logger.error("Ошибка проверки подписки: " + str(e))
                return await handler(*args, **kwargs)
        return wrapper
    return decorator

# ==================== КОМАНДЫ ====================
async def start_cmd(msg: types.Message):
    await msg.answer(START_TEXT, reply_markup=main_menu)

async def catalog_cmd(msg: types.Message):
    if not category_data:
        await msg.answer("⚠️ Каталог временно недоступен. Попробуйте позже.")
        return
    await msg.answer("📋 <b>Выберите категорию:</b>", reply_markup=catalog_menu)

async def contacts_cmd(msg: types.Message):
    await msg.answer(CONTACTS_TEXT, reply_markup=back_menu)

async def order_cmd(msg: types.Message):
    await msg.answer(ORDER_TEXT, reply_markup=order_menu)

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
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🌐 Открыть Max", url=MAX_LINK))
    await msg.answer(
        "🌐 <b>Заказ через Max</b>\n\n"
        "Откройте мессенджер Max и найдите нас по номеру:\n"
        "<code>+7 (963) 814-36-34</code>\n\n"
        "Или перейдите по ссылке ниже.",
        reply_markup=keyboard
    )

async def order_phone(msg: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📞 Позвонить", url="tel:+79638143634"))
    await msg.answer(
        "📞 <b>Позвонить нам</b>\n\n"
        "Телефон: +7 (963) 814-36-34\n"
        "Режим работы: 10:00 — 22:00",
        reply_markup=keyboard
    )

async def sales_cmd(msg: types.Message):
    await msg.answer(SALES_TEXT, reply_markup=back_menu)

async def back_to_menu(msg: types.Message):
    await msg.answer("⬅️ Главное меню", reply_markup=main_menu)

# ==================== ХЕНДЛЕРЫ ====================
@dp.message_handler(commands=["start"])
async def start_handler(msg: types.Message):
    await start_cmd(msg)

@dp.message_handler(commands=["catalog"])
@subscription_required()
async def catalog_handler(msg: types.Message):
    await catalog_cmd(msg)

@dp.message_handler(commands=["contacts"])
@subscription_required()
async def contacts_handler(msg: types.Message):
    await contacts_cmd(msg)

@dp.message_handler(commands=["order"])
@subscription_required()
async def order_handler(msg: types.Message):
    await order_cmd(msg)

@dp.message_handler(commands=["sales"])
@subscription_required()
async def sales_handler(msg: types.Message):
    await sales_cmd(msg)

@dp.message_handler(Text(equals="📋 Каталог", ignore_case=True))
@subscription_required()
async def catalog_btn(msg: types.Message):
    await catalog_cmd(msg)

@dp.message_handler(Text(equals="📞 Контакты", ignore_case=True))
@subscription_required()
async def contacts_btn(msg: types.Message):
    await contacts_cmd(msg)

@dp.message_handler(Text(equals="🛒 Оформить заказ", ignore_case=True))
@subscription_required()
async def order_btn(msg: types.Message):
    await order_cmd(msg)

@dp.message_handler(Text(equals="💬 Написать в Telegram", ignore_case=True))
@subscription_required()
async def order_tg_btn(msg: types.Message):
    await order_telegram(msg)

@dp.message_handler(Text(equals="📱 Написать в WhatsApp", ignore_case=True))
@subscription_required()
async def order_wa_btn(msg: types.Message):
    await order_whatsapp(msg)

@dp.message_handler(Text(equals="🌐 Заказать через Max", ignore_case=True))
@subscription_required()
async def order_max_btn(msg: types.Message):
    await order_max(msg)

@dp.message_handler(Text(equals="📞 Позвонить", ignore_case=True))
@subscription_required()
async def order_phone_btn(msg: types.Message):
    await order_phone(msg)

@dp.message_handler(Text(equals="🎁 Акции", ignore_case=True))
@subscription_required()
async def sales_btn(msg: types.Message):
    await sales_cmd(msg)

@dp.message_handler(Text(equals="🔙 Назад в меню", ignore_case=True))
@subscription_required()
async def back_handler(msg: types.Message):
    await back_to_menu(msg)

@dp.message_handler(lambda msg: msg.text in category_data)
@subscription_required()
async def category_handler(msg: types.Message):
    logger.info("Пользователь " + str(msg.from_user.id) + " выбрал: " + str(msg.text))
    await msg.answer(category_data[msg.text], reply_markup=back_menu)

@dp.message_handler()
async def catch_all(msg: types.Message):
    logger.warning("Необработанное от " + str(msg.from_user.id) + ": " + str(msg.text))
    await msg.answer(
        "❓ Я не понял команду. Используйте меню ниже или нажмите /start",
        reply_markup=main_menu
    )

@dp.errors_handler()
async def error_handler(update, exception):
    logger.error("Ошибка: " + str(exception), exc_info=True)
    if update and hasattr(update, 'message') and update.message:
        await update.message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
    return True

async def on_startup(dp):
    logger.info("Бот Краба Море запущен. Webhook: " + str(WEBHOOK_URL))
    logger.info("Категорий: " + str(len(category_data)))
    try:
        await bot.set_my_commands([
            types.BotCommand("start", "Главное меню"),
            types.BotCommand("catalog", "Каталог"),
            types.BotCommand("contacts", "Контакты"),
            types.BotCommand("order", "Оформить заказ"),
            types.BotCommand("sales", "Акции"),
        ])
        logger.info("Команды установлены")
    except Exception as e:
        logger.error("Команды не установлены: " + str(e))
    if WEBHOOK_URL and "render" in WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook установлен")
    else:
        logger.warning("WEBHOOK_URL не задан!")

async def on_shutdown(dp):
    logger.info("Удаляю webhook...")
    await bot.delete_webhook()
    await storage.close()
    await bot.session.close()
    logger.info("Бот остановлен")

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
        from aiogram.utils.executor import start_polling
        start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
