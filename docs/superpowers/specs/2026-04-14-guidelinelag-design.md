# GuidelineLag — Design Specification

**Date:** 2026-04-14
**Author:** Mahmood Ahmad (Royal Free Hospital / Tahir Heart Institute)
**Status:** Design — pending user review
**Targets:** E156 micro-paper + BMJ Analysis
**Prior art:** `C:\NICECardiology\` (2 drug classes, 6 bodies, LIVE); `C:\Projects\cardio-guideline-discordance-audit\` (distinct question: evidence-strength discordance, not temporal lag)

---

## 1. Problem statement

For high-quality cardiology meta-analyses, how long does it take for pooled effects that cross a clinically meaningful threshold to alter recommendation class in major guideline documents?

"Lag" is quantified per (meta-analysis, guideline body) pair as the months elapsed between:
- **T1 — threshold-cross year:** earliest year in which the cumulative Cochrane meta-analysis (adding studies in publication-year order) has an upper 95% CI bound of the pooled hazard ratio below the class-specific threshold.
- **T2 — first L4 citation:** publication date of the first guideline edition from that body in which the drug/indication is at canonical rec-level L4 (strong-recommend-for).

Primary endpoint: **median lag-to-L4 (months), stratified by society.**

Secondary endpoint: **lag-to-cite** — months to first guideline edition whose reference list contains the Cochrane DOI, regardless of whether the rec-table mentions the drug/indication.

**Lag arithmetic:** threshold-cross is year-granularity (no per-month data inside cumulative MAs); guideline editions have a publication date. Lag = (edition publication date) − (July 1 of threshold year), expressed in months rounded to the nearest integer.

**Pooling model:** REML random-effects for k ≥ 5; Paule-Mandel for k < 5 (per advanced-stats.md rule: never DL for k < 10). Hartung-Knapp adjustment with Q-floor `max(1, Q/(k-1))` to prevent HKSJ CI narrowing below DL.

---

## 2. Scope

### In scope
- **10 cardiology drug classes** (see §6 for threshold config):
  1. SGLT2i for HFrEF (DAPA-HF, EMPEROR-Reduced)
  2. SGLT2i for HFpEF (EMPEROR-Preserved, DELIVER)
  3. PCSK9i post-ACS (FOURIER, ODYSSEY)
  4. Icosapent ethyl (REDUCE-IT)
  5. Finerenone HF (FINEARTS-HF)
  6. ARNI / sacubitril-valsartan (PARADIGM-HF)
  7. Ticagrelor post-ACS (PLATO)
  8. GLP-1 RA CV benefit (LEADER, SUSTAIN-6, REWIND)
  9. Colchicine CCS (LoDoCo2, COLCOT)
  10. AF ablation first-line (EAST-AFNET4, STOP-AF, EARLY-AF)

- **4 guideline bodies:** ESC, ACC/AHA (treated as a single joint body per published guidelines), NICE, CCS.
- **Editions:** every edition of the relevant guideline published since the first pivotal trial for each class.
- **MA feedstock:** `C:\Projects\Pairwise70\` (501 Cochrane MAs, one .rda per review) filtered to the cardiology subset.
- **Outputs:** lag dataset (CSV), single-file HTML dashboard, E156 article, BMJ Analysis manuscript draft, TruthCert bundle.

### Non-goals
- Non-cardiology therapeutic areas (deferred).
- Devices / structural procedures (TAVI, MitraClip, renal denervation, LAA closure) — different adoption dynamics, deferred.
- Causal attribution of lag to any specific society process (cost-effectiveness deliberations, committee composition, etc.) — this is a descriptive atlas, not a mechanistic paper.
- Patient-level outcomes of delayed adoption (a different paper).

---

## 3. Architecture overview

**Language split:** Python for orchestration, parsing, matching, output; R for meta-analytic pooling via `metafor` (passes advanced-stats.md validation rules at tolerance 1e-6). Python ↔ R crosses via `Rscript` subprocess calls (not rpy2 — Windows fragility).

**Storage:** all intermediate artifacts are CSV or YAML. No database. Every row is auditable end-to-end.

**Directory layout:**

```
C:\Projects\GuidelineLag\
├── data\
│   ├── pairwise70_cardio\      # filtered .rda + cumulative CSVs
│   ├── guidelines\             # source PDFs, one subfolder per body
│   └── derived\                # threshold dates, citations, lag dataset
├── src\
│   ├── python\                 # enricher, detectors, matchers, composer
│   └── R\                      # cumulative pooler (metafor)
├── outputs\
│   ├── dashboard\              # index.html, assets (offline, no CDN)
│   ├── e156\                   # article.json, paper.html
│   ├── manuscript\             # BMJ Analysis draft, figures
│   └── truthcert\              # HMAC-signed bundle
├── tests\
│   ├── baselines\              # numerical baselines (frozen lag_dataset)
│   ├── integration\
│   └── unit\
├── protocol\                   # thresholds.yaml, taxonomy.yaml, manifests
└── docs\
```

---

## 4. Components

Each component has one job and a typed contract with the next. Schema mismatch raises; silent-failure sentinels are forbidden (2026-04-14 lesson).

| Component | File | Inputs | Outputs |
|---|---|---|---|
| CD topic enricher | `src/python/cd_topic_enricher.py` | 501 CD IDs from Pairwise70, Cochrane API (cached) | `data/derived/cd_topics.csv` (cd_id, title, mesh_terms, is_cardio, cardio_class) |
| Cumulative pooler | `src/R/cumulative_pooler.R` | .rda file + per-class config (outcome column, metric) | `data/pairwise70_cardio/{cd_id}_cumulative.csv` (year, k, effect, se, ci_lo, ci_hi, tau2) |
| Threshold detector | `src/python/threshold_detector.py` | cumulative CSV + `protocol/thresholds.yaml` | `data/derived/ma_threshold_dates.csv` (cd_id, class, threshold_year, pooled_effect, pooled_uci) |
| Guideline corpus manifest | `src/python/guideline_corpus.py` | manual inventory | `data/derived/guideline_editions.csv` (body, topic, edition_year, pdf_path, status) |
| Guideline parser | `src/python/guideline_parser.py` | edition PDFs | `data/derived/{body}_{edition}_refs.csv`, `{body}_{edition}_recs.csv` |
| Citation matcher | `src/python/citation_matcher.py` | MA DOIs + ref CSVs | `data/derived/first_citation.csv` (cd_id, body, first_citing_edition, citing_date, rec_level) |
| Lag calculator | `src/python/lag_calculator.py` | threshold dates + citation dates + rec tables | `data/derived/lag_dataset.csv` |
| Dashboard builder | `src/python/build_dashboard.py` | lag dataset | `outputs/dashboard/index.html` |
| E156 composer | `src/python/e156_compose.py` | lag dataset + summary stats | `outputs/e156/article.json`, `paper.html` |
| BMJ Analysis draft | `src/python/build_manuscript.py` | lag dataset + figure assets | `outputs/manuscript/bmj_analysis.md` |
| TruthCert signer | `src/python/truthcert_sign.py` | lag dataset + thresholds.yaml + manifest hashes + `TRUTHCERT_HMAC_KEY` env | `outputs/truthcert/bundle.json` |

### Data flow (one-way)

```
Pairwise70/*.rda
        │
        ▼
 cd_topic_enricher ──► cardio MA subset (N ≈ 30-80 expected)
        │
        ▼
 cumulative_pooler (R/metafor)
        │
        ▼
 threshold_detector (uniform 0.90 UCI rule) ──► ma_threshold_dates.csv
                                                        │
 guidelines/*.pdf ──► guideline_parser ──► refs + recs ─┤
                                                        ▼
                                               citation_matcher
                                                        │
                                                        ▼
                                               lag_calculator ──► lag_dataset.csv
                                                        │
      ┌─────────────────┬──────────────────┬────────────┼──────────────────┐
      ▼                 ▼                  ▼            ▼                  ▼
  dashboard        e156 article      manuscript    TruthCert         numerical baseline
```

---

## 5. Canonical rec-class taxonomy

Societies use incompatible rubrics. Canonical 5-level scale mapping (`protocol/taxonomy.yaml`):

| Canonical | ESC | ACC/AHA | NICE | CCS |
|---|---|---|---|---|
| **L4 — Strong for** | Class I | Class I | "Offer" | Strong-for |
| **L3 — Weak for** | Class IIa | Class IIa | "Consider" | Weak-for |
| **L2 — May consider** | Class IIb | Class IIb | (no direct equivalent; coded as not applicable when absent) | Conditional |
| **L1 — Not recommended** | Class III (no benefit) | Class III (no benefit) | "Do not routinely offer" | Weak-against |
| **L0 — Recommend against** | Class III (harm) | Class III (harm) | "Do not offer" | Strong-against |

**Endpoints:**
- **Lag-to-L4** (primary): threshold-cross year → first edition with the drug/indication at L4.
- **Lag-to-cite** (secondary): threshold-cross year → first edition whose reference list contains the Cochrane DOI (regardless of rec-table status). Difference between the two metrics captures the "cited but not acted on" gap.

Mapping is deterministic and unit-tested (`tests/unit/test_taxonomy_mapper.py`).

---

## 6. Pre-registered thresholds

**Committed to `protocol/thresholds.yaml` BEFORE any threshold dates are computed.** Pre-registration is the anti-p-hacking gate; BMJ Analysis reviewers will ask for it explicitly.

**Unified rule:** for every class, threshold-cross occurs in the earliest Study.year at which the cumulative pooled hazard ratio has **upper 95% CI bound < 0.90** on the Cochrane-standard composite outcome. Rationale: 0.90 UCI is the NICE/ESC clinical-significance anchor; applying it uniformly removes reviewer debate about class-bespoke anchors.

| Class | Outcome (Cochrane-standard) | Metric | UCI threshold |
|---|---|---|---|
| SGLT2i HFrEF | CV death or HF hospitalization | HR | < 0.90 |
| SGLT2i HFpEF | HF hospitalization | HR | < 0.90 |
| PCSK9i | 3-point MACE | HR | < 0.90 |
| Icosapent | MACE | HR | < 0.90 |
| Finerenone HF | CV death or HF worsening | HR | < 0.90 |
| ARNI | CV death or HF hospitalization | HR | < 0.90 |
| Ticagrelor | CV death/MI/stroke | HR | < 0.90 |
| GLP-1 RA CV | 3-point MACE | HR | < 0.90 |
| Colchicine CCS | CV death/MI/stroke | HR | < 0.90 |
| AF ablation first-line | CV composite (death/stroke/HF hosp, EAST-AFNET4 framing — **not** arrhythmia recurrence) | HR | < 0.90 |

If the Cochrane MA for a given class never crosses the threshold, that class's lag-to-L4 is reported as **"not yet reached"** and contributes to the league table as a right-censored observation (not dropped).

---

## 7. Testing strategy

**Integration tests first** (per testing.md multi-component rule):

- `tests/integration/test_e2e_sglt2i_hfref.py` — **anchor test.** Full pipeline for SGLT2i HFrEF must reproduce NICECardiology's finding: NICE ranks last among ESC/ACC-AHA/NICE/CCS for this class. If this test breaks, the pipeline is wrong. Runs on committed Pairwise70 snapshot + committed guideline manifest.
- `tests/integration/test_contract_cumulative_pooler.py` — R metafor output schema contract; Python threshold detector raises `KeyError` with expected-vs-received diff on schema mismatch.
- `tests/integration/test_contract_guideline_parser.py` — PDF parser must return `{refs: [...], recs: [...]}` with typed fields; never silent-return on parse failure.

**Unit tests:**

- `tests/unit/test_cumulative_pool.R` — agreement with `metafor::rma()` on ≥ 3 Pairwise70 datasets, tolerance 1e-6.
- `tests/unit/test_threshold_detector.py` — synthetic effect trajectories with known crossing years; boundary cases at exactly UCI = 0.90 (excluded by strict `<`).
- `tests/unit/test_taxonomy_mapper.py` — ESC/ACC-AHA/NICE/CCS rec strings map to L0-L4 deterministically; unmapped strings raise.
- `tests/unit/test_citation_matcher.py` — exact DOI, normalized DOI (strip trailing dots, strip `.pubN`), fuzzy author-year fallback.
- `tests/unit/test_lag_calculator.py` — months arithmetic across year boundaries; right-censored case handled.

**Numerical baseline (committed):**

- `tests/baselines/lag_dataset_frozen.csv` — full lag output on the committed Pairwise70 snapshot + guideline manifest.
- `tests/baselines/lag_dataset_sha256.txt` — hash of frozen dataset.
- Any pipeline change that moves a number triggers baseline review; regression gate is 0% drift (not a 2% tolerance — this is a meta-research claim, not a simulation).

**Preflight (blocks test run):**

- `Rscript --version` ≥ 4.5.2
- `import metafor_wrapper` resolves
- `C:\Projects\Pairwise70\data\` has ≥ 500 .rda files
- `data/guidelines/manifest.csv` has a row per (body, topic) pair in scope

**Bounded verify-fix-rerun loop:** per workflow.md, cap at 3 rerun attempts per failure; log unresolved blockers to `STUCK_FAILURES.md`.

---

## 8. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| PDF parsing brittleness across 4 societies | High | Manual reference-list extraction is the default fallback. 160 PDFs × ~30s each = ~80 min. Column `guideline_parse_mode: auto\|manual` records which pathway. |
| Cochrane API / MeSH enrichment fails for CD→topic | Medium | Offline override via `protocol/cd_manual_cardio.csv`; cache all API calls. |
| Cochrane not first-to-threshold (Lancet/JAMA/NEJM MA beat it) | Certain for some classes | Acknowledged in paper — this is the Cochrane-confirmation lens by design. Sensitivity column in lag dataset records earliest-known non-Cochrane MA year if available. |
| Guideline edition paywalled or missing | Medium | `guideline_manifest.csv` column `status: sourced\|missing\|paywall`; missing editions drop the row and are reported in the PRISMA-style flow diagram. |
| Threshold config changes mid-analysis | Low (preventable) | `thresholds.yaml` committed to git BEFORE any threshold dates computed; TruthCert bundles the hash. |
| Multiple Cochrane MAs cover same topic | Medium | Use most recent `.pubN` version; log earlier versions' threshold years as sensitivity rows. |
| Taxonomy mismatch (NICE has no direct L2 equivalent) | Acknowledged | L2 coded as `NA` for NICE rows in the rec-table; does not affect primary (L4) or secondary (cite) endpoints. |
| Pairwise70 filter yields fewer than expected cardiology MAs | Medium | Fallback: supplement with manually-curated non-Cochrane MA entries using the same threshold rule. Flag source in `cd_id` column prefix (`CD*` vs `MAN*`). |

---

## 9. Outputs

### 9.1 Dashboard (`outputs/dashboard/index.html`)

Single-file offline HTML. No CDN (per html-apps.md). Three views:
1. **Heatmap:** class (rows) × society (cols), cell = lag-to-L4 in months, color-scaled. Right-censored cells marked "NYR" (not yet reached).
2. **League table:** societies sorted by median lag-to-L4 across all classes; secondary sort by count of L4-reached classes.
3. **Per-class drill-down:** timeline per class showing threshold-cross year, each guideline edition as a dot colored by rec-level L0-L4, with lag arrows.

No hardcoded local paths (per code-quality lesson). Fully self-contained.

### 9.2 E156 paper (`outputs/e156/article.json` + `paper.html`)

7 sentences, ≤156 words. One estimand: **median lag-to-L4 (months)**. One stratifier: **society**. Follows `C:\E156\docs\E156_v0.2_SPEC.md`.

### 9.3 BMJ Analysis manuscript (`outputs/manuscript/bmj_analysis.md`)

Target ~1500 words. Thesis: *"Across 10 cardiology drug classes, Cochrane-confirmed evidence takes a median of X months to reach strong-recommend status, with Y-fold variation across societies — NICE is the slowest."*

Figures:
- Fig 1: heatmap (class × society).
- Fig 2: league table.
- Fig 3: case-study timeline (default SGLT2i HFpEF; pick the class with the most dramatic spread after the data lands).

### 9.4 TruthCert bundle (`outputs/truthcert/bundle.json`)

HMAC-SHA256-signed artifact. Key from `TRUTHCERT_HMAC_KEY` env var (fail closed if missing; never default to a placeholder per crypto lesson 2026-04-14). Contents:
- SHA-256 of `lag_dataset.csv`
- SHA-256 of `protocol/thresholds.yaml`
- SHA-256 of `protocol/taxonomy.yaml`
- Pairwise70 snapshot date + SHA-256 of `cd_topics.csv`
- SHA-256 of `guideline_editions.csv`
- ISO timestamp of bundle creation
- Git commit hash of the pipeline

### 9.5 Deployment artifacts

Per E156 pipeline rules:
- `README.md` — claims aligned with actual implementation; no marketing descriptors ("Complete", "Global", "Full").
- `E156-PROTOCOL.md` — project name, date, body, dashboard link.
- GitHub push via `C:\Users\user\push_all_repos.py`.
- GitHub Pages enabled for dashboard.
- `INDEX.md` entry updated; `rewrite-workbook.txt` entry added with empty `YOUR REWRITE` and `SUBMITTED: [ ]`.
- `restart-manifest.json` updated; `reconcile_counts.py` must pass.

---

## 10. Static vs dynamic disclosure

Per CLAUDE.md rule — explicit enumeration of what is static (fixed at design time) vs dynamic (computed from data).

| Item | Static / Dynamic | Source |
|---|---|---|
| List of 10 drug classes | **Static** (protocol) | This design doc, §2 |
| Threshold rule (UCI < 0.90) | **Static** (protocol) | §6 |
| Rec-class taxonomy mapping | **Static** (protocol) | §5 |
| List of 4 guideline bodies | **Static** (protocol) | §2 |
| Per-class Cochrane-standard outcome | **Static** (protocol) | §6 |
| Threshold-cross year per class | **Dynamic** | Cumulative pool of Pairwise70 studies |
| Pooled HR + CI per year | **Dynamic** | metafor on Pairwise70 data |
| First citing edition per (MA, body) | **Dynamic** | Guideline ref-list parsing |
| First L4 edition per (MA, body) | **Dynamic** | Guideline rec-table parsing |
| Lag values | **Dynamic** | Computed arithmetic |
| Heatmap colors | **Dynamic** | lag_dataset.csv values |
| League table rank | **Dynamic** | Median aggregation |
| "NICE is slowest" claim in manuscript | **Dynamic** (hypothesis until data confirms) | Must be verified against produced lag_dataset before the manuscript draft is finalized. Default thesis is **data-contingent**. |

---

## 11. Definition of done

The project is complete when:

1. All 10 classes have a lag-to-L4 row (or "not yet reached") for all 4 societies (40 rows, with acknowledged dropouts).
2. Integration test `test_e2e_sglt2i_hfref.py` passes, reproducing NICECardiology's finding.
3. All unit tests pass; numerical baseline matches.
4. `reconcile_counts.py` passes with GuidelineLag added to the portfolio.
5. Dashboard renders with no broken sections, no placeholder tokens, no hardcoded local paths.
6. E156 article is 7 sentences, ≤156 words, passes E156 validator.
7. BMJ Analysis draft cites every number back to lag_dataset row.
8. TruthCert bundle verifies with `TRUTHCERT_HMAC_KEY`.
9. Published to GitHub + Pages enabled; INDEX.md, rewrite-workbook.txt, restart-manifest.json updated consistently.
10. `YOUR REWRITE` section in workbook left empty (sacrosanct).

---

## 12. Open questions

None as of 2026-04-14. All major design decisions locked in Sections 2-6 above.

---

## 13. Non-goals reminder

To prevent scope creep during implementation:

- No device/structural procedures.
- No non-cardiology areas.
- No causal attribution of lag.
- No patient-outcome modelling of delayed adoption.
- No real-time "live" updating of lag values — this is a point-in-time atlas.
- No Gemini-style marketing descriptors in outputs ("Complete", "Full", "Global") per no-marketing rule.
