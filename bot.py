import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Render автоматически предоставит этот адрес, формат: https://med-bot-service.onrender.com
BASE_WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "https://med-bot-service.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret-token"  # Опционально, можно оставить как есть

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ВАШИ ДАННЫЕ О ПРЕПАРАТАХ (DRUGS) ==========
# ... (вставьте сюда ваш полный словарь DRUGS без изменений, я его пропускаю для краткости) ...

# ========== КЛАВИАТУРЫ (без изменений) ==========
# ... (вставьте сюда ваши функции main_menu, form_menu, drug_menu) ...

# ========== ОБРАБОТЧИКИ (без изменений) ==========
# ... (вставьте сюда ваши cmd_start, handle_symptom, handle_form, handle_drug, back_to_main, ignore_button) ...

# ========== НАСТРОЙКА WEBHOOK ==========
async def on_startup(bot: Bot):
    # При запуске сообщаем Telegram, куда отправлять сообщения
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)
    logging.info(f"Webhook установлен на {BASE_WEBHOOK_URL}{WEBHOOK_PATH}")

async def on_shutdown(bot: Bot):
    # При остановке удаляем webhook
    await bot.delete_webhook()
    logging.info("Webhook удален")

def main():
    app = web.Application()
    
    # Регистрируем обработчик webhook
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настраиваем события запуска/остановки
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Запускаем веб-сервер (Render передаст порт через переменную PORT)
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
