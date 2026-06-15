from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import logging
from typing import Any
import html
import re
import urllib.request
import xml.etree.ElementTree as ET


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeedSource:
    category: str
    name: str
    url: str


@dataclass(frozen=True)
class Article:
    category: str
    source: str
    title: str
    link: str
    published_at: datetime | None
    raw_summary: str


def load_feed_sources(path: Path) -> list[FeedSource]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("Install PyYAML or keep feeds.yaml simple enough for the built-in parser.") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    sources: list[FeedSource] = []
    for category, feeds in data.items():
        for feed in feeds or []:
            sources.append(FeedSource(category=category, name=feed["name"], url=feed["url"]))
    return sources


def fetch_articles(sources: list[FeedSource], lookback_hours: int, max_per_category: int) -> dict[str, list[Article]]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    grouped: dict[str, list[Article]] = {}

    for source in sources:
        try:
            source_articles = _fetch_source(source)
        except Exception as exc:
            logger.warning("Skipping feed %s (%s): %s", source.name, source.url, exc)
            continue

        for article in source_articles:
            if article.published_at and article.published_at < cutoff:
                continue
            category_articles = grouped.setdefault(source.category, [])
            if _is_duplicate(article, category_articles):
                continue
            category_articles.append(article)

    for category, articles in grouped.items():
        articles.sort(key=lambda item: item.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        grouped[category] = articles[:max_per_category]

    return grouped


def _fetch_source(source: FeedSource) -> list[Article]:
    try:
        import feedparser

        parsed = feedparser.parse(source.url)
        return [_article_from_feedparser_entry(source, entry) for entry in parsed.entries]
    except Exception:
        return _fetch_source_with_stdlib(source)


def _article_from_feedparser_entry(source: FeedSource, entry: Any) -> Article:
    published = None
    published_value = entry.get("published") or entry.get("updated")
    if published_value:
        try:
            published = parsedate_to_datetime(published_value)
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            published = None

    return Article(
        category=source.category,
        source=source.name,
        title=html.unescape(entry.get("title", "Untitled")),
        link=entry.get("link", source.url),
        published_at=published,
        raw_summary=_clean_html(entry.get("summary", "")),
    )


def _fetch_source_with_stdlib(source: FeedSource) -> list[Article]:
    request = urllib.request.Request(source.url, headers={"User-Agent": "daily-tech-briefing/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())

    articles: list[Article] = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or "Untitled"
        link = item.findtext("link") or source.url
        published = item.findtext("pubDate")
        summary = item.findtext("description") or ""
        published_at = None
        if published:
            try:
                published_at = parsedate_to_datetime(published)
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
            except ValueError:
                published_at = None
        articles.append(
            Article(
                category=source.category,
                source=source.name,
                title=html.unescape(title),
                link=link,
                published_at=published_at,
                raw_summary=_clean_html(summary),
            )
        )
    return articles


def _clean_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def _is_duplicate(article: Article, articles: list[Article]) -> bool:
    normalized_title = article.title.casefold().strip()
    return any(existing.link == article.link or existing.title.casefold().strip() == normalized_title for existing in articles)
