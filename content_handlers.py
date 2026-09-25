import os
import base64
from io import BytesIO
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from content_ai import generate_content

OWNER_TELEGRAM_ID = int(os.getenv("OWNER_TELEGRAM_ID", "364573446"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@krabamoreblg")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/krabamoreblg")

class ContentStates(StatesGroup):
    waiting_prompt = State()

def is_owner(user_id):
    return int(user_id) == OWNER_TELEGRAM_ID

def content_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎨 Пост + картинка", callback_data="content_new"),
        types.InlineKeyboardButton("📝 Только пост", callback_data="content_text"),
    )
    kb.add(types.InlineKeyboardButton("❌ Закрыть", callback_data="content_close"))
    return kb

def preview_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Опубликовать", callback_data="content_publish"),
        types.InlineKeyboardButton("🔄 Переделать", callback_data="content_regenerate"),
    )
    kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="content_cancel"))
    return kb

def register_content_handlers(dp, bot, get_main_menu, catalog_text_provider, logger):
    async def show_content(msg):
        if not is_owner(msg.from_user.id):
            await msg.answer("⛔ Раздел доступен только владельцу.")
            return
        await msg.answer(
            "⚓ <b>Контент-центр КРАБА МОРЕ</b>\n\n"
            "Здесь Шкипер готовит посты и рекламные изображения "
            "для @krabamoreblg. Сначала будет предпросмотр, "
            "а публикация произойдёт только после твоего подтверждения.",
            reply_markup=content_menu()
        )

    async def create(msg, prompt, with_image, state):
        await msg.answer("⚓ Шкипер готовит контент…")
        try:
            post, image = await generate_content(
                prompt,
                catalog_text_provider(),
                with_image=with_image
            )
            image_b64 = base64.b64encode(image).decode("ascii") if image else None
            await state.update_data(
                content_prompt=prompt,
                content_post=post,
                content_image=image_b64,
                content_mode="image" if with_image else "text"
            )
            if image:
                await msg.answer_photo(
                    types.InputFile(BytesIO(image), filename="krabamore_ai.jpg"),
                    caption=post,
                    reply_markup=preview_menu()
                )
            else:
                await msg.answer(post, reply_markup=preview_menu())
        except Exception as exc:
            logger.exception("AI content error")
            await msg.answer(
                "⚠️ <b>Не удалось подготовить контент.</b>\n\n"
                f"<code>{str(exc)}</code>\n\n"
                "Проверь OPENAI_API_KEY в Render."
            )

    @dp.message_handler(commands=["content"])
    async def content_command(msg: types.Message):
        await show_content(msg)

    @dp.callback_query_handler(lambda c: c.data.startswith("content_"))
    async def content_callback(call: types.CallbackQuery, state: FSMContext):
        if not is_owner(call.from_user.id):
            await bot.answer_callback_query(call.id, "⛔ Нет доступа")
            return

        action = call.data
        await bot.answer_callback_query(call.id)

        if action in ("content_close", "content_cancel"):
            await state.finish()
            await call.message.answer(
                "⚓ Контент-центр закрыт.",
                reply_markup=get_main_menu(call.from_user.id)
            )
            return

        if action == "content_new":
            await state.update_data(content_mode="image")
            await state.set_state(ContentStates.waiting_prompt.state)
            await call.message.answer(
                "🎨 <b>Пост + картинка</b>\n\n"
                "Напиши задачу. Например:\n"
                "Камчатский краб L2, 3990 ₽. Сделай красивый пост без агрессивных продаж."
            )
            return

        if action == "content_text":
            await state.update_data(content_mode="text")
            await state.set_state(ContentStates.waiting_prompt.state)
            await call.message.answer(
                "📝 <b>Только пост</b>\n\n"
                "Напиши товар, тему, цену или акцию."
            )
            return

        if action == "content_publish":
            data = await state.get_data()
            post = data.get("content_post")
            image_b64 = data.get("content_image")
            if not post:
                await call.message.answer("⚠️ Предпросмотр не найден. Создай пост заново.")
                return
            try:
                if image_b64:
                    sent = await bot.send_photo(
                        CHANNEL_USERNAME,
                        types.InputFile(
                            BytesIO(base64.b64decode(image_b64)),
                            filename="krabamore_post.jpg"
                        ),
                        caption=post
                    )
                else:
                    sent = await bot.send_message(CHANNEL_USERNAME, post)
                await state.finish()
                await call.message.answer(
                    "✅ <b>Опубликовано в канале.</b>\n\n"
                    f'<a href="{CHANNEL_URL}">@krabamoreblg</a>',
                    reply_markup=get_main_menu(call.from_user.id)
                )
                logger.info(
                    "Published content to %s message_id=%s",
                    CHANNEL_USERNAME,
                    getattr(sent, "message_id", None)
                )
            except Exception as exc:
                logger.exception("Telegram channel publish error")
                await call.message.answer(
                    "❌ Не удалось опубликовать. Проверь, что бот — администратор канала "
                    "с правом публикации сообщений и фотографий.\n\n"
                    f"<code>{str(exc)}</code>"
                )
            return

        if action == "content_regenerate":
            data = await state.get_data()
            prompt = data.get("content_prompt")
            mode = data.get("content_mode", "image")
            if not prompt:
                await call.message.answer("⚠️ Исходная задача не найдена.")
                return
            # Не завершаем FSM до генерации: create() сохраняет предпросмотр в state.
            await create(call.message, prompt, mode == "image", state)
            return

    @dp.message_handler(
        state=ContentStates.waiting_prompt,
        content_types=types.ContentTypes.TEXT
    )
    async def content_prompt(msg: types.Message, state: FSMContext):
        if not is_owner(msg.from_user.id):
            await state.finish()
            await msg.answer("⛔ Раздел доступен только владельцу.")
            return
        prompt = (msg.text or "").strip()
        if len(prompt) < 3:
            await msg.answer("Напиши подробнее, что нужно продвигать.")
            return
        data = await state.get_data()
        mode = data.get("content_mode", "image")
        await state.finish()
        await create(msg, prompt, mode == "image", state)

    return show_content
