from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.db import upsert_user
from bot.keyboards import main_menu
from bot.utils.states import ProductFlow

router = Router()

HELP_TEXT = """
🤖 <b>Бот для создания карточек товаров</b>

Я помогу создать продающую карточку для маркетплейса (WB, Ozon, Яндекс Маркет).

<b>Что я умею:</b>
• Принять фото товара или текстовое описание
• Задать уточняющие вопросы (не более 3)
• Сгенерировать полную карточку:
  — Название и описание
  — УТП и преимущества
  — SEO-ключи
  — Тексты для слайдов
  — Рекомендации по фото

<b>Как начать:</b>
Нажмите «📦 Новая карточка» или просто отправьте фото/описание товара.
"""


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    await message.answer(
        f"Привет, <b>{message.from_user.first_name}</b>! 👋\n\n{HELP_TEXT}",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
    await state.set_state(ProductFlow.waiting_for_product)


@router.message(Command("help"))
@router.message(lambda m: m.text == "ℹ️ Помощь")
async def cmd_help(message: Message, state: FSMContext) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=main_menu())
    await state.set_state(ProductFlow.waiting_for_product)


@router.message(lambda m: m.text == "📦 Новая карточка")
async def new_card(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ProductFlow.waiting_for_product)
    await message.answer(
        "📸 Отправьте фото товара или напишите его описание.\n"
        "Чем подробнее — тем лучше получится карточка!",
        reply_markup=main_menu(),
    )