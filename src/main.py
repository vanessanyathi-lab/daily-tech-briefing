from __future__ import annotations

import os
from datetime import datetime, timezone

from src.config import ROOT_DIR, Settings, load_settings
from src.emailer import BriefingItem, render_briefing, send_email
from src.feeds import Article, fetch_articles, load_feed_sources
from src.summarizer import configure_gemini, summarize_article


MAX_TOTAL_ARTICLES = int(os.getenv("MAX_TOTAL_ARTICLES", "10"))


AUTOMATION_KEYWORDS = [
    "automation",
    "automate",
    "automated",
    "workflow",
    "ci/cd",
    "devops",
    "infrastructure as code",
    "iac",
    "ansible",
    "terraform",
    "github actions",
    "jenkins",
    "orchestration",
    "sre",
    "platform engineering",
    "cloud automation",
    "ai agent",
    "agentic ai",
    "networking",
    "network automation",
    "router automation",
    "zero touch provisioning",
    "automatic provisioning",

]


def automation_score(article: Article) -> int:
    text = f"{article.title} {article.source} {article.raw_summary}".lower()

    score = 0

    for keyword in AUTOMATION_KEYWORDS:
        if keyword.lower() in text:
            score += 1

    return score


def build_briefing(settings: Settings) -> str:
    configure_gemini(settings.gemini_api_key)

    sources = load_feed_sources(ROOT_DIR / "feeds.yaml")

    articles_by_category = fetch_articles(
        sources,
        lookback_hours=settings.article_lookback_hours,
        max_per_category=settings.max_articles_per_category,
    )

    all_articles: list[tuple[str, Article]] = []

    for category, articles in articles_by_category.items():
        for article in articles:
            all_articles.append((category, article))

    # Sort articles so automation-related ones appear first.
    all_articles.sort(
        key=lambda item: automation_score(item[1]),
        reverse=True,
    )

    selected_articles = all_articles[:MAX_TOTAL_ARTICLES]

    items_by_category: dict[str, list[BriefingItem]] = {}

    for category, article in selected_articles:
        if category not in items_by_category:
            items_by_category[category] = []

        items_by_category[category].append(
            BriefingItem(
                article=article,
                summary=summarize_article(
                    article,
                    model_name=settings.gemini_model,
                ),
            )
        )

    return render_briefing(
        items_by_category,
        generated_at=datetime.now(timezone.utc),
    )


def main() -> None:
    settings = load_settings()

    html_body = build_briefing(settings)

    subject = f"Daily Tech Briefing - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    send_email(settings, subject, html_body)


if __name__ == "__main__":
    main()