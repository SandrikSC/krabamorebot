diff --git a/bot.py b/bot.py
index 0b820606c8f140cbb74c3370311701a650e9a96c..318aec9478471396b14f7ba552255e93fcd05b52 100644
--- a/bot.py
+++ b/bot.py
@@ -141,41 +141,48 @@ async def contacts_btn(msg: types.Message):
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
+    await bot.set_my_commands([
+        types.BotCommand("start", "Запуск бота"),
+        types.BotCommand("catalog", "Каталог"),
+        types.BotCommand("contacts", "Контакты"),
+        types.BotCommand("order", "Заказать в WhatsApp"),
+        types.BotCommand("sales", "Акции"),
+    ])
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
