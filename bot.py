import logging
import os
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
MANAGER_TELEGRAM = "@krabamoreblg"  # Telegram канал/бот магазина Краба Море
MAX_LINK = "https://max.ru"  # Ссылка на мессенджер Max (замени на свою, если есть)

# ==================== КАТАЛОГ (86 товаров, 13 категорий) ====================
category_data = {
    "🦀 Крабы": """🦀 <b>Крабы</b>

1. Краб Камчатский размер L — <b>3350₽</b>/кг
2. Краб Камчатский подарочный — <b>3200₽</b>/кг
3. Краб Колючий — <b>1850₽</b>/кг
4. Краб Камчатский размер S — <b>1650₽</b>/кг
5. Краб Камчатский размер М — <b>2800₽</b>/кг
6. Краб Волосатик крупный — <b>1100₽</b>/шт
7. Краб Стригун L3 — <b>2050₽</b>/кг
8. Салатное мясо камчатского краба  (крупно кусковое) — <b>3800₽</b>/кг
9. Фаланга Камчатского краба 10/12 — <b>5950₽</b>/кг
10. Кулак краба (вес) — <b>5950₽</b>/кг
11. Краб Камчатский размер L5 — <b>4300₽</b>/кг""",
    "🍥 Рулетики": """🍥 <b>Рулетики</b>

1. Рулетики из нерки с сырной начинкой, травами и орехами 150гр. — <b>500₽</b>/шт
2. Рулет из форели с сырной начинкой, мясом краба и свежими шампиньонами 400 гр. — <b>1700₽</b>/шт
3. Ролл из свежей форели со сливочным \"тартаром\" из камчатского краба и приморского гребешка 200гр. — <b>1000₽</b>/шт
4. Рулетики из нерки с сырной начинкой, каперсами и сыром чеддер 150гр — <b>500₽</b>/шт
5. Рулет из Тунца 400 гр. (с сырной начинкой, шампиньонами, каперсами и вяленными томатами) — <b>1050₽</b>/шт
6. Микс рулетов (форель, нерка, палтус, тунец) 400гр. — <b>1500₽</b>/шт
7. Рулетики из форели с сырной начинкой 150гр. — <b>650₽</b>/шт
8. Рулетики из нерки с сырной начинкой 150гр. — <b>500₽</b>/шт
9. Рулет из кижуча с сырной начинкой и свежими шампиньонами 400 гр. — <b>1100₽</b>/шт
10. Рулет из Тунца 400 гр. (с сырной начинкой, маслинами и спаржей) — <b>1050₽</b>/шт""",
    "🦐 Креветки/Раки": """🦐 <b>Креветки/Раки</b>

1. Креветка Ботан (крупный) — <b>4100₽</b>/кг
2. Креветка Тигровая 21/25 (очищенная) — <b>1900₽</b>/кг
3. Креветка северная (150+) — <b>1200₽</b>/кг
4. Креветка красная (Лангустин) С/М С/Г в панцире L1 10/20 — <b>2800₽</b>/шт
5. Креветка Тигровая черная 21/25 IQF н/р с/м шт — <b>1600₽</b>/кг
6. Креветка шримс медвежонок 70/90 — <b>2000₽</b>/кг
7. Креветка Тигровая 21/25 шт — <b>1750₽</b>/кг
8. Креветка Чилим M 600 грамм — <b>1900₽</b>/шт
9. Креветка Тигровая 08/12 шт — <b>2450₽</b>/кг
10. Креветка северная (Далькреветка) — <b>2400₽</b>/кг
11. Креветка северная (90/120) — <b>2000₽</b>/кг""",
    "🦑 Кальмар/Осьминог": """🦑 <b>Кальмар/Осьминог</b>

1. Кальмар щупальца сушеные — <b>5000₽</b>/кг
2. Кальмар (Филе) — <b>900₽</b>/кг
3. Щупальца кальмара без кожи — <b>1150₽</b>/кг
4. Кальмар щупальца г/к в кунжуте — <b>3000₽</b>/кг
5. Кальмар щупальца г/к в пикантные — <b>3000₽</b>/кг""",
    "🥚 Икра": """🥚 <b>Икра</b>

1. Икра горбуши — <b>8500₽</b>/кг
2. Икра Морского Ежа 100 гр. — <b>650₽</b>/шт""",
    "🍜 Супы/Вок": """🍜 <b>Супы/Вок</b>

1. Вок с кальмаром и овощами на черном тесте в томатном соусе (скин-упаковка) — <b>590₽</b>/шт
2. Жульен из форели со свежими шампиньонами, каперсами, вялеными томатами, сырами чеддер и моцарела — <b>500₽</b>/шт
3. Том-Ям со свежими морепродуктами и тайскими специями 450 грамм — <b>585₽</b>/шт
4. Вок с кальмаром и овощами на зеленом тесте с сырным соусом (скин-упаковка) — <b>590₽</b>/шт
5. Вок с креветкой и овощами на белом тесте в устричном соусе (скин-упаковка) — <b>590₽</b>/шт
6. Крем-суп для запекания из шампиньонов и гребешка под сыром чеддер 300 грамм — <b>500₽</b>/шт""",
    "🥫 Пресервы": """🥫 <b>Пресервы</b>

1. Горбуша тихоокеанская натуральная ТМ \"Nord Pilgrim\" ЖБ 245 гр. — <b>200₽</b>/шт
2. Печень трески натуральная 115 гр. — <b>350₽</b>/шт
3. Мясо краба равношипого в солевой заливке. Первый сорт ЖБ 240 гр. — <b>999₽</b>/шт""",
    "🐟 Рыба": """🐟 <b>Рыба</b>

1. Сибас 400-600 н/р Турция — <b>1350₽</b>/кг
2. Корюшка Вяленая — <b>3200₽</b>/кг
3. Филе форели в соусе \"Бедный парижанин\" с/м в/у 350гр. — <b>650₽</b>/шт
4. Нерка D-Trim с/с Аякс — <b>2250₽</b>/кг
5. Стейк (филе) тунца — <b>650₽</b>/шт
6. Стейк Палтус — <b>2200₽</b>/кг
7. Дорадо 400-600 н/р Турция — <b>1350₽</b>/кг
8. Форель Слабосоленая филе (Trim-D) — <b>2800₽</b>/кг
9. Филе форели в соусе \"Кольбер\" с/м в/у 350гр. — <b>650₽</b>/шт""",
    "🥩 Котлеты": """🥩 <b>Котлеты</b>

1. Котлеты из тунца и нерки с сыром моцарелла и цукини 500гр. — <b>650₽</b>/шт
2. Котлеты из лосося (кета) 500 гр. — <b>550₽</b>/шт
3. Медальоны из тунца — <b>550₽</b>/шт
4. Котлета из палтуса и форели с сыром и вялеными томатами 500гр. — <b>1050₽</b>/шт
5. Котлеты из кальмара и приморского гребешка500гр. — <b>1050₽</b>/шт""",
    "🐚 Гребешки/Мидии": """🐚 <b>Гребешки/Мидии</b>

1. Мидии в раковине д/запекания с сырной начинкой, грибами и специями — <b>900₽</b>/кг
2. Гребешок на створке — <b>1400₽</b>/кг
3. Гребешок в раковине д/запекания по-шанхайски с сырной начинкой, беконом, грибами и спаржей 1/5 — <b>1350₽</b>/кг
4. Гребешок в раковине д/запекания по-шанхайски \"4 сыра\" 1/5 — <b>1350₽</b>/кг
5. Мидии 30-40 на ракушке 1 кг. — <b>650₽</b>/шт
6. Гребешок в раковине д/запекания по-шанхайски с сырной начинкой, кальмаром и филе палтуса 1/5 — <b>1350₽</b>/кг
7. Гребешок Сахалинский — <b>4200₽</b>/кг
8. Мидии в раковине д/запекания с сырной начинкой и палтусом — <b>900₽</b>/кг
9. Гребешок в раковине д/запекания по-шанхайски с сырной начинкой, креветкой и спаржей 1/5 — <b>1350₽</b>/кг""",
    "🦑 Молюск": """🦑 <b>Молюск</b>

1. Угорь жаренный 30% — <b>2750₽</b>/кг
2. Клемы Вонголе в раковине — <b>325₽</b>/шт
3. Трепанг на меду (70/30) 500 грамм — <b>1250₽</b>/шт
4. Мясо мидий в/м 100-200 — <b>900₽</b>/кг
5. Устрицы — <b>900₽</b>/кг
6. Трубач очищеный Дальневосточный(Аналог мясу Рапана) — <b>2000₽</b>/кг
7. Морской Коктейль — <b>550₽</b>/шт""",
    "🥟 Пельмени": """🥟 <b>Пельмени</b>

1. Равиоли с креветкой 300 гр (Зеленые равиоли с креветкой и сыром) — <b>580₽</b>/шт
2. Пельмени с неркой \"по домашнему\"  300гр. — <b>450₽</b>/шт
3. Пельмени с крабом 300 гр (черные пельмени с крабом, палтусом и сыром рикота) — <b>580₽</b>/шт""",
    "🍢 Шашлычки": """🍢 <b>Шашлычки</b>

1. Шашлычки из тунца, палтуса и болгарского перца со специями 400гр. — <b>1750₽</b>/шт
2. Шашлычки из тунца и маслин в соево-чесночном соусе 400гр. — <b>1250₽</b>/шт
3. Шашлычки из форели, помидор черри, свежих шампиньонов в соусе терияки 400 гр. — <b>1150₽</b>/шт
4. Шашлычки из тунца, палтуса и болгарского перца со специями 400гр. — <b>1750₽</b>/шт
5. Шашлычки из гребешка, помидоров черри и свежих шампиньонов со специями, травами и цитрусом 400гр. — <b>1500₽</b>/шт""",
}

