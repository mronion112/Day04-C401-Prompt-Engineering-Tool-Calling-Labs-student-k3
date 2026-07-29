from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err

BOOK_API_URL = "https://api.bigbookapi.com/search-books"


def search_book(query: str = "", max_results: int = 3) -> dict[str, Any]:
    try:
        key = os.getenv("BOOK_API_KEY")
        if not key:
            raise RuntimeError("Missing BOOK_API_KEY env var")

        response = requests.get(
            BOOK_API_URL,
            params={"query": query, "api-key": key},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        books = data.get("books") or []

        items: list[dict[str, Any]] = []
        for entry in books[: max(1, int(max_results or 3))]:
            if isinstance(entry, list) and entry:
                entry = entry[0]
            if not isinstance(entry, dict):
                continue
            book = entry
            authors_info = book.get("authors") or []
            author_names = [a.get("name", "") for a in authors_info if isinstance(a, dict) and a.get("name")]
            rating_info = book.get("rating") or {}
            items.append({
                "title": book.get("title") or "Unknown",
                "url": book.get("url") or "",
                "source": "bigbookapi.com",
                "summary": f"By {', '.join(author_names)}" if author_names else "",
                "authors": author_names,
                "rating": rating_info.get("average") if isinstance(rating_info, dict) else rating_info,
                "image": book.get("image") or "",
                "book_id": book.get("id"),
            })

        return {
            "tool": "search_book",
            "query": query,
            "items": items,
            "total_results": data.get("total", len(items)),
        }
    except Exception as exc:
        return err("search_book", exc)
