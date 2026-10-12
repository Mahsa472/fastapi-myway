'''
Jinja filters, registered in main.py and used in templates like {{ post.created_date | timeago }}.
'''
from datetime import UTC, datetime


def _parse(value: str) -> datetime:
    date = datetime.fromisoformat(value)
    return date if date.tzinfo else date.replace(tzinfo=UTC)


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def date_format(value: str) -> str:
    date = _parse(value)
    return f"{date:%b} {date.day}, {date.year}" # Oct 2, 2026


def time_ago(value: str) -> str:
    seconds = (datetime.now(UTC) - _parse(value)).total_seconds()
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{_plural(minutes, 'minute')} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{_plural(hours, 'hour')} ago"
    days = hours // 24
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    return date_format(value)


def reading_time(text: str) -> str:
    minutes = max(1, round(len(text.split()) / 200)) # people read about 200 words per minute
    return f"{minutes} min read"


def initials(name: str) -> str:
    return "".join(word[0] for word in name.split()[:2]).upper() or "?"


def excerpt(text: str, length: int = 180) -> str:
    text = " ".join(text.split()) # line breaks don't make sense in a short preview
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "…"
