# sentinel:skip-file — hardcoded paths / templated placeholders are fixture/registry/audit-narrative data for this repo's research workflow, not portable application configuration. Same pattern as push_all_repos.py and E156 workbook files.
"""Generate a BMJ Analysis manuscript draft from lag_dataset."""
from __future__ import annotations
from pathlib import Path
import pandas as pd


def build_bmj_draft(lag: pd.DataFrame, out_path: Path) -> None:
    reached = lag[~lag["censored_l4"]]
    per_body = reached.groupby("body")["lag_to_l4_months"].agg(["median", "count"]).reset_index()
    per_body = per_body.sort_values("median", ascending=False)
    slowest = per_body.iloc[0]
    fastest = per_body.iloc[-1]
    overall_median = int(reached["lag_to_l4_months"].median())

    lines = [
        "# Cardiology evidence takes years to become strong recommendations, and the delay differs markedly by society",
        "",
        f"**Authors:** Mahmood Ahmad; affiliation Royal Free Hospital, London, United Kingdom; ORCID 0009-0003-7781-4478",
        "",
        "## Key messages",
        "",
        f"- Across {reached['class_id'].nunique()} pre-registered cardiology drug classes and four major guideline societies, Cochrane-confirmed evidence took a median of {overall_median} months to become a strong-recommend-for recommendation.",
        f"- {slowest['body'].upper()} was the slowest body, with median lag-to-strong of {int(slowest['median'])} months across {int(slowest['count'])} reached classes.",
        f"- {fastest['body'].upper()} was the fastest, at median {int(fastest['median'])} months.",
        "",
        "## Why this matters",
        "",
        "Guidelines drive prescribing and commissioning. Multi-year delays between meta-analytic confirmation and strong recommendation are a patient-level harm when the evidence is robust and the drugs are available.",
        "",
        "## What we did",
        "",
        "We pre-registered 10 cardiology drug classes and a uniform threshold rule (pooled hazard ratio upper 95% CI < 0.90 on the Cochrane-standard composite outcome). We reconstructed cumulative Cochrane meta-analyses from the Pairwise70 dataset, identified the year each crossed threshold, and measured months until each of ESC, ACC/AHA, NICE, and CCS assigned a strong-recommend-for classification.",
        "",
        "## Lag by society",
        "",
        "| Society | Median lag to strong-recommend (months) | Classes reached |",
        "|---|---|---|",
    ]
    for _, r in per_body.iterrows():
        lines.append(f"| {r['body'].upper()} | {int(r['median'])} | {int(r['count'])} |")

    lines += [
        "",
        "## Limitations",
        "",
        "This is a Cochrane-confirmation lens. For some classes, non-Cochrane meta-analyses (Lancet, JAMA, NEJM) crossed threshold earlier; we report those as sensitivity rows. We do not attribute lag to committee process, cost-effectiveness deliberations, or regulatory constraints.",
        "",
        "## Data and code",
        "",
        "Full lag dataset, pre-registered protocol, and pipeline code are available in the project repository. TruthCert HMAC bundle hashes the frozen dataset against the committed protocol files.",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
