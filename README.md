# Serverless AI Tech News Briefing

This repository contains a Python ETL pipeline that collects daily technology news from RSS feeds, summarises each article with the Google Gemini API, renders a categorised HTML briefing, and emails it every morning using GitHub Actions.

The scheduled workflow runs at `07:00 UTC`, which is `09:00` in Zimbabwe time (`Africa/Harare`, UTC+2).

## What It Covers

- AI
- Cybersecurity
- Cloud computing
- Software engineering
- Startups
- Networking
- Fintech
- Data science

## How It Works

1. Extract RSS items from `feeds.yaml`.
2. Filter and deduplicate recent articles.
3. Summarise each article into exactly two sentences using Gemini.
4. Render a categorised HTML email briefing.
5. Send the briefing through SMTP.
6. Run automatically with GitHub Actions every day at 9:00 AM Zimbabwe time.

## Local Setup

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements-dev.txt
```

Set environment variables before running locally:

```powershell
$env:GEMINI_API_KEY="your-gemini-api-key"
$env:EMAIL_SENDER="you@example.com"
$env:EMAIL_PASSWORD="your-email-app-password"
$env:EMAIL_RECIPIENT="you@example.com"
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
python -m src.main
```

For Gmail, use an app password instead of your account password.

## GitHub Secrets

Create these repository secrets in GitHub under **Settings > Secrets and variables > Actions**:

| Secret | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Google Gemini API key used for article summaries |
| `EMAIL_SENDER` | Sender email address |
| `EMAIL_PASSWORD` | SMTP password or app password |
| `EMAIL_RECIPIENT` | Inbox that receives the briefing |
| `SMTP_HOST` | Optional SMTP host, defaults to Gmail in code |
| `SMTP_PORT` | Optional SMTP port, defaults to `587` in code |
| `GEMINI_MODEL` | Optional Gemini model override, defaults to `gemini-1.5-flash` |

## Running Tests

```powershell
pip install -r requirements-dev.txt
pytest
```

## Customising Feeds

Edit `feeds.yaml` to add, remove, or rename feeds. Each category contains a list of RSS sources:

```yaml
ai:
  - name: Example AI Feed
    url: https://example.com/rss
```

## Manual Run

The workflow includes `workflow_dispatch`, so you can run it manually from the GitHub Actions tab after adding your secrets.
