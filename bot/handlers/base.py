from aiogram import Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я DotSound — музыка прямо в Telegram.\n"
        "Используй /help чтобы узнать что я умею."
    )


@router.message(F.text)
async def echo(message: Message) -> None:
    await message.answer(message.text or "")


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)
