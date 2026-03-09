# StockSignal

Search recent news for any stock or company, with optional **sentiment analysis** (VADER). Uses the [GDELT 2.1 Doc API](https://blog.gdeltproject.org/gdelt-doc-2-1-api-debuts/).

## Features

- **Ticker search** — Autocomplete from 5,000+ NASDAQ symbols; type any ticker or company name.
- **Keyword filters** — Narrow results (e.g. `guidance`, `earnings`, `investigation`).
- **Sentiment** — VADER sentiment on headlines; aggregate and per-article.
- **CLI + Web UI** — Use from the terminal or run the Streamlit dashboard.

## Quick start

```powershell
cd StockSignal   # or your project folder
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Web app (recommended):**

```powershell
streamlit run app.py
```

**CLI:**

```powershell
python main.py MSFT -k "guidance, investigation" -d 5 -l 40
```

## CLI options

| Option | Description |
|--------|-------------|
| `symbol` | Ticker or company name (e.g. `AAPL`, `"Bank of America"`) |
| `-k` / `--keyword` | Keywords (repeatable or comma-separated) |
| `-d` / `--days` | Days of history (default `3`; `0` = all available) |
| `-l` / `--limit` | Max articles (1–250, default `25`) |
| `--allow-non-english` | Include non-English sources |

**Examples:**

```powershell
python main.py "NVIDIA" -k "ai, chips, guidance"
python main.py AAPL -k "earnings, outlook" -d 2
python main.py "Tesla" --allow-non-english -l 15
python main.py "Meta" -k "privacy, regulation" -d 7
```

## Tech

- **Python** — Fetch (GDELT), sentiment (VADER), CLI.
- **Streamlit** — Web UI; ticker autocomplete via [streamlit-searchbox](https://github.com/m-wrzr/streamlit-searchbox).
- **Data** — Ticker list from [NASDAQ listings](https://github.com/datasets/nasdaq-listings) (refreshed daily).

## Notes

- GDELT rate-limits; the app retries with backoff. Use lower **limit** / fewer requests if you hit 429.
- English-only filter: `sourcelang:english`; disable with `--allow-non-english` (CLI) or the sidebar toggle (app).
- Keywords under 3 characters are skipped (GDELT constraint).
