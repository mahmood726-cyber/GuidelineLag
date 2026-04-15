"""Dev-mode synthesis: fabricate lag_dataset end-to-end. NON-RELEASE.

Produces:
  outputs/lag_dataset.csv
  outputs/mode.json          (synthetic=true, seed, timestamp)
  outputs/baseline_dev.json  (per-society medians, Spearman, censored count)
  outputs/dashboard.html
  outputs/e156_body.txt
  outputs/manuscript.md

The shape mirrors what the release pipeline would produce once real Cochrane
Pairwise70 RDA files and sourced guideline PDFs are wired in. Every output is
tagged dev-release-blocked; TruthCert (Task 21) will carry the same flag.
"""
from __future__ import annotations

import json
import platform
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "python"))

from build_dashboard import render_dashboard
from build_manuscript import build_bmj_draft
from e156_compose import compose_article, validate_e156
from lag_calculator import build_lag_dataset

SEED = 42
MODE = "dev-release-blocked"
SYNTHETIC = True

# Synthetic Cochrane-threshold-crossed year per class. Chosen to straddle
# realistic cardiology-evidence milestones without claiming to reproduce them.
THRESHOLD_ANCHOR = {
    "sglt2i_hfref": 2019,
    "sglt2i_hfpef": 2022,
    "pcsk9i": 2017,
    "icosapent": 2019,
    "finerenone_hf": 2024,
    "arni": 2014,
    "ticagrelor": 2011,
    "glp1_ra_cv": 2016,
    "colchicine_ccs": 2020,
    "af_ablation_first_line": 2021,
}

# Expected per-society lag-to-L4 (months), before per-class noise.
BASE_LAG_BY_BODY = {"esc": 18, "acc_aha": 24, "nice": 36, "ccs": 30}

BODIES = ("esc", "acc_aha", "nice", "ccs")

# Probability a (class, body) pair is still NYR (not-yet-reached) at cutoff.
CENSOR_PROB = 0.15
CUTOFF = date(2026, 4, 15)


def _synth_threshold_dates(classes: list[str]) -> pd.DataFrame:
    rows = []
    for cls in classes:
        rows.append({
            "cd_id": f"MAN_{cls}",
            "class_id": cls,
            "threshold_year": THRESHOLD_ANCHOR[cls],
        })
    return pd.DataFrame(rows)


def _synth_citations(rng, classes: list[str]) -> pd.DataFrame:
    """First citing publication per (class_id, body) = threshold anchor + 3-18 mo."""
    rows = []
    for cls in classes:
        anchor = date(THRESHOLD_ANCHOR[cls], 7, 1)
        for body in BODIES:
            lag_m = int(rng.integers(3, 19))
            d = _add_months(anchor, lag_m)
            if d > CUTOFF:
                continue
            rows.append({
                "cd_id": f"MAN_{cls}",
                "body": body,
                "first_citing_pub_date": d.isoformat(),
            })
    return pd.DataFrame(rows)


def _synth_l4(rng, classes: list[str]) -> pd.DataFrame:
    rows = []
    for cls in classes:
        anchor = date(THRESHOLD_ANCHOR[cls], 7, 1)
        for body in BODIES:
            if rng.random() < CENSOR_PROB:
                continue
            base = BASE_LAG_BY_BODY[body]
            noise = int(rng.integers(-8, 13))
            lag_m = max(2, base + noise)
            d = _add_months(anchor, lag_m)
            if d > CUTOFF:
                continue
            rows.append({
                "class_id": cls,
                "body": body,
                "first_l4_pub_date": d.isoformat(),
            })
    return pd.DataFrame(rows)


def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    try:
        return date(y, m, d.day)
    except ValueError:
        return date(y, m, 28)


