"""Sentiment scoring with VADER (headlines / short text)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# VADER convention: compound in [-1, 1]; common thresholds for label
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def _get_analyzer():
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer()
    except ImportError as e:
        raise RuntimeError(
            'Sentiment requires "vaderSentiment". Install with: pip install vaderSentiment'
        ) from e


def score_text(text: str) -> tuple[float, str]:
    """
    Score a single string with VADER. Returns (compound_score, label).
    label is "Positive", "Neutral", or "Negative".
    """
    if not (text or "").strip():
        return 0.0, "Neutral"
    analyzer = _get_analyzer()
    scores = analyzer.polarity_scores((text or "").strip())
    compound = float(scores.get("compound", 0.0))
    if compound >= POSITIVE_THRESHOLD:
        label = "Positive"
    elif compound <= NEGATIVE_THRESHOLD:
        label = "Negative"
    else:
        label = "Neutral"
    return compound, label


def score_articles(
    articles: Sequence[dict[str, str | None]],
    title_key: str = "title",
) -> list[dict[str, str | None]]:
    """
    Add sentiment fields to each article. Mutates and returns the same list;
    each item gets "sentiment_compound" (float) and "sentiment" (str).
    """
    analyzer = _get_analyzer()
    for art in articles:
        text = (art.get(title_key) or "").strip() or ""
        if not text:
            art["sentiment_compound"] = 0.0
            art["sentiment"] = "Neutral"
            continue
        scores = analyzer.polarity_scores(text)
        compound = float(scores.get("compound", 0.0))
        art["sentiment_compound"] = compound
        if compound >= POSITIVE_THRESHOLD:
            art["sentiment"] = "Positive"
        elif compound <= NEGATIVE_THRESHOLD:
            art["sentiment"] = "Negative"
        else:
            art["sentiment"] = "Neutral"
    return list(articles)


def aggregate_sentiment(articles: Sequence[dict[str, str | None]]) -> dict[str, float | int]:
    """
    Return aggregate stats: mean compound, and counts of Positive / Neutral / Negative.
    Expects articles to already have "sentiment_compound" and "sentiment" (e.g. from score_articles).
    """
    if not articles:
        return {"mean_compound": 0.0, "positive": 0, "neutral": 0, "negative": 0}
    compounds = []
    pos = neu = neg = 0
    for art in articles:
        c = art.get("sentiment_compound")
        if c is not None:
            compounds.append(float(c))
        s = (art.get("sentiment") or "").strip().lower()
        if s == "positive":
            pos += 1
        elif s == "negative":
            neg += 1
        else:
            neu += 1
    mean = sum(compounds) / len(compounds) if compounds else 0.0
    return {"mean_compound": mean, "positive": pos, "neutral": neu, "negative": neg}
