# GuidelineLag

Systematic atlas of cardiology meta-analysis -> guideline adoption lag across ESC, ACC/AHA, NICE, and CCS, for 10 pre-registered drug classes.

> **Status: DEV-MODE (non-release).** `outputs/baseline_dev.json` carries `release_gate.promotable=false`. The committed lag_dataset is produced from synthetic inputs (seed=42) so the full pipeline is reviewable end-to-end, but the numeric results are NOT a claim about real guideline lag. Real-inputs promotion gates on (a) verified `protocol/cd_manual_cardio.csv` and (b) sourced guideline PDFs + extracted refs/recs. See the PR description for the release checklist.
>
> Live dev-mode preview: https://mahmood726-cyber.github.io/GuidelineLag/

## What it does

1. Filters the 501 Cochrane meta-analyses in Pairwise70 to a cardiology subset.
2. For each cardio MA, reconstructs the cumulative pooled hazard ratio by study-publication year using R `metafor`.
3. Identifies the first year the cumulative upper 95% CI bound crosses a pre-registered clinical-significance anchor (HR UCI < 0.90).
4. Cross-references the Cochrane DOI against reference lists of ESC, ACC/AHA, NICE, and CCS guideline editions.
5. Computes two lag metrics per (class, body) pair:
   - Lag-to-cite (months to first edition citing the Cochrane DOI).
   - Lag-to-L4 (months to first edition assigning a strong-recommend-for classification).
6. Produces: lag dataset CSV, offline HTML dashboard, 7-sentence E156 article, BMJ Analysis manuscript draft, and HMAC-signed TruthCert bundle.

## Scope

- 10 drug classes (see `protocol/classes.yaml`).
- 4 guideline societies (ESC, ACC/AHA, NICE, CCS).
- Cochrane-confirmation lens (non-Cochrane MAs reported as sensitivity where relevant).

## Non-goals

- Non-cardiology areas. Devices (TAVI, MitraClip, etc.). Causal attribution of lag. Patient-outcome modelling of delayed adoption.

## Reproducibility

- `protocol/thresholds.yaml`, `protocol/taxonomy.yaml`, and `protocol/classes.yaml` are pre-registered and committed before any threshold date is computed.
- `outputs/lag_dataset.csv` is the dev-mode numerical snapshot; `outputs/baseline_dev.json` records the frozen per-society medians plus a `release_gate` block.
- `outputs/truthcert/bundle_dev.json` hashes the dataset, protocol, baseline, and mode manifest under an HMAC key supplied via `TRUTHCERT_HMAC_KEY` (env var, or `.secrets/truthcert_dev_key.txt` which is gitignored). The key is never derived from bundle fields.

## Running the pipeline (dev-mode)

```
# Generate or set the HMAC key once:
python -c "import secrets; print(secrets.token_hex(32))" > .secrets/truthcert_dev_key.txt

# Synthesize + sign:
python scripts/synthesize_dev_mode.py
python scripts/sign_dev_bundle.py

# Test:
python -m pytest tests/ -q
```

For release-mode (real Cochrane RDA + guideline PDFs), Tasks 7 and 14 in `docs/superpowers/plans/2026-04-14-guidelinelag.md` must complete first.

## Related work

- `C:\NICECardiology\` - 2-class pilot this project generalizes.
- `C:\Projects\Pairwise70\` - 501-review Cochrane dataset used as MA feedstock.

## Licence

MIT.
