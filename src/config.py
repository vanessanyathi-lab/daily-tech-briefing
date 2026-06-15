from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    email_sender: str
    email_password: str
    email_recipient: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    gemini_model: str = "gemini-1.5-flash"
    max_articles_per_category: int = 5
    article_lookback_hours: int = 36


def load_settings() -> Settings:
    required = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "EMAIL_SENDER": os.getenv("EMAIL_SENDER"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "EMAIL_RECIPIENT": os.getenv("EMAIL_RECIPIENT"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return Settings(
        gemini_api_key=required["GEMINI_API_KEY"] or "",
        email_sender=required["EMAIL_SENDER"] or "",
        email_password=required["EMAIL_PASSWORD"] or "",
        email_recipient=required["EMAIL_RECIPIENT"] or "",
        smtp_host=os.getenv("SMTP_HOST") or "smtp.gmail.com",
        smtp_port=int(os.getenv("SMTP_PORT") or "587"),
        gemini_model=os.getenv("GEMINI_MODEL") or "gemini-1.5-flash",
        max_articles_per_category=int(os.getenv("MAX_ARTICLES_PER_CATEGORY") or "5"),
        article_lookback_hours=int(os.getenv("ARTICLE_LOOKBACK_HOURS") or "36"),
    )
