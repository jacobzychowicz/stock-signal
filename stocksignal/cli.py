from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .config import EXAMPLE_COMMANDS, MIN_KEYWORD_LEN, MAX_RECORDS
from .formatters import print_articles
from .gdelt import fetch_articles
from .keywords import normalize_keywords
from .symbols import expand_symbol_to_company_name


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search stock-related news via GDELT (English-only by default)."
    )
    parser.add_argument("symbol", help="Stock symbol or company name (e.g., MSFT or Microsoft)")
    parser.add_argument(
        "-k",
        "--keyword",
        action="append",
        dest="keywords",
        default=None,
        help="Keyword(s) to include; repeatable or comma-separated string.",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=3,
        help="How many days back to search (0 = all available).",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=25,
        help=f"Max articles to return (1-{MAX_RECORDS}).",
    )
    parser.add_argument(
        "--allow-non-english",
        action="store_true",
        help="Disable the English-only filter (default keeps only English).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(argv or sys.argv[1:])
    if not args_list:
        print("Try one of these commands:")
        for example in EXAMPLE_COMMANDS:
            print(f"  python main.py {example}")
        print("\nUse -h/--help for full options.")
        return 1

    args = parse_args(args_list)

    try:
        keywords, skipped = normalize_keywords(args.keywords)
        if skipped:
            print(
                f"Skipping short keywords (<{MIN_KEYWORD_LEN} chars): {', '.join(skipped)}",
                flush=True,
            )

        def do_fetch(target_symbol: str):
            return fetch_articles(
                symbol=target_symbol,
                keywords=keywords,
                days=args.days,
                limit=args.limit,
                english_only=not args.allow_non_english,
            )

        try:
            articles = do_fetch(args.symbol)
        except RuntimeError as exc:
            msg = str(exc).lower()
            fallback_used = False
            if "phrase is too short" in msg:
                expanded = expand_symbol_to_company_name(args.symbol)
                if expanded and expanded.lower() != args.symbol.lower():
                    print(
                        f'Query phrase too short for "{args.symbol}". '
                        f'Retrying with company name "{expanded}".',
                        flush=True,
                    )
                    articles = do_fetch(expanded)
                    fallback_used = True
            if not fallback_used:
                raise
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"Error: {exc}")
        return 1

    print_articles(articles)
    return 0
