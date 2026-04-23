# sentinel:skip-file — hardcoded paths / templated placeholders are fixture/registry/audit-narrative data for this repo's research workflow, not portable application configuration. Same pattern as push_all_repos.py and E156 workbook files.
"""Render an offline, single-file HTML dashboard from lag_dataset."""
from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GuidelineLag - Cardiology Evidence-to-Guideline Adoption Atlas</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#111}
h1{font-weight:600;letter-spacing:-0.01em}
table{border-collapse:collapse;width:100%;margin:1rem 0}
th,td{border:1px solid #ccc;padding:.4rem .6rem;text-align:center}
th{background:#f4f4f4;font-weight:600}
.heatmap td{font-variant-numeric:tabular-nums}
.censored{color:#888;font-style:italic}
.footer{font-size:.85rem;color:#555;margin-top:2rem;border-top:1px solid #eee;padding-top:1rem}
</style>
</head>
<body>
<h1>GuidelineLag - Cardiology Evidence-to-Guideline Adoption Atlas</h1>
<p>Months elapsed between Cochrane-confirmed pooled HR crossing upper-95%-CI &lt; 0.90 and first L4 (strong-recommend-for) appearance in each society's guidelines.</p>

<h2>Heatmap - lag-to-L4 (months)</h2>
<table class="heatmap">
<thead><tr><th>Class</th>__BODY_HEADERS__</tr></thead>
<tbody>__HEATMAP_ROWS__</tbody>
</table>

<h2>Society league table</h2>
<table>
<thead><tr><th>Society</th><th>Median lag-to-L4 (months)</th><th>Classes reaching L4</th></tr></thead>
<tbody>__LEAGUE_ROWS__</tbody>
</table>

<div class="footer">
Generated from <code>lag_dataset.csv</code>. Data rows: __N_ROWS__. See TruthCert bundle for reproducibility hashes.
</div>
<script>
const LAG_DATA = __JSON_DATA__;
</script>
</body>
</html>
"""


def render_dashboard(lag: pd.DataFrame, out_path: Path) -> None:
    bodies = sorted(lag["body"].unique().tolist())
    classes = sorted(lag["class_id"].unique().tolist())

    body_headers = "".join(f"<th>{b.upper()}</th>" for b in bodies)
    heatmap_rows = []
    for cls in classes:
        cells = [f"<td><strong>{cls}</strong></td>"]
        for body in bodies:
            row = lag[(lag["class_id"] == cls) & (lag["body"] == body)]
            if row.empty or bool(row.iloc[0]["censored_l4"]):
                cells.append('<td class="censored">NYR</td>')
            else:
                cells.append(f"<td>{int(row.iloc[0]['lag_to_l4_months'])}</td>")
        heatmap_rows.append(f"<tr>{''.join(cells)}</tr>")

    league = []
    for body in bodies:
        sub = lag[(lag["body"] == body) & ~lag["censored_l4"]]
        median = int(sub["lag_to_l4_months"].median()) if not sub.empty else None
        league.append({"body": body, "median": median, "n_reached": len(sub)})
    league.sort(key=lambda r: (r["median"] is None, r["median"] or 0))
    league_rows = "".join(
        f"<tr><td>{r['body'].upper()}</td><td>{r['median'] if r['median'] is not None else '-'}</td><td>{r['n_reached']}/{len(classes)}</td></tr>"
        for r in league
    )

    html = (TEMPLATE
            .replace("__BODY_HEADERS__", body_headers)
            .replace("__HEATMAP_ROWS__", "".join(heatmap_rows))
            .replace("__LEAGUE_ROWS__", league_rows)
            .replace("__N_ROWS__", str(len(lag)))
            .replace("__JSON_DATA__", json.dumps(lag.to_dict(orient="records"))))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