def _baseline_metrics(lag: pd.DataFrame) -> dict:
    reached = lag[~lag["censored_l4"]].copy()
    per_body = (reached.groupby("body")["lag_to_l4_months"]
                .agg(["median", "count"]).to_dict(orient="index"))
    per_body_clean = {b: {"median_months": float(v["median"]), "n_reached": int(v["count"])}
                      for b, v in per_body.items()}
    overall_median = float(reached["lag_to_l4_months"].median())

    both = lag.dropna(subset=["lag_to_cite_months", "lag_to_l4_months"])
    if len(both) >= 3:
        spearman = float(both[["lag_to_cite_months", "lag_to_l4_months"]]
                         .corr(method="spearman").iloc[0, 1])
    else:
        spearman = None

    return {
        "overall_median_lag_to_l4_months": overall_median,
        "per_body": per_body_clean,
        "spearman_cite_vs_l4": spearman,
        "n_pairs_total": int(len(lag)),
        "n_pairs_reached_l4": int(len(reached)),
        "n_pairs_censored_l4": int(lag["censored_l4"].sum()),
        "n_classes": int(lag["class_id"].nunique()),
    }


def main() -> int:
    rng = np.random.default_rng(SEED)
    classes_yaml = yaml.safe_load((ROOT / "protocol" / "classes.yaml").read_text())
    classes = [c["id"] for c in classes_yaml["classes"]]
    assert set(classes) == set(THRESHOLD_ANCHOR), "classes.yaml drift vs THRESHOLD_ANCHOR"

    threshold_dates = _synth_threshold_dates(classes)
    citations = _synth_citations(rng, classes)
    l4 = _synth_l4(rng, classes)

    lag = build_lag_dataset(threshold_dates, citations, l4, bodies=BODIES)

    outputs = ROOT / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    lag_path = outputs / "lag_dataset.csv"
    lag.to_csv(lag_path, index=False)

    metrics = _baseline_metrics(lag)

    mode_manifest = {
        "mode": MODE,
        "synthetic": SYNTHETIC,
        "seed": SEED,
        "generated_on": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "notes": "Dev-mode synthetic lag_dataset. Non-release. Task 14 (real PDFs) "
                 "and Task 7 (Cochrane CD ID verification) must complete before "
                 "this baseline is promoted to release.",
    }
    (outputs / "mode.json").write_text(json.dumps(mode_manifest, indent=2), encoding="utf-8")

    baseline = {
        "mode": MODE,
        "synthetic": SYNTHETIC,
        "seed": SEED,
        "generated_on": mode_manifest["generated_on"],
        "metrics": metrics,
        "release_gate": {
            "promotable": False,
            "reason": "synthetic_inputs",
            "required_before_release": [
                "Task 7: verified cd_manual_cardio.csv (Cochrane CD IDs)",
                "Task 14: sourced guideline PDFs + extracted recs + refs",
                "Task 18: rerun synthesize on real inputs with AUC >= 0.70 on "
                          "SGLT2i HFrEF NICECardiology anchor",
            ],
        },
    }
    baseline_path = outputs / "baseline_dev.json"
    baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    render_dashboard(lag, outputs / "dashboard.html")

    # Pages copy with a dev-mode banner injected before the H1.
    docs_path = ROOT / "docs" / "index.html"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    html = (outputs / "dashboard.html").read_text(encoding="utf-8")
    banner = (
        '<div style="background:#fff3cd;border:1px solid #ffeeba;padding:.75rem 1rem;'
        'margin:0 0 1rem;border-radius:.25rem;color:#856404;font-size:.95rem">'
        '<strong>DEV-MODE PREVIEW.</strong> Synthetic inputs (seed=42). '
        'Not release data. Promotion gated on Tasks 7 and 14 — '
        'see <code>outputs/baseline_dev.json</code> for the release gate.'
        '</div>'
    )
    docs_path.write_text(html.replace("<h1>", banner + "<h1>", 1), encoding="utf-8")

    article = compose_article(lag)
    e156_errors = validate_e156(article)
    if e156_errors:
        print(f"E156 validation errors: {e156_errors}", file=sys.stderr)
        return 2
    (outputs / "e156_body.txt").write_text(article["body"], encoding="utf-8")

    build_bmj_draft(lag, outputs / "manuscript.md")

    print(f"[dev-mode] lag_dataset rows: {len(lag)}")
    print(f"[dev-mode] overall median lag-to-L4: {metrics['overall_median_lag_to_l4_months']:.0f} mo")
    print(f"[dev-mode] per-body medians: "
          f"{ {b: v['median_months'] for b, v in metrics['per_body'].items()} }")
    print(f"[dev-mode] baseline: {baseline_path}")
    print(f"[dev-mode] NON-RELEASE — synthetic=true, mode={MODE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
