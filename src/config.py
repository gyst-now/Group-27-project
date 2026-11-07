import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()
YEAR = '2026-27'
URLS = (
    'https://catalog.illinois.edu/courses-of-instruction/cs/',
    'https://catalog.illinois.edu/courses-of-instruction/math/',
    'https://catalog.illinois.edu/undergraduate/engineering/computer-science-bs/',
)

@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    openai_key: str
    model: str

    @classmethod
    def load(cls):
        values = [os.getenv('SUPABASE_URL', '').strip(),
                  (os.getenv('SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')).strip(),
                  os.getenv('OPENAI_API_KEY', '').strip()]
        if not all(values):
            raise RuntimeError('Configure server-side Supabase and OpenAI environment variables.')
        return cls(*values, os.getenv('OPENAI_CHAT_MODEL', 'gpt-4.1-mini'))
