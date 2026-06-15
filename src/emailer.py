from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html
import smtplib

from src.config import Settings
from src.feeds import Article


@dataclass(frozen=True)
class BriefingItem:
    article: Article
    summary: str


def render_briefing(items_by_category: dict[str, list[BriefingItem]], generated_at: datetime) -> str:
    sections = []
    for category, items in items_by_category.items():
        if not items:
            continue
        section_items = "\n".join(_render_item(item) for item in items)
        sections.append(
            f"""
            <section>
              <h2>{_format_category(category)}</h2>
              {section_items}
            </section>
            """
        )

    body = "\n".join(sections) or "<p>No fresh articles were found for today's briefing.</p>"
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Daily Tech Briefing</title>
    <style>
      body {{ margin: 0; background: #f6f8fb; color: #1f2937; font-family: Arial, sans-serif; }}
      .container {{ max-width: 760px; margin: 0 auto; padding: 28px 18px; }}
      .header {{ border-bottom: 3px solid #2563eb; padding-bottom: 14px; margin-bottom: 22px; }}
      h1 {{ font-size: 28px; margin: 0 0 6px; }}
      h2 {{ font-size: 19px; margin: 28px 0 12px; color: #111827; text-transform: capitalize; }}
      article {{ background: #ffffff; border: 1px solid #dbe2ea; border-radius: 6px; padding: 16px; margin-bottom: 12px; }}
      h3 {{ font-size: 16px; margin: 0 0 8px; }}
      p {{ line-height: 1.55; }}
      a {{ color: #1d4ed8; text-decoration: none; }}
      .meta {{ color: #6b7280; font-size: 13px; margin-bottom: 8px; }}
      .footer {{ color: #6b7280; font-size: 12px; margin-top: 28px; }}
    </style>
  </head>
  <body>
    <main class="container">
      <div class="header">
        <h1>Daily Tech Briefing</h1>
        <p>Generated {html.escape(generated_at.strftime("%Y-%m-%d %H:%M UTC"))}</p>
      </div>
      {body}
      <p class="footer">Automated by the serverless AI tech briefing pipeline.</p>
    </main>
  </body>
</html>"""


def send_email(settings: Settings, subject: str, html_body: str) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.email_sender
    message["To"] = settings.email_recipient
    message.attach(MIMEText("Your email client does not support HTML briefings.", "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.email_sender, settings.email_password)
        server.sendmail(settings.email_sender, [settings.email_recipient], message.as_string())


def _render_item(item: BriefingItem) -> str:
    article = item.article
    published = article.published_at.strftime("%Y-%m-%d %H:%M UTC") if article.published_at else "Date unavailable"
    return f"""
    <article>
      <h3><a href="{html.escape(article.link)}">{html.escape(article.title)}</a></h3>
      <div class="meta">{html.escape(article.source)} | {html.escape(published)}</div>
      <p>{html.escape(item.summary)}</p>
    </article>
    """


def _format_category(category: str) -> str:
    return category.replace("_", " ")
