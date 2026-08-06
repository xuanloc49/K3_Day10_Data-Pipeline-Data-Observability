from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

CROSSREF_API_URL = "https://api.crossref.org/works"
RETRY_STATUS_CODES = {429, 503}
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 1.5


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _date_parts_to_iso(date_parts: list | None) -> str:
    if not date_parts:
        return ""
    parts = date_parts[0] if isinstance(date_parts[0], list) else date_parts
    if not parts:
        return ""
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def _extract_date(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if not isinstance(value, dict):
            continue
        date_parts = value.get("date-parts")
        iso = _date_parts_to_iso(date_parts)
        if iso:
            return iso
        date_time = value.get("date-time")
        if isinstance(date_time, str) and date_time:
            return date_time[:10]
    return ""


def _extract_authors(item: dict) -> list[str]:
    authors: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        given = normalize_whitespace(str(author.get("given") or ""))
        family = normalize_whitespace(str(author.get("family") or ""))
        name = normalize_whitespace(f"{given} {family}")
        if not name:
            name = normalize_whitespace(str(author.get("name") or ""))
        if name:
            authors.append(name)
    return authors


def _extract_pdf_url(item: dict) -> str:
    for link in item.get("link") or []:
        if not isinstance(link, dict):
            continue
        content_type = str(link.get("content-type") or "").lower()
        url = str(link.get("URL") or "").strip()
        if url and "pdf" in content_type:
            return url
    for link in item.get("link") or []:
        if not isinstance(link, dict):
            continue
        url = str(link.get("URL") or "").strip()
        if url.lower().endswith(".pdf"):
            return url
    return ""


def _extract_summary(item: dict) -> str:
    for key in ("abstract", "description"):
        value = item.get(key)
        if isinstance(value, str) and normalize_whitespace(value):
            return normalize_whitespace(value)
        if isinstance(value, list):
            joined = normalize_whitespace(" ".join(str(part) for part in value if part))
            if joined:
                return joined
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    message = payload.get("message") or {}
    items = message.get("items") or []
    records: list[PaperRecord] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        titles = item.get("title") or []
        title = normalize_whitespace(str(titles[0])) if titles else ""
        summary = _extract_summary(item)
        if not title or not summary:
            continue

        doi = normalize_whitespace(str(item.get("DOI") or ""))
        paper_id = doi or normalize_whitespace(str(item.get("URL") or title))
        if not paper_id:
            continue

        authors = _extract_authors(item)
        categories = [
            normalize_whitespace(str(subject))
            for subject in (item.get("subject") or [])
            if normalize_whitespace(str(subject))
        ]
        container = item.get("container-title") or []
        comment = normalize_whitespace(str(container[0])) if container else ""

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=_extract_date(
                    item,
                    "published-print",
                    "published-online",
                    "published",
                    "issued",
                    "created",
                ),
                updated=_extract_date(item, "deposited", "indexed", "created"),
                abs_url=normalize_whitespace(str(item.get("URL") or (f"https://doi.org/{doi}" if doi else ""))),
                pdf_url=_extract_pdf_url(item),
                comment=comment,
            )
        )

    return records


def _request_with_retry(url: str, params: dict[str, str | int], headers: dict[str, str]) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=60)
            if response.status_code in RETRY_STATUS_CODES:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    sleep_seconds = float(retry_after)
                else:
                    sleep_seconds = BASE_BACKOFF_SECONDS * (2**attempt)
                time.sleep(sleep_seconds)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(BASE_BACKOFF_SECONDS * (2**attempt))
    raise RuntimeError(f"Failed to fetch Crossref after {MAX_RETRIES} retries: {last_error}")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi Crossref API, luu raw response, parse thanh records."""
    params: dict[str, str | int] = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "User-Agent": "Day10DataObservabilityLab/0.1 (mailto:student@example.com)",
        "Accept": "application/json",
    }

    payload = _request_with_retry(CROSSREF_API_URL, params=params, headers=headers)
    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh PaperRecord."""
    payload = read_json(path)
    if isinstance(payload, dict):
        return parse_crossref_payload(payload)
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected raw records format at {path}")

    records: list[PaperRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        records.append(
            PaperRecord(
                paper_id=str(item.get("paper_id") or ""),
                title=str(item.get("title") or ""),
                summary=str(item.get("summary") or ""),
                authors=[str(author) for author in (item.get("authors") or [])],
                categories=[str(category) for category in (item.get("categories") or [])],
                primary_category=str(item.get("primary_category") or ""),
                published=str(item.get("published") or ""),
                updated=str(item.get("updated") or ""),
                abs_url=str(item.get("abs_url") or ""),
                pdf_url=str(item.get("pdf_url") or ""),
                comment=str(item.get("comment") or ""),
            )
        )
    return records
