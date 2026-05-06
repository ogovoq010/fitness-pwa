import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
MINI_APP_URL = os.environ["MINI_APP_URL"]  # GitHub Pages URL, напр. https://user.github.io/fitness-pwa/

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def _app_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏋️ Відкрити FitTrack", web_app=WebAppInfo(url=MINI_APP_URL))]],
        resize_keyboard=True,
        is_persistent=True,
    )

def _inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏋️ Відкрити FitTrack", web_app=WebAppInfo(url=MINI_APP_URL))
    ]])


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    name = message.from_user.first_name or "Спортсмен"
    await message.answer(
        f"👋 Привіт, *{name}*\\!\n\n"
        f"Я *FitTrack* — твій персональний трекер тренувань і харчування\\.\n\n"
        f"Що вмію:\n"
        f"💪 Відстежувати тренування щодня\n"
        f"🥗 Трекер калорій і макронутрієнтів\n"
        f"📊 Статистика і графіки прогресу\n"
        f"⏱ Таймер відпочинку між підходами\n"
        f"🔔 Нагадування про тренування\n\n"
        f"Підходить для будь\\-якого виду активності:\n"
        f"🧘 Йога · 🤸 Пілатес · 🔥 Кросфіт · 🥋 Єдиноборства\n"
        f"💃 Танці · 🏊 Плавання · 🥊 Бокс · 🏃 Біг\n\n"
        f"Тисни кнопку нижче, щоб відкрити додаток\\!",
        parse_mode="MarkdownV2",
        reply_markup=_app_keyboard(),
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ *Допомога FitTrack*\n\n"
        "*/start* — запустити бота\n"
        "*/app* — відкрити додаток\n"
        "*/help* — ця довідка\n\n"
        "Всі функції доступні прямо в додатку\\.",
        parse_mode="MarkdownV2",
        reply_markup=_app_keyboard(),
    )


@dp.message(Command("app"))
async def cmd_app(message: types.Message):
    await message.answer(
        "Відкрий свій трекер 👇",
        reply_markup=_inline_keyboard(),
    )


@dp.message(F.web_app_data)
async def web_app_data(message: types.Message):
    # Mini App може надсилати дані при закритті (опціонально)
    log.info("WebApp data from %s: %s", message.from_user.id, message.web_app_data.data)
    await message.answer("✅ Дані синхронізовано!")


async def main():
    log.info("Starting FitTrack bot...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
