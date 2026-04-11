import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from chyllonge.api import ChallongeApi

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHALLONGE_USER = os.getenv("CHALLONGE_USER")
CHALLONGE_KEY = os.getenv("CHALLONGE_KEY")

api = ChallongeApi()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_ttext = []


def create_button():
    buttons = [[InlineKeyboardButton(text="Создать турнир", callback_data="create_tournament")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(Command("create_tournament"))
async def create_tournament(msg: types.Message):
    await msg.answer("Создание турнира", reply_markup=create_button())


@dp.callback_query(F.data == "create_tournament")
async def on_create(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    users_ttext.append(user_id)

    await callback.message.edit_text("Введите название турнира")


@dp.message()
async def handle_text(msg: types.Message):
    user_id = msg.from_user.id

    if user_id in users_ttext:
        tournament_name = msg.text

        if len(tournament_name) > 60:
            await msg.answer("Название слишком длинное (максимум 60 символов)")
            return

        tournament = api.tournaments.create(
            name=tournament_name,
            tournament_type="single elimination"
        )

        await msg.answer(f"Турнир [{tournament_name}]({tournament['full_challonge_url']}) успешно создан")

        del users_ttext[users_ttext.index(user_id)]


@dp.message(Command("tournaments"))
async def tournaments(msg: types.Message):
    tournaments_data = api.tournaments.get_all()
    for tournament in tournaments_data:
        state = tournament['state']
        status = None
        if state == "pending":
            status = "⏳Ожидает запуска"
        elif state == "underway":
            status = "🔄В процессе"
        elif state == "complete":
            status = "🏁Завершён"
        await msg.answer(f"[{tournament['name']}]({tournament['full_challonge_url']})\n"
                         f"Статус - {status}\n",
                         parse_mode="Markdown")


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
