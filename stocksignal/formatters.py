from __future__ import annotations


def print_articles(articles: list[dict[str, str | None]]) -> None:
    if not articles:
        print("No articles found.")
        return

    for idx, article in enumerate(articles, 1):
        title = article.get("title") or "No title"
        source = article.get("source") or "unknown source"
        date = article.get("seendate") or "unknown date"
        lang = article.get("language") or "?"
        url = article.get("url") or "unknown URL"

        print(f"[{idx}] {title}")
        print(f"    Source: {source} | Date: {date} | Lang: {lang}")
        print(f"    URL: {url}\n")
