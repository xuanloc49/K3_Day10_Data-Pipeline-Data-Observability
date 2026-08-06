from __future__ import annotations

from datetime import datetime
import re

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

HTML_TAG_RE = re.compile(r"<[^>]+>")
MIN_SUMMARY_CHARS = 100


def strip_markup(value: str) -> str:
    """Loai bo the XML/HTML va chuan hoa whitespace."""
    without_tags = HTML_TAG_RE.sub(" ", value or "")
    return normalize_whitespace(without_tags)


def _parse_date(value: str) -> datetime | None:
    text = normalize_whitespace(value)
    if not text:
        return None
    for fmt, length in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
        try:
            return datetime.strptime(text[:length], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    rows: list[dict] = []
    run_day = run_date.replace(tzinfo=None).date() if run_date.tzinfo else run_date.date()

    for record in records:
        title = strip_markup(record.title)
        summary = strip_markup(record.summary)
        if not title or len(summary) < MIN_SUMMARY_CHARS:
            continue

        authors = [strip_markup(author) for author in record.authors if strip_markup(author)]
        categories = [
            strip_markup(category) for category in record.categories if strip_markup(category)
        ]
        if not categories:
            # Crossref hiem khi tra ve `subject`; dung ten journal (container-title) lam category proxy.
            journal_name = strip_markup(record.comment)
            if journal_name:
                categories = [journal_name]
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)

        published_dt = _parse_date(record.published) or _parse_date(record.updated)
        if published_dt is None:
            published = ""
            age_days = None
        else:
            published = published_dt.date().isoformat()
            age_days = (run_day - published_dt.date()).days

        updated_dt = _parse_date(record.updated)
        updated = updated_dt.date().isoformat() if updated_dt else ""

        text_for_embedding = (
            f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": record.paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": categories[0] if categories else strip_markup(record.primary_category),
                "published": published,
                "updated": updated,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": strip_markup(record.comment),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True], na_position="last")
    return df.reset_index(drop=True)
