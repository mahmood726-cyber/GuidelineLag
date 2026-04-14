# GuidelineLag Design

Status: draft
Date: 2026-04-14
Author: Mahmood Ahmad

## Purpose

Quantify adoption lag: for every Cochrane CDSR meta-analysis whose pooled effect crosses a pre-specified clinical threshold, measure the time from MA publication to the first ESC / ACC-AHA / NICE cardiology guideline edition that cites the MA and changes an associated recommendation class or strength.

Ships a BMJ/JAMA Analysis manuscript (survival analysis: Kaplan-Meier + Cox PH), an E156 micro-paper, a static GitHub Pages dashboard, and a reusable adoption-lag CSV.

## Non-goals

- Not covering non-cardiology societies (Phase 2).
- Not covering landmark non-Cochrane MAs (Phase 2).
- Not attributing lag to individual committee dynamics (descriptive survival analysis only).
- Not using Altmetric / media-attention covariates (judged measurement-error heavy during decision B).
- Not covering guideline editions before 2010.

## Cohort

- **MA trigger set:** Cochrane CDSR MAs whose pooled effect crosses a pre-specified minimum clinically important effect threshold. Threshold table pre-registered in `sap/mce_thresholds.yml` (e.g. HR < 0.85 or > 1.15 for mortality; topic-specific MCID for symptom scores). Thresholds are frozen before cohort assembly and cited in the manuscript.
- **Guideline corpus:** ESC / ACC-AHA / NICE cardiology full edition history from 2010 to the pinned export date. Edition manifest version-controlled in `guideline_archive/edition_manifest.yml`.

## Module layout

```
C:\Models\GuidelineLag\
  cohort/                # Cochrane MAs, effect-threshold filter
  guideline_archive/     # per-society PDF set + edition manifest
  citation_extractor/    # ref-list parse; Cochrane ID match; hand-audit gate
  rec_class_parser/      # class/LoE per citation + class-change vs prior edition
  event_engine/          # endpoint B (primary) and endpoint C (secondary); censoring
  survival/              # KM + Cox PH; Schoenfeld PH check; RMST fallback
  analysis/              # per-society median lag, HRs, league
  dashboard/             # KM curves, Cox forest, lag tables, per-MA cards
  paper/                 # BMJ Analysis manuscript
  e156-submission/       # E156 body + workbook entry
  sap/                   # pre-registered analysis plan, MCE thresholds, covariate list
  tests/                 # extractor + Cox + PH + schema checks
  data/                  # pinned exports; adoption_lag.csv (reusable)
  docs/                  # this spec + downstream plan
  LICENSE, README.md, E156-PROTOCOL.md, index.html, PROGRESS.md (gitignored)
```

## Endpoints

- **Primary endpoint B:** months from MA publication date to the first guideline edition that (a) cites the MA in its reference list AND (b) changes the class or strength of the associated recommendation relative to the immediately prior edition of that guideline.
- **Secondary endpoint C:** months from MA publication to the first edition where a Class I or IIa recommendation is aligned with the MA's pooled-effect direction (i.e. the guideline moved in the direction the MA supports). Requires per-MA PICO-to-recommendation matching; hand-audited.
- **Censoring:** at the latest available edition per guideline (society-specific censor date). Right-censoring only; no loss-to-follow-up interpretation because guideline editions are publicly observed.

## Cox regression covariates

Pre-specified in `sap/covariates.yml`. All six entered simultaneously:

1. MA sponsor (industry vs non-industry, binary).
2. MA effect magnitude (|log HR| or standardized |effect|, continuous).
3. Society (ESC / ACC-AHA / NICE, categorical).
4. GRADE rating of the MA (high / moderate / low / very low, ordinal).
5. Journal tier (Cochrane / top-5 general / top cardiology / other, categorical).
6. Topic area (prevention / drug / device / diagnostic, categorical).

Schoenfeld residuals test the proportional-hazards assumption per covariate. If PH is rejected for any covariate, the manuscript reports interval-specific HRs or RMST difference at a stated `tau*` in place of the single Cox coefficient (per advanced-stats rules: single HR is misleading under non-PH).

## Adoption-lag CSV schema

`data/adoption_lag.csv`, one row per MA in the cohort:

```
cochrane_id, pmid, pub_date, effect_direction, effect_magnitude,
first_adoption_edition_date, endpoint_b_months, endpoint_c_months,
event_b, event_c, censor_date, sponsor, grade, journal_tier,
topic_area, society_cited
```

## Data sources

All OA:

- Cochrane CDSR metadata export (same pinned dated version as Proto-Pub-Drift and RetractRipple).
- CDSR `results_data` tables for MA pooled effects.
- CDSR summary-of-findings tables for GRADE ratings.
- ESC guideline PDF archive (escardio.org/Guidelines).
- ACC-AHA guideline PDF archive (jacc.org / Circulation).
- NICE cardiology archive (nice.org.uk).

