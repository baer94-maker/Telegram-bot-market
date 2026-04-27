from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.db import create_session, update_session, get_session
from bot.keyboards import skip_keyboard, new_card_keyboard, remove_keyboard
from bot.services import get_clarify_question, generate_card, generate_slide_image
from bot.services.image_gen import download_photo
from bot.utils.states import ProductFlow
from config import MAX_CLARIFY_QUESTIONS, BOT_TOKEN

router = Router()


async def _get_photo_description(message: Message) -> tuple:
    if message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption or ""
        description = f"[Фото товара]. {caption}".strip()
        return description, file_id
    return message.text or "", ""


async def _ask_or_generate(
    message: Message,
    state: FSMContext,
    session_id: int,
    description: str,
    qa_pairs: list,
    clarify_count: int,
) -> None:
    if clarify_count < MAX_CLARIFY_QUESTIONS:
        question = await get_clarify_question(description, qa_pairs)
        new_count = clarify_count + 1
        update_session(session_id, clarify_count=new_count)
        await state.update_data(
            clarify_count=new_count,
            pending_question=question,
        )
        await state.set_state(ProductFlow.waiting_for_clarify)
        await message.answer(f"❓ {question}", reply_markup=skip_keyboard())
        return

    await _do_generate(message, state, session_id, description, qa_pairs)


async def _do_generate(
    message: Message,
    state: FSMContext,
    session_id: int,
    description: str,
    qa_pairs: list,
) -> None:
    await state.set_state(ProductFlow.generating)
    wait_msg = await message.answer(
        "⏳ Генерирую карточку и слайд, подождите ~30 секунд…",
        reply_markup=remove_keyboard,
    )
    try:
        # 1. Текст карточки
        card = await generate_card(description, qa_pairs)
        update_session(session_id, card_result=card)

        # 2. Скачиваем фото пользователя если было
        photo_bytes = None
        session = get_session(session_id)
        if session and session.get("photo_file_id"):
            photo_bytes = await download_photo(BOT_TOKEN, session["photo_file_id"])

        # 3. Генерируем слайд
        image_bytes = generate_slide_image(card, photo_bytes)
        slide = BufferedInputFile(image_bytes, filename="card_slide.png")

        await wait_msg.delete()

        # 4. Отправляем слайд
        if photo_bytes:
            caption = "🖼 Слайд-черновик • использовано ваше фото товара"
        else:
            caption = "🖼 Слайд-черновик • фото не было, использован тёмный фон"

        await message.answer_photo(photo=slide, caption=caption)

        # 5. Полный текст карточки
        await message.answer(card, reply_markup=new_card_keyboard())
        await message.answer(
            "✅ Готово! Нажмите «📦 Новая карточка» для следующего товара.",
            reply_markup=new_card_keyboard(),
        )

    except Exception as e:
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer(
            f"❌ Ошибка: {e}\n\nПопробуйте ещё раз.",
            reply_markup=new_card_keyboard(),
        )
    finally:
        await state.clear()
        await state.set_state(ProductFlow.waiting_for_product)


@router.message(F.photo | F.text)
async def handle_all(message: Message, state: FSMContext, bot: Bot) -> None:
    text = message.text or ""

    if text.startswith("/"):
        return
    if text in ("📦 Новая карточка", "ℹ️ Помощь"):
        return

    current_state = await state.get_state()

    if current_state == ProductFlow.generating:
        await message.answer("⏳ Ещё генерирую, подождите…")
        return

    if current_state == ProductFlow.waiting_for_clarify:
        data = await state.get_data()
        session_id = data["session_id"]
        description = data["description"]
        qa_pairs = data.get("qa_pairs", [])
        clarify_count = data.get("clarify_count", 0)
        pending_question = data.get("pending_question", "")

        skipped = text == "⏭ Пропустить вопрос"
        answer = "" if skipped else text

        if pending_question:
            qa_pairs = qa_pairs + [{"q": pending_question, "a": answer}]
            update_session(session_id, clarify_qa=qa_pairs)
            await state.update_data(qa_pairs=qa_pairs)

        await _ask_or_generate(
            message, state, session_id, description, qa_pairs, clarify_count
        )
        return

    # Новый товар
    description, file_id = await _get_photo_description(message)
    if not description and not file_id:
        await message.answer("Пожалуйста, отправьте фото или описание товара.")
        return

    session_id = create_session(
        user_id=message.from_user.id,
        description=description,
        photo_file_id=file_id,
    )
    await state.set_data({
        "session_id": session_id,
        "description": description,
        "qa_pairs": [],
        "clarify_count": 0,
    })
    await state.set_state(ProductFlow.waiting_for_product)
    await message.answer(
        "✅ Получил! Сейчас задам пару вопросов.",
        reply_markup=remove_keyboard,
    )
    await _ask_or_generate(message, state, session_id, description, [], 0)