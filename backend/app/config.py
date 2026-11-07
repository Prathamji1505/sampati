from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')


@dataclass(frozen=True)
class Settings:
    database_url: str = os.environ.get('DATABASE_URL', '')
    preview_secret: str = os.environ.get('PREVIEW_SECRET', '')
    freshness_hours: int = int(os.environ.get('FRESHNESS_HOURS', '24'))
    session_cookie_secure: bool = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    session_hours: int = 12


settings = Settings()
