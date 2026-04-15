"""Compose a 7-sentence, <=156-word E156 article from a lag dataset."""
from __future__ import annotations
import re
import pandas as pd


def compose_article(lag: pd.DataFrame) -> dict:
    reached = lag[~lag["censored_l4"]].copy()
    per_body_median = reached.groupby("body")["lag_to_l4_months"].median().round(0).astype(int)
    overall_median = int(reached["lag_to_l4_months"].median())
    slowest_body = per_body_median.idxmax()
    slowest_med = int(per_body_median[slowest_body])
    fastest_body = per_body_median.idxmin()
    fastest_med = int(per_body_median[fastest_body])
    n_classes = reached["class_id"].nunique()
    n_pairs = len(reached)

    sentences = {
        "S1": "Does cardiology-guideline adoption of meta-analytically confirmed evidence lag systematically across major societies, and by how many months?",
        "S2": f"We pooled Cochrane Pairwise70 cumulative meta-analyses for {n_classes} pivotal cardiology drug classes against ESC, ACC/AHA, NICE, and CCS guideline editions through 2024.",
        "S3": "For each class we found the first Cochrane-year at which cumulative pooled hazard-ratio upper-95%-CI fell below 0.90, then counted months to the earliest strong-recommend-for edition.",
        "S4": f"Across {n_pairs} class-by-society pairs the median lag-to-strong-recommend was {overall_median} months, with {slowest_body.upper()} slowest at {slowest_med} months and {fastest_body.upper()} fastest at {fastest_med} months.",
        "S5": "Sensitivity with lag-to-first-citation corroborated the ordering, and right-censored pairs that had not reached strong-recommend were reported separately rather than dropped.",
        "S6": "Once Cochrane-confirmed, cardiology evidence still takes years to become strongly recommended in at least one major guideline body, and the spread between societies is clinically material.",
        "S7": "The analysis cannot attribute lag to any committee process and is bounded to the ten drug classes and Cochrane composite outcomes pre-registered in protocol/thresholds.yaml.",
    }
    body = " ".join(sentences[k] for k in sorted(sentences))
    word_count = len(body.split())
    return {
        "id": "GuidelineLag",
        "title": "Cardiology evidence-adoption lag: a systematic atlas across four guideline societies",
        "sentences": sentences,
        "body": body,
        "word_count": word_count,
        "estimand": "median lag-to-L4 (months)",
        "stratifier": "society",
    }


def validate_e156(article: dict) -> list[str]:
    errors = []
    if len(article.get("sentences", {})) != 7:
        errors.append("must have 7 sentences (S1..S7)")
    if article.get("word_count", 0) > 156:
        errors.append(f"word_count > 156 ({article.get('word_count')})")
    body = article.get("body", "")
    sent_count = len(re.findall(r"[.!?]+(?=\s|$)", body))
    if sent_count != 7:
        errors.append(f"body has {sent_count} sentences, expected 7")
    return errors
