import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot.db")
MAX_CLARIFY_QUESTIONS: int = 3

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")