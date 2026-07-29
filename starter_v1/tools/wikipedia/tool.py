from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary"


WIKI_HEADERS = {
    "User-Agent": "AI20k-Lab-Research-Agent/1.0 (educational; contact: local)",
    "Accept-Language": "en",
}


def _wiki_get(title: str, lang: str = "en") -> dict[str, Any]:
    headers = {**WIKI_HEADERS, "Accept-Language": lang}
    response = requests.get(
        f"{WIKI_API}/{quote(title)}",
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _wiki_search(query: str, lang: str = "en", limit: int = 5) -> list[str]:
    url = f"https://{lang}.wikipedia.org/w/api.php"
    response = requests.get(
        url,
        params={
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "format": "json",
        },
        headers=WIKI_HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data[1] if len(data) > 1 else []


def search_wikipedia(query: str = "", lang: str = "en", limit: int = 3) -> dict[str, Any]:
    try:
        titles = _wiki_search(query, lang, max(1, min(int(limit or 3), 5)))
        if not titles:
            return {
                "tool": "search_wikipedia",
                "query": query,
                "lang": lang,
                "items": [],
                "message": f"No Wikipedia article found for '{query}'.",
            }

        items: list[dict[str, Any]] = []
        for title in titles[:max(1, min(int(limit or 3), 5))]:
            try:
                data = _wiki_get(title, lang)
            except requests.HTTPError as http_err:
                if http_err.response is not None and http_err.response.status_code == 404:
                    continue
                raise
            items.append({
                "title": data.get("title") or title,
                "url": data.get("content_urls", {}).get("desktop", {}).get("page") or f"https://{lang}.wikipedia.org/wiki/{quote(title)}",
                "source": "wikipedia.org",
                "summary": (data.get("extract") or "")[:2000],
                "description": data.get("description") or "",
                "page_id": data.get("pageid"),
                "thumbnail": data.get("thumbnail", {}).get("source") if data.get("thumbnail") else None,
                "lang": data.get("lang") or lang,
            })

        return {
            "tool": "search_wikipedia",
            "query": query,
            "lang": lang,
            "items": items,
        }
    except Exception as exc:
        return err("search_wikipedia", exc)
