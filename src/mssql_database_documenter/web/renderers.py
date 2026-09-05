"""Safe, complete file presentation with pagination and raw-source retention."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
from typing import Any

import bleach
import markdown

from ..comparison.normalizers import raise_csv_field_limit


ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    "p", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6", "table", "thead",
    "tbody", "tfoot", "tr", "th", "td", "caption", "blockquote", "hr", "br", "div",
    "span", "main", "section", "article", "header", "footer", "aside", "dl", "dt", "dd",
    "details", "summary", "small", "mark",
}
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "role", "aria-label", "aria-labelledby"],
    "a": ["href", "title"],
    "th": ["scope", "colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
}
MAX_FORMATTED_FILE_BYTES = 5 * 1024 * 1024


def _trusted_report_html(source: str) -> str:
    """Extract a generated report body and retain safe structure, never executable markup."""
    source = re.sub(r"(?is)<(script|style|iframe|object|embed)\b[^>]*>.*?</\1\s*>", "", source)
    body = re.search(r"(?is)<body\b[^>]*>(.*?)</body\s*>", source)
    fragment = body.group(1) if body else source
    return bleach.clean(
        fragment,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        strip=True,
        strip_comments=True,
    )


def _pagination(page: int, per_page: int, total: int) -> dict[str, int]:
    page = max(1, page)
    per_page = min(200, max(1, per_page))
    start = (page - 1) * per_page
    return {"page": page, "per_page": per_page, "total": total, "start": min(start + 1, total) if total else 0, "end": min(start + per_page, total)}


def _page(values: list[Any], page: int, per_page: int) -> tuple[list[Any], dict[str, int]]:
    pagination = _pagination(page, per_page, len(values))
    start = (pagination["page"] - 1) * pagination["per_page"]
    return values[start:start + pagination["per_page"]], pagination


def _csv(path: Path, *, page: int, per_page: int, search: str, sort: str, descending: bool) -> dict[str, Any]:
    raise_csv_field_limit()
    page = max(1, page); per_page = min(200, max(1, per_page)); start = (page - 1) * per_page
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle); headers = list(reader.fieldnames or [])
        sorting_allowed = path.stat().st_size <= MAX_FORMATTED_FILE_BYTES
        if sort and sort in headers and sorting_allowed:
            rows = [row for row in reader if not search or any(search.casefold() in str(value).casefold() for value in row.values())]
            rows.sort(key=lambda row: str(row.get(sort, "")).casefold(), reverse=descending)
            visible, pagination = _page(rows, page, per_page)
            return {"kind": "csv", "headers": headers, "rows": visible, "pagination": pagination, "search": search, "sort": sort, "descending": descending}
        visible = []
        total = 0
        for row in reader:
            if search and not any(search.casefold() in str(value).casefold() for value in row.values()):
                continue
            if start <= total < start + per_page:
                visible.append(row)
            total += 1
    notice = "Sorting is disabled for large files; all rows remain available in source order, raw view, and download." if sort and sort in headers and not sorting_allowed else ""
    return {"kind": "csv", "headers": headers, "rows": visible, "pagination": _pagination(page, per_page, total), "search": search, "sort": "" if notice else sort, "descending": descending, "notice": notice}


def _text(path: Path, *, kind: str, page: int, per_page: int, search: str) -> dict[str, Any]:
    page = max(1, page); per_page = min(200, max(1, per_page)); start = (page - 1) * per_page
    visible = []
    total = 0
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, value in enumerate(handle, 1):
            value = value.rstrip("\r\n")
            if search and search.casefold() not in value.casefold():
                continue
            if start <= total < start + per_page:
                visible.append({"number": line_number, "text": value})
            total += 1
    return {"kind": kind, "lines": visible, "pagination": _pagination(page, per_page, total), "search": search}


def render_file(path: Path, *, page: int = 1, per_page: int = 50, search: str = "", sort: str = "", descending: bool = False) -> dict[str, Any]:
    suffix = path.suffix.casefold()
    metadata = {"name": path.name, "size": path.stat().st_size, "suffix": suffix}
    if suffix == ".csv": result = _csv(path, page=page, per_page=per_page, search=search, sort=sort, descending=descending)
    elif "mermaid" in path.name.casefold():
        result = _text(path, kind="mermaid", page=page, per_page=per_page, search=search)
    elif suffix == ".md":
        if path.stat().st_size > MAX_FORMATTED_FILE_BYTES:
            return {**metadata, **_text(path, kind="text", page=page, per_page=per_page, search=search), "notice": "Large Markdown is shown as paginated source to keep rendering memory-bounded."}
        source = path.read_text(encoding="utf-8-sig", errors="replace")
        if "```mermaid" in source.casefold():
            result = _text(path, kind="mermaid", page=page, per_page=per_page, search=search)
        else:
            rendered = markdown.markdown(source, extensions=("tables", "fenced_code", "sane_lists", "admonition"))
            result = {"kind": "markdown", "html": bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols={"http", "https"})}
    elif suffix == ".json":
        if path.stat().st_size > MAX_FORMATTED_FILE_BYTES:
            return {**metadata, **_text(path, kind="text", page=page, per_page=per_page, search=search), "notice": "Large JSON is shown as paginated source to keep rendering memory-bounded."}
        value = json.loads(path.read_text(encoding="utf-8-sig")); result = {"kind": "json", "json": value, "pretty": json.dumps(value, indent=2, ensure_ascii=False)}
    elif suffix in {".sql", ".tsql"}: result = _text(path, kind="sql", page=page, per_page=per_page, search=search)
    elif suffix in {".txt", ".log", ".sha256"} or path.name == "checksums.sha256": result = _text(path, kind="text", page=page, per_page=per_page, search=search)
    elif suffix == ".html":
        if path.stat().st_size > MAX_FORMATTED_FILE_BYTES:
            return {**metadata, **_text(path, kind="text", page=page, per_page=per_page, search=search), "notice": "Large HTML is shown as paginated source to keep rendering memory-bounded."}
        source = path.read_text(encoding="utf-8-sig", errors="replace")
        trusted = "21_HTML_Report" in path.parts or "comparisons" in path.parts
        if trusted:
            result = {"kind": "html", "trusted": True, "html": _trusted_report_html(source)}
        else:
            result = _text(path, kind="text", page=page, per_page=per_page, search=search)
            result["trusted"] = False
    else: result = {"kind": "unsupported", "message": "Preview is unavailable; raw view and download retain the full source."}
    return {**metadata, **result}
