import os
import re
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from fetch import collect_all
from news import get_news

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
TR_OFFSET = timedelta(hours=3)


def _urlname(url):
    path = re.sub(r"https?://[^/]+/", "", url).rstrip("/")
    return path.replace("-", " ").capitalize() if path else url


def _format_lastmod(lastmod):
    if not lastmod:
        return ""
    try:
        dt = datetime.fromisoformat(lastmod)
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return lastmod


def _render_eksiseyler_links(items, color):
    rows = []
    for item in items:
        url = item["url"]
        label = _urlname(url)
        date_str = _format_lastmod(item.get("lastmod"))
        date_span = (
            f'<span style="display:inline-block;margin-left:8px;font-size:11px;color:#aaaaaa;font-weight:700;">'
            f"{date_str}</span>"
            if date_str
            else ""
        )
        rows.append(
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">'
            f'<a href="{url}" style="color:inherit;text-decoration:none;font-size:14px;">{label}</a>'
            f"{date_span}"
            f"</td></tr>"
        )
    return "\n".join(rows)


def _render_links(items, url_key="url", color="inherit"):
    rows = []
    for item in items:
        url = item[url_key] if isinstance(item, dict) else item
        label = item.get("title", _urlname(url)) if isinstance(item, dict) else _urlname(url)
        rows.append(
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">'
            f'<a href="{url}" style="color:{color};text-decoration:none;font-size:14px;">{label}</a>'
            f"</td></tr>"
        )
    return "\n".join(rows)


def _render_new_links(items):
    rows = []
    for item in items:
        url = item["url"]
        label = _urlname(url)
        date_str = _format_lastmod(item.get("lastmod"))
        date_span = (
            f'<span style="display:inline-block;margin-left:8px;font-size:11px;color:#aaaaaa;">'
            f"{date_str}</span>"
            if date_str
            else ""
        )
        rows.append(
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">'
            f'<span style="display:inline-block;background-color:#e8f4fd;color:#0f3460;'
            f'font-size:10px;font-weight:700;padding:2px 6px;border-radius:3px;'
            f'margin-right:8px;text-transform:uppercase;">Yeni</span>'
            f'<a href="{url}" style="color:#0f3460;text-decoration:none;font-size:14px;">{label}</a>'
            f"{date_span}"
            f"</td></tr>"
        )
    return "\n".join(rows)


def _build_new_section(new_links):
    if not new_links:
        return ""
    return f"""
      <tr>
        <td style="padding:20px 32px 0 32px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="border-left:3px solid #0f3460;padding-left:12px;">
                <p style="margin:0;font-size:11px;color:#888888;letter-spacing:1.5px;text-transform:uppercase;">Ekşi Şeyler</p>
                <h2 style="margin:4px 0 0 0;font-size:16px;color:#1a1a2e;">🆕 Yeni Eklenenler</h2>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:12px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            {_render_new_links(new_links)}
          </table>
        </td>
      </tr>
    """


def _render_news_section(items: list[dict]) -> str:
    """Haber listesini HTML satırlarına dönüştürür."""
    rows = []
    seen_titles = set()
    for item in items:
        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        channel = item.get("channel_name", "").strip()
        if not title or not link or title in seen_titles:
            continue
        seen_titles.add(title)
        channel_span = (
            f'<span style="display:inline-block;margin-right:8px;font-size:10px;'
            f'color:#888888;font-weight:700;text-transform:uppercase;">'
            f'{channel}</span>'
            if channel else ""
        )
        rows.append(
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">'
            f'{channel_span}'
            f'<a href="{link}" style="color:inherit;text-decoration:none;font-size:14px;line-height:1.5;">'
            f'{title}</a>'
            f'</td></tr>'
        )
    return "\n".join(rows)


def build_html(data, date_str, news: dict | None = None):
    template = Path("templates/mail.html").read_text(encoding="utf-8")

    eksiseyler_random_rows = _render_eksiseyler_links(data["eksiseyler_random"], color="inherit")
    debe_rows = _render_links(data["debe"], url_key="url")
    evrimagaci_rows = _render_links(data["evrimagaci"])

    gundem_rows = _render_news_section((news or {}).get("Gündem", []))
    teknoloji_rows = _render_news_section((news or {}).get("Teknoloji", []))

    html = template
    html = re.sub(
        r"\{%\s*for item in eksiseyler_random\s*%\}.*?\{%\s*endfor\s*%\}",
        eksiseyler_random_rows,
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"\{%\s*if eksiseyler_new\s*%\}.*?\{%\s*endif\s*%\}",
        "",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"\{%\s*for item in debe\s*%\}.*?\{%\s*endfor\s*%\}",
        debe_rows,
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"\{%\s*for url in evrimagaci\s*%\}.*?\{%\s*endfor\s*%\}",
        evrimagaci_rows,
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"\{%\s*for item in gundem\s*%\}.*?\{%\s*endfor\s*%\}",
        gundem_rows,
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"\{%\s*for item in teknoloji\s*%\}.*?\{%\s*endfor\s*%\}",
        teknoloji_rows,
        html,
        flags=re.DOTALL,
    )
    html = html.replace("{{ date }}", date_str)
    return html


def send(html_body, date_str):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipients = [r.strip() for r in os.environ["MAIL_TO"].split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Günlük Bülten — {date_str}"
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())


TR_MONTHS = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def main():
    now_tr = datetime.now(timezone.utc).astimezone(timezone(TR_OFFSET))
    date_str = f"{now_tr.day} {TR_MONTHS[now_tr.month]} {now_tr.year}"

    data = collect_all()
    news = get_news()
    html_body = build_html(data, date_str, news=news)
    send(html_body, date_str)
    print(f"Mail gönderildi: {date_str}")


if __name__ == "__main__":
    main()
