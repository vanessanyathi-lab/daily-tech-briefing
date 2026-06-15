from __future__ import annotations

import time

from google.api_core.exceptions import ResourceExhausted
from src.feeds import Article


PROMPT = """Summarise this technology news article in exactly two clear sentences.
Keep the tone concise, factual, and useful for an executive daily briefing.

Title: {title}
Source: {source}
Existing excerpt: {excerpt}
URL: {url}
"""


# This prevents the programme from repeatedly calling Gemini after daily quota is finished.
GEMINI_QUOTA_EXHAUSTED = False


def configure_gemini(api_key: str) -> None:
    import google.generativeai as genai

    genai.configure(api_key=api_key)


def summarize_article(article: Article, model_name: str = "gemini-2.5-flash-lite") -> str:
    global GEMINI_QUOTA_EXHAUSTED

    import google.generativeai as genai

    # If quota is already exhausted, do not keep calling Gemini.
    if GEMINI_QUOTA_EXHAUSTED:
        return _fallback_summary(article)

    model = genai.GenerativeModel(model_name)

    try:
        # Keep requests slower to avoid per-minute limits.
        time.sleep(8)

        response = model.generate_content(
            PROMPT.format(
                title=article.title,
                source=article.source,
                excerpt=article.raw_summary[:2000],
                url=article.link,
            ),
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 120,
            },
        )

        text = (response.text or "").strip()
        return _limit_to_two_sentences(text) or _fallback_summary(article)

    except ResourceExhausted as error:
        error_text = str(error)

        print(f"Gemini quota reached while summarising: {article.title}")

        # Daily quota means there is no point retrying today.
        if "GenerateRequestsPerDay" in error_text or "PerDay" in error_text:
            print("Daily Gemini quota exhausted. Using fallback summaries for the remaining articles.")
            GEMINI_QUOTA_EXHAUSTED = True
            return _fallback_summary(article)

        # Per-minute quota can be retried after waiting.
        print("Gemini minute limit reached. Waiting 60 seconds before retrying...")
        time.sleep(60)

        try:
            response = model.generate_content(
                PROMPT.format(
                    title=article.title,
                    source=article.source,
                    excerpt=article.raw_summary[:2000],
                    url=article.link,
                ),
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 120,
                },
            )

            text = (response.text or "").strip()
            return _limit_to_two_sentences(text) or _fallback_summary(article)

        except Exception as retry_error:
            print(f"Retry failed for article: {article.title}")
            print(f"Error: {retry_error}")
            return _fallback_summary(article)

    except Exception as error:
        print(f"Could not summarise article: {article.title}")
        print(f"Error: {error}")
        return _fallback_summary(article)


def _fallback_summary(article: Article) -> str:
    """
    Used when Gemini fails or quota is exhausted.
    This keeps the briefing working using the RSS summary/title.
    """
    fallback_text = article.raw_summary or article.title
    return _limit_to_two_sentences(fallback_text) or article.title


def _limit_to_two_sentences(text: str) -> str:
    sentences: list[str] = []
    current: list[str] = []

    for char in text:
        current.append(char)

        if char in ".!?" and len("".join(current).strip()) > 20:
            sentences.append("".join(current).strip())
            current = []

            if len(sentences) == 2:
                break

    if not sentences and text:
        return text.strip()

    return " ".join(sentences).strip()