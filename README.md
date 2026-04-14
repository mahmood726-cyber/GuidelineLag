# GuidelineLag

Systematic atlas of cardiology meta-analysis -> guideline adoption lag across ESC, ACC/AHA, NICE, and CCS, for 10 pre-registered drug classes.

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
- `tests/baselines/lag_dataset_frozen.csv` is the committed numerical baseline. Any pipeline change that moves a row triggers baseline review.
- TruthCert bundle (`outputs/truthcert/bundle.json`) hashes the dataset, protocol, and git commit under an HMAC key supplied via `TRUTHCERT_HMAC_KEY` env var.

## Running the pipeline

```
set TRUTHCERT_HMAC_KEY=your-secret
python -m src.python.preflight
python scripts/run_pipeline.py
python -m pytest tests/ -v
```

## Related work

- `C:\NICECardiology\` - 2-class pilot this project generalizes.
- `C:\Projects\Pairwise70\` - 501-review Cochrane dataset used as MA feedstock.

## Licence

MIT.
