from __future__ import annotations

from datetime import datetime, timezone

from src.emailer import BriefingItem, render_briefing
from src.feeds import Article


def test_render_briefing_includes_category_article_and_summary() -> None:
    article = Article(
        category="ai",
        source="Example Feed",
        title="Gemini improves summarisation",
        link="https://example.com/article",
        published_at=datetime(2026, 6, 3, 7, 0, tzinfo=timezone.utc),
        raw_summary="Raw text",
    )

    html = render_briefing(
        {"ai": [BriefingItem(article=article, summary="A useful two sentence summary. It is concise.")]},
        generated_at=datetime(2026, 6, 3, 7, 5, tzinfo=timezone.utc),
    )

    assert "Daily Tech Briefing" in html
    assert "Gemini improves summarisation" in html
    assert "A useful two sentence summary. It is concise." in html
    assert "Example Feed" in html
