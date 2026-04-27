import httpx
from config import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    COHERE_API_KEY,
    MISTRAL_API_KEY,
)


async def ask_llm(system: str, user: str) -> str:
    if LLM_PROVIDER == "anthropic":
        return await _ask_anthropic(system, user)
    if LLM_PROVIDER == "openai":
        return await _ask_openai(system, user)
    if LLM_PROVIDER == "gemini":
        return await _ask_gemini(system, user)
    if LLM_PROVIDER == "groq":
        return await _ask_groq(system, user)
    if LLM_PROVIDER == "cohere":
        return await _ask_cohere(system, user)
    if LLM_PROVIDER == "mistral":
        return await _ask_mistral(system, user)
    raise ValueError(f"Неизвестный LLM_PROVIDER: {LLM_PROVIDER}")


async def _ask_anthropic(system: str, user: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY не задан")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 4096,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


async def _ask_openai(system: str, user: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY не задан")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "max_tokens": 4096,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def _ask_gemini(system: str, user: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не задан")
    prompt = f"{system}\n\n{user}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ],
                "generationConfig": {
                    "maxOutputTokens": 4096,
                    "temperature": 0.7,
                },
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def _ask_groq(system: str, user: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY не задан")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 4096,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def _ask_cohere(system: str, user: str) -> str:
    if not COHERE_API_KEY:
        raise ValueError("COHERE_API_KEY не задан")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.cohere.com/v2/chat",
            headers={
                "Authorization": f"Bearer {COHERE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "command-r-plus",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 4096,
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"][0]["text"]


async def _ask_mistral(system: str, user: str) -> str:
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY не задан")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistral-large-latest",
                "max_tokens": 4096,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]