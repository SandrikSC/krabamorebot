diff --git a/bot.py b/bot.py
index 66aa658e2ae79891bd4ba45da9ee48ed581f791a..4e60c5ce81f6cd8f96569d8b1f329ae804e43aaf 100644
--- a/bot.py
+++ b/bot.py
@@ -1,33 +1,32 @@
 import logging
 import os
 import pandas as pd
 from collections import defaultdict
 from aiogram import Bot, Dispatcher, types
 from aiogram.contrib.fsm_storage.memory import MemoryStorage
 from aiogram.utils.executor import start_webhook, start_polling
-import asyncio
 
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
@@ -108,51 +107,57 @@ SALES_TEXT = (
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
-WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
+RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
+# Render автоматически задаёт RENDER_EXTERNAL_URL. WEBHOOK_URL можно указать
+# вручную, если бот размещён у другого провайдера.
+WEBHOOK_URL = os.getenv(
+    "WEBHOOK_URL",
+    f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else "",
+)
 
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
@@ -323,89 +328,77 @@ async def all_buttons_handler(msg: types.Message):
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
 
-# ==================== KEEP-ALIVE (чтобы Render не усыплял бота) ====================
-async def keep_alive():
-    """Отправляем себе пинг каждые 5 минут, чтобы бот не засыпал на Render"""
-    while True:
-        await asyncio.sleep(300)  # 5 минут
-        logger.info("Keep-alive ping")
-
 async def on_startup(dp):
     logger.info("Бот Краба Море запущен. Webhook: " + str(WEBHOOK_URL))
     logger.info("Категорий: " + str(len(category_data)))
-    
-    # Запускаем keep-alive
-    asyncio.create_task(keep_alive())
-    
+
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
-    
-    if WEBHOOK_URL and "render" in WEBHOOK_URL:
+
+    if WEBHOOK_URL:
         try:
             await bot.set_webhook(WEBHOOK_URL)
             logger.info("Webhook установлен: " + WEBHOOK_URL)
         except Exception as e:
             logger.error("Webhook не установлен: " + str(e))
     else:
         logger.warning("WEBHOOK_URL не задан! Используется polling.")
 
 async def on_shutdown(dp):
-    logger.info("Удаляю webhook...")
-    try:
-        await bot.delete_webhook()
-    except:
-        pass
+    # Не удаляем webhook: Render может остановить бесплатный сервис при простое.
+    # Сохранённый webhook позволит следующему сообщению Telegram разбудить сервис.
+    logger.info("Бот остановлен; webhook сохранён для следующего запуска")
     await storage.close()
     await bot.session.close()
-    logger.info("Бот остановлен")
 
 # ==================== ЗАПУСК ====================
 if __name__ == "__main__":
     if not TOKEN or TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН":
         logger.error("❌ TELEGRAM_TOKEN не задан!")
         exit(1)
 
-    if WEBHOOK_URL and "render" in WEBHOOK_URL:
+    if WEBHOOK_URL:
         start_webhook(
             dispatcher=dp,
             webhook_path=WEBHOOK_PATH,
             on_startup=on_startup,
             on_shutdown=on_shutdown,
-            skip_updates=True,
+            # Не отбрасываем сообщение, которое могло разбудить бесплатный сервис.
+            skip_updates=False,
             host=WEBAPP_HOST,
             port=WEBAPP_PORT,
         )
     else:
         logger.info("Запуск polling...")
         start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