# ==================== ТЕКСТЫ ====================
CONTACTS_TEXT = (
    "📞 <b>Контакты магазина Краба Море</b>\n\n"
    "☎️ Телефон: +7 (963) 814-36-34\n"
    "📍 Адрес: ул. Калинина 1\n"
    "💬 WhatsApp: +79638143634\n"
    "📱 Telegram: " + MANAGER_TELEGRAM + "\n\n"
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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
        async def wrapper(msg: types.Message, *args, **kwargs):
            if not channel:
                return await handler(msg, *args, **kwargs)
            try:
                member = await bot.get_chat_member(channel, msg.from_user.id)
                if member.status in ["member", "administrator", "creator"]:
                    return await handler(msg, *args, **kwargs)
                else:
                    await msg.answer(
                        "❗ Для использования бота подпишись на канал: " + str(channel),
                        reply_markup=types.ReplyKeyboardRemove()
                    )
            except Exception as e:
                logger.error("Ошибка проверки подписки: " + str(e))
                return await handler(msg, *args, **kwargs)
        return wrapper
    return decorator

# ==================== КОМАНДЫ ====================
async def start_cmd(msg: types.Message):
    await msg.answer(START_TEXT, reply_markup=main_menu)

async def catalog_cmd(msg: types.Message):
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
        "Нажмите кнопку ниже, чтобы связаться с менеджером напрямую.\n\n"
        "Менеджер: " + MANAGER_TELEGRAM,
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
    keyboard.add(types.InlineKeyboardButton("🌐 Перейти на Max", url=MAX_LINK))
    await msg.answer(
        "🌐 <b>Заказ через Max</b>\n\n"
        "Оформите заказ онлайн на нашей странице.\n\n"
        "Или напишите менеджеру в Telegram/WhatsApp.",
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

# ==================== ХЕНДЛЕРЫ КОМАНД ====================
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

# ==================== ХЕНДЛЕРЫ КНОПОК ====================
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

# ==================== ХЕНДЛЕР КАТЕГОРИЙ ====================
@dp.message_handler(lambda msg: msg.text in category_data)
@subscription_required()
async def category_handler(msg: types.Message):
    logger.info("Пользователь " + str(msg.from_user.id) + " выбрал: " + str(msg.text))
    await msg.answer(category_data[msg.text], reply_markup=back_menu)

# ==================== ЛОВУШКА ====================
@dp.message_handler()
async def catch_all(msg: types.Message):
    logger.warning("Необработанное сообщение от " + str(msg.from_user.id) + ": " + str(msg.text))
    await msg.answer(
        "❓ Я не понял команду. Используйте меню ниже или нажмите /start",
        reply_markup=main_menu
    )

# ==================== ОБРАБОТКА ОШИБОК ====================
@dp.errors_handler()
async def error_handler(update, exception):
    logger.error("Ошибка при обработке: " + str(exception), exc_info=True)
    if update and hasattr(update, 'message') and update.message:
        await update.message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
    return True

# ==================== СТАРТ / СТОП ====================
async def on_startup(dp):
    logger.info("Бот Краба Море запущен. Webhook URL: " + str(WEBHOOK_URL))
    logger.info("Категорий: " + str(len(category_data)) + ", товаров: 86")
    
    try:
        await bot.set_my_commands([
            types.BotCommand("start", "Главное меню"),
            types.BotCommand("catalog", "Каталог товаров"),
            types.BotCommand("contacts", "Контакты"),
            types.BotCommand("order", "Оформить заказ"),
            types.BotCommand("sales", "Акции"),
        ])
        logger.info("Команды меню установлены")
    except Exception as e:
        logger.error("Не удалось установить команды: " + str(e))
    
    if WEBHOOK_URL and "render" in WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook установлен")
    else:
        logger.warning("WEBHOOK_URL не задан или некорректен!")

async def on_shutdown(dp):
    logger.info("Удаляю webhook...")
    await bot.delete_webhook()
    await storage.close()
    await bot.session.close()
    logger.info("Бот остановлен")

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    if not TOKEN or TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН":
        logger.error("❌ TELEGRAM_TOKEN не задан! Установите переменную окружения.")
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
        logger.info("Запуск в режиме polling (для локального теста)...")
        from aiogram.utils.executor import start_polling
        start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
