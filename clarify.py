from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.utils.states import ProductFlow

# Этот роутер теперь не нужен — логика переехала в product.py
# Оставляем пустым чтобы неломать импорты в __init__.py
router = Router()