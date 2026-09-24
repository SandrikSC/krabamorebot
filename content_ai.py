import os
import base64
import asyncio

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.6-luna")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")

def _client():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не задан в Render")
    if OpenAI is None:
        raise RuntimeError("Пакет openai не установлен")
    return OpenAI(api_key=OPENAI_API_KEY)

def generate_post(user_prompt, catalog_text):
    client = _client()
    system = (
        "Ты редактор Telegram-канала магазина КРАБА МОРЕ. "
        "Пиши живо, аппетитно и современно. Без дешевого кликбейта. "
        "Не выдумывай цены, наличие, характеристики или акции. "
        "Используй HTML Telegram. Максимум 900 символов. "
        "В конце добавь мягкий призыв заказать и ссылку https://t.me/krabamoreblg."
    )
    response = client.responses.create(
        model=OPENAI_TEXT_MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": "Задача владельца: " + user_prompt + "\n\nКаталог:\n" + catalog_text},
        ],
    )
    return response.output_text.strip()

def generate_image(user_prompt, post_text):
    client = _client()
    prompt = (
        "Премиальная фотореалистичная рекламная food-фотография для магазина "
        "морепродуктов КРАБА МОРЕ. Натуральный продукт, аппетитная ресторанная "
        "подача, морская эстетика, дорогая коммерческая фотография, чистая композиция. "
        "Без текста и логотипов на изображении. Не добавляй товары, которых нет в задаче. "
        "Задача: " + user_prompt + ". Пост: " + post_text
    )
    result = client.images.generate(
        model=OPENAI_IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024",
    )
    b64 = getattr(result.data[0], "b64_json", None)
    if not b64:
        raise RuntimeError("OpenAI не вернул изображение")
    return base64.b64decode(b64)

async def generate_content(user_prompt, catalog_text, with_image=True):
    post = await asyncio.to_thread(generate_post, user_prompt, catalog_text)
    image = None
    if with_image:
        image = await asyncio.to_thread(generate_image, user_prompt, post)
    return post, image