No paywalled sources. Edition PDFs that are no longer OA are excluded with reason.

## Testing

- Unit tests for citation extractor: DOI match, Cochrane review ID match, first-author+year fallback match, and no-match handling.
- Cox model output validated against R `survival::coxph` on a 20-MA fixture subset, tolerance 1e-6.
- Schoenfeld PH test regression-tested; RMST path with explicit `tau*` exercised end-to-end on a synthetic PH-violating fixture.
- Kaplan-Meier point estimates validated against R `survival::survfit`, tolerance 1e-6.
- Edge cases:
  - MAs with no adoption event by latest edition (right-censored); KM and Cox must handle without silent row drop.
  - MAs adopted in the edition immediately after publication (interval-censoring sensitivity analysis).
  - Guidelines with a single historical edition in the archive (excluded with reason; reason captured in manifest).
  - Ties in event time (guideline published same month as another) broken by Efron's method; tested explicitly.
- Hand-audit 50-citation subsample per society; accuracy >= 0.85 per society gates that society's headline lag figure.
- Schema check on Cochrane export columns and edition manifest; fail-closed on drift.
- Numerical baselines pinned for KM medians, Cox HRs, and RMST differences against the 20-MA fixture.

## Failure-mode guards

- Recommendation-class phrasing differs by society -> per-society parsing rules; hand-audit gate 0.85 per society; below-bar societies blocked from headline.
- Edition-cycle asymmetry (ESC every ~5 years vs NICE continuously updated) -> stratified KM by society; interval-censoring sensitivity in manuscript appendix.
- PICO-to-rec matching for endpoint C is the largest measurement-error surface -> remains the secondary endpoint; accuracy reported per society.
- MCE threshold table (`sap/mce_thresholds.yml`) is pre-registered; any post-hoc change requires a dated amendment and is flagged in the manuscript.
- Advanced-stats rules honoured: Schoenfeld PH check mandatory before interpreting any single Cox HR; under non-PH, report RMST with stated `tau*` per outcome or interval-specific HRs; KM confidence interval uses complementary log-log transform, not plain; any ratio effects pooled from underlying MA data are handled on log scale.
- TruthCert on all pooled claims (median lag, Cox HRs, KM differences, per-society lag). HMAC key sourced only from `TRUTHCERT_HMAC_KEY` env var; never from the bundle; `hmac.compare_digest` for MAC comparison; no placeholder signatures.
- Memory != evidence: MCE threshold table, cohort manifest, and guideline edition manifest are version-controlled artifacts.
- No hardcoded local paths in dashboard or E156 PDFs. Windows candidate-root pattern for local PDF archives.

## Shipping artifacts

- BMJ/JAMA Analysis manuscript (`paper/bmj-analysis.md`) featuring KM curves, Cox forest plot, per-society median lag, and RMST difference where PH is violated.
- E156 micro-paper body + `e156-submission/` + rewrite-workbook entry (CURRENT BODY only; YOUR REWRITE empty; SUBMITTED `[ ]`).
- Static GitHub Pages dashboard at `index.html`: KM curves stratified by society, Cox forest plot, per-society lag tables, per-MA adoption cards. Offline-first, no CDN.
- TruthCert bundle covering all pooled claims.
- Reusable `data/adoption_lag.csv`, consumed read-only by downstream projects.
- `INDEX.md` + `rewrite-workbook.txt` entries (count incremented).

## Timeline

~6-7 weeks. Guideline archive parsing is the rate-limiter.

## Dependencies / prereqs (Task 0 fail-closed gate)

Before the implementation plan runs a single test:

- `python C:\ProjectIndex\reconcile_counts.py` exits 0 (registry sane).
- Cochrane CDSR metadata export path resolves (same pinned version as Proto-Pub-Drift and RetractRipple).
- ESC / ACC-AHA / NICE cardiology guideline PDF archive directories resolve and contain edition history back to 2010.
- `C:\Program Files\R\R-4.5.2\bin\Rscript.exe` resolves and `library(survival)` plus `library(metafor)` both load.
- `TRUTHCERT_HMAC_KEY` env var set.
- `sap/mce_thresholds.yml` and `sap/covariates.yml` present and committed.

Any missing prereq fails closed with a specific user-action list.

## Out of scope for this spec

- Non-cardiology societies (NICE oncology, USPSTF, etc.) - Phase 2.
- Landmark non-Cochrane MAs (NEJM/JAMA/Lancet/BMJ/EHJ/JACC/Circulation MAs) - Phase 2.
- Causal attribution of lag to committee dynamics, COI, or individual members.
- Altmetric / media-attention covariate.
- Guideline editions before 2010.
- MAs not crossing the pre-specified clinical effect threshold (by design of the trigger set).
