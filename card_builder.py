from .llm import ask_llm

SYSTEM_CARD = """Ты — эксперт по маркетплейсам (Wildberries, Ozon, Яндекс Маркет).
Твоя задача — создавать продающие карточки товаров.
Отвечай строго в формате ниже, используй только русский язык.

=== КАРТОЧКА ТОВАРА ===

📦 НАЗВАНИЕ
[краткое, ёмкое название для листинга, до 100 символов]

📝 ОПИСАНИЕ
[продающее описание 150–300 слов]

💎 УНИКАЛЬНОЕ ТОРГОВОЕ ПРЕДЛОЖЕНИЕ (УТП)
[1–2 предложения, главное отличие от конкурентов]

✅ ПРЕИМУЩЕСТВА
• [преимущество 1]
• [преимущество 2]
• [преимущество 3]
• [преимущество 4]
• [преимущество 5]

🔍 SEO-КЛЮЧИ
[15–20 ключевых фраз через запятую]

🖼 ТЕКСТЫ ДЛЯ СЛАЙДОВ
Слайд 1 (главный): [заголовок] / [подзаголовок]
Слайд 2 (боль): [проблема покупателя]
Слайд 3 (решение): [как товар решает проблему]
Слайд 4 (преимущества): [3 буллита]
Слайд 5 (призыв): [CTA]

📸 РЕКОМЕНДАЦИИ ПО ФОТО
• [рекомендация 1]
• [рекомендация 2]
• [рекомендация 3]
• [рекомендация 4]

=== КОНЕЦ КАРТОЧКИ ==="""


async def check_enough_info(description: str, qa_pairs: list) -> bool:
    # Если уже есть хоть один ответ — считаем достаточно
    if len(qa_pairs) >= 1:
        return True
    # Если описание длиннее 30 символов — достаточно
    if len(description.replace("[Фото товара].", "").strip()) > 30:
        return True
    return False


async def get_clarify_question(description: str, qa_pairs: list) -> str:
    from .llm import ask_llm
    already_asked = [qa["q"] for qa in qa_pairs]
    already_str = ""
    if already_asked:
        already_str = "\nУже заданные вопросы (НЕ повторяй их):\n" + "\n".join(f"- {q}" for q in already_asked)

    system = """Ты — помощник по созданию карточек товаров для маркетплейсов.
Задай РОВНО ОДИН короткий вопрос о товаре. Вопрос должен быть конкретным.
Не повторяй уже заданные вопросы. Не объясняй — просто задай вопрос."""

    user = f"Описание товара: {description}{already_str}"
    question = await ask_llm(system, user)
    return question.strip()


async def generate_card(description: str, qa_pairs: list) -> str:
    context = _build_context(description, qa_pairs)
    card = await ask_llm(
        SYSTEM_CARD,
        f"Создай карточку товара на основе информации:\n\n{context}"
    )
    return card.strip()


def _build_context(description: str, qa_pairs: list) -> str:
    parts = [f"Описание товара: {description}"] if description else ["Описание товара: не предоставлено"]
    for i, qa in enumerate(qa_pairs, 1):
        parts.append(f"Вопрос {i}: {qa['q']}")
        parts.append(f"Ответ {i}: {qa['a']}")
    return "\n".join(parts)