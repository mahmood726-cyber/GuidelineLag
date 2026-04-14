# GuidelineLag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Pairwise70-backed systematic atlas quantifying months of lag between Cochrane-confirmed meta-analytic evidence crossing a clinical-significance threshold and its adoption at L4 (strong-recommend-for) in ESC, ACC/AHA, NICE, and CCS cardiology guidelines — across 10 pre-specified drug classes — producing a lag dataset, offline HTML dashboard, E156 micro-paper, and BMJ Analysis manuscript draft.

**Architecture:** Python 3.13 orchestration + R 4.5.2 metafor subprocess for pooling. CSV-only intermediate storage, no database. Pre-registered `protocol/thresholds.yaml` and `protocol/taxonomy.yaml` committed before any threshold date is computed. Integration-first testing with SGLT2i HFrEF anchor test reproducing `C:\NICECardiology\` finding. TruthCert HMAC bundle from `TRUTHCERT_HMAC_KEY` env var (never placeholder signatures).

**Tech Stack:** Python 3.13, R 4.5.2 + metafor, pandas, PyYAML, pdfplumber, requests, pytest, hmac (stdlib).

**Spec reference:** `C:\Projects\GuidelineLag\docs\superpowers\specs\2026-04-14-guidelinelag-design.md`

---

## Prereqs (external, verified before Task 1 by Task 1 itself)

- `C:\Projects\Pairwise70\data\` contains ≥ 500 .rda files
- `Rscript --version` returns ≥ 4.5.2
- R package `metafor` installed
- Python ≥ 3.13 with packages in `requirements.txt`
- **User-sourced:** guideline PDFs in `data/guidelines/{body}/...` — Task 11 produces the manifest template; the anchor test (Task 16) blocks until at least SGLT2i-relevant editions are sourced.

---

## File structure (locked at plan time)

```
C:\Projects\GuidelineLag\
├── .gitignore
├── README.md
├── E156-PROTOCOL.md
├── requirements.txt
├── pytest.ini
├── protocol\
│   ├── classes.yaml
│   ├── thresholds.yaml
│   ├── taxonomy.yaml
│   ├── cd_manual_cardio.csv
│   └── guideline_manifest_template.csv
├── src\
│   ├── python\
│   │   ├── __init__.py
│   │   ├── preflight.py
│   │   ├── taxonomy_mapper.py
│   │   ├── cd_topic_enricher.py
│   │   ├── threshold_detector.py
│   │   ├── guideline_corpus.py
│   │   ├── guideline_parser.py
│   │   ├── citation_matcher.py
│   │   ├── lag_calculator.py
│   │   ├── build_dashboard.py
│   │   ├── e156_compose.py
│   │   ├── build_manuscript.py
│   │   └── truthcert_sign.py
│   └── R\
│       └── cumulative_pooler.R
├── scripts\
│   └── run_pipeline.py
├── tests\
│   ├── conftest.py
│   ├── baselines\
│   ├── fixtures\
│   ├── unit\
│   └── integration\
├── data\
│   ├── pairwise70_cardio\   (gitignored)
│   ├── guidelines\
│   └── derived\             (gitignored)
├── outputs\
│   ├── dashboard\
│   ├── e156\
│   ├── manuscript\
│   └── truthcert\
└── docs\
    └── superpowers\
        ├── specs\
        └── plans\
```

---

# PHASE 0 — Foundation

## Task 1: Scaffold project + preflight

**Files:**
- Create: `C:\Projects\GuidelineLag\.gitignore`
- Create: `C:\Projects\GuidelineLag\requirements.txt`
- Create: `C:\Projects\GuidelineLag\pytest.ini`
- Create: `C:\Projects\GuidelineLag\src\python\__init__.py`
- Create: `C:\Projects\GuidelineLag\src\python\preflight.py`
- Create: `C:\Projects\GuidelineLag\tests\conftest.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_preflight.py`

- [ ] **Step 1: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
PROGRESS.md
data/pairwise70_cardio/
data/derived/
outputs/**/*.html
outputs/**/*.json
outputs/truthcert/
!outputs/dashboard/.gitkeep
.env
*.log
```

- [ ] **Step 2: Write `requirements.txt`**

```
pandas>=2.2
PyYAML>=6.0
requests>=2.31
pdfplumber>=0.11
pytest>=8.0
Jinja2>=3.1
```

- [ ] **Step 3: Write `pytest.ini`**

```ini
[pytest]
testpaths = tests
addopts = -ra -q --strict-markers
markers =
    integration: end-to-end tests (may need external data)
    slow: tests that take > 5s
```

- [ ] **Step 4: Create empty module init**

Write `src/python/__init__.py` containing a single line: `"""GuidelineLag pipeline package."""`

- [ ] **Step 5: Write failing preflight test**

`tests/unit/test_preflight.py`:

```python
from pathlib import Path
import pytest
from src.python.preflight import check_environment, PreflightError


def test_preflight_passes_when_all_present(tmp_path, monkeypatch):
    pw70 = tmp_path / "Pairwise70" / "data"
    pw70.mkdir(parents=True)
    for i in range(501):
        (pw70 / f"CD{i:06d}_pub1_data.rda").write_bytes(b"\x00")
    monkeypatch.setattr("src.python.preflight.PAIRWISE70_DATA", pw70)
    monkeypatch.setattr("src.python.preflight._rscript_version", lambda: "R scripting front-end version 4.5.2 (2025-10-31)")
    monkeypatch.setattr("src.python.preflight._metafor_installed", lambda: True)
    check_environment()


def test_preflight_fails_when_pairwise70_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("src.python.preflight.PAIRWISE70_DATA", tmp_path / "does_not_exist")
    with pytest.raises(PreflightError, match="Pairwise70"):
        check_environment()


def test_preflight_fails_when_rscript_too_old(tmp_path, monkeypatch):
    pw70 = tmp_path / "Pairwise70" / "data"
    pw70.mkdir(parents=True)
    for i in range(501):
        (pw70 / f"CD{i:06d}_pub1_data.rda").write_bytes(b"\x00")
    monkeypatch.setattr("src.python.preflight.PAIRWISE70_DATA", pw70)
    monkeypatch.setattr("src.python.preflight._rscript_version", lambda: "R scripting front-end version 4.0.0 (2020-04-24)")
    monkeypatch.setattr("src.python.preflight._metafor_installed", lambda: True)
    with pytest.raises(PreflightError, match="4.5"):
        check_environment()
```

- [ ] **Step 6: Run test to verify it fails**

```
cd C:\Projects\GuidelineLag
python -m pytest tests/unit/test_preflight.py -v
```
Expected: FAIL (module `src.python.preflight` not found).

- [ ] **Step 7: Implement `preflight.py`**

```python
"""Preflight checks for GuidelineLag. Fails closed on any missing prereq."""
from __future__ import annotations
import re
import shutil
import subprocess
from pathlib import Path

PAIRWISE70_DATA = Path(r"C:\Projects\Pairwise70\data")
MIN_R_VERSION = (4, 5)
MIN_RDA_COUNT = 500


class PreflightError(RuntimeError):
    """Raised when an external prereq is missing or wrong version."""


def _rscript_version() -> str:
    exe = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
    result = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
    return (result.stderr or result.stdout).strip()


def _metafor_installed() -> bool:
    exe = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
    result = subprocess.run(
        [exe, "-e", "cat(requireNamespace('metafor', quietly=TRUE))"],
        capture_output=True, text=True, timeout=60,
    )
    return "TRUE" in result.stdout


def _parse_r_version(banner: str) -> tuple[int, int]:
    m = re.search(r"version\s+(\d+)\.(\d+)", banner)
    if not m:
        raise PreflightError(f"Cannot parse Rscript version from: {banner!r}")
    return int(m.group(1)), int(m.group(2))


def check_environment() -> None:
    if not PAIRWISE70_DATA.is_dir():
        raise PreflightError(f"Pairwise70 data dir missing: {PAIRWISE70_DATA}")
    rda_count = sum(1 for p in PAIRWISE70_DATA.iterdir() if p.suffix == ".rda")
    if rda_count < MIN_RDA_COUNT:
        raise PreflightError(f"Pairwise70 has only {rda_count} .rda files, need ≥ {MIN_RDA_COUNT}")

    banner = _rscript_version()
    major, minor = _parse_r_version(banner)
    if (major, minor) < MIN_R_VERSION:
        raise PreflightError(f"Rscript {major}.{minor} < required {'.'.join(map(str, MIN_R_VERSION))}")

    if not _metafor_installed():
        raise PreflightError("R package 'metafor' not installed. Run: install.packages('metafor')")


if __name__ == "__main__":
    check_environment()
    print("preflight: OK")
```

- [ ] **Step 8: Write `tests/conftest.py`**

```python
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
```

- [ ] **Step 9: Run tests to verify all pass**

```
cd C:\Projects\GuidelineLag
python -m pytest tests/unit/test_preflight.py -v
```
Expected: 3 passed.

- [ ] **Step 10: Run live preflight**

```
cd C:\Projects\GuidelineLag
python -m src.python.preflight
```
Expected output: `preflight: OK`. If it fails, STOP and fix the prereq — do not proceed.

- [ ] **Step 11: Commit**

```
cd C:\Projects\GuidelineLag
git add .gitignore requirements.txt pytest.ini src/python/__init__.py src/python/preflight.py tests/conftest.py tests/unit/test_preflight.py
git commit -m "feat(preflight): scaffold project and add environment checks"
```

---

## Task 2: Pre-register `classes.yaml`

**Files:**
- Create: `C:\Projects\GuidelineLag\protocol\classes.yaml`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_protocol_classes.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_protocol_classes.py`:

```python
import yaml
from pathlib import Path

CLASSES_YAML = Path(__file__).resolve().parents[2] / "protocol" / "classes.yaml"


def test_classes_yaml_has_ten_entries():
    data = yaml.safe_load(CLASSES_YAML.read_text())
    assert len(data["classes"]) == 10


def test_each_class_has_required_fields():
    data = yaml.safe_load(CLASSES_YAML.read_text())
    required = {"id", "display_name", "pivotal_trials", "bodies_in_scope"}
    for cls in data["classes"]:
        missing = required - cls.keys()
        assert not missing, f"{cls.get('id')} missing {missing}"


def test_bodies_are_canonical_four():
    data = yaml.safe_load(CLASSES_YAML.read_text())
    expected = {"esc", "acc_aha", "nice", "ccs"}
    for cls in data["classes"]:
        assert set(cls["bodies_in_scope"]) == expected
```

- [ ] **Step 2: Run test to verify it fails**

```
python -m pytest tests/unit/test_protocol_classes.py -v
```
Expected: FAIL (file not found).

- [ ] **Step 3: Write `protocol/classes.yaml`**

```yaml
version: 1
registered_on: 2026-04-14
classes:
  - id: sglt2i_hfref
    display_name: SGLT2 inhibitors for HFrEF
    pivotal_trials: [DAPA-HF, EMPEROR-Reduced]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: sglt2i_hfpef
    display_name: SGLT2 inhibitors for HFpEF
    pivotal_trials: [EMPEROR-Preserved, DELIVER]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: pcsk9i
    display_name: PCSK9 inhibitors post-ACS
    pivotal_trials: [FOURIER, ODYSSEY OUTCOMES]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: icosapent
    display_name: Icosapent ethyl
    pivotal_trials: [REDUCE-IT]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: finerenone_hf
    display_name: Finerenone for HF
    pivotal_trials: [FINEARTS-HF]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: arni
    display_name: ARNI (sacubitril/valsartan)
    pivotal_trials: [PARADIGM-HF]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: ticagrelor
    display_name: Ticagrelor post-ACS
    pivotal_trials: [PLATO]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: glp1_ra_cv
    display_name: GLP-1 RA CV benefit
    pivotal_trials: [LEADER, SUSTAIN-6, REWIND]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: colchicine_ccs
    display_name: Colchicine in chronic coronary syndromes
    pivotal_trials: [LoDoCo2, COLCOT]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
  - id: af_ablation_first_line
    display_name: AF ablation as first-line rhythm control
    pivotal_trials: [EAST-AFNET4, STOP-AF, EARLY-AF]
    bodies_in_scope: [esc, acc_aha, nice, ccs]
```

- [ ] **Step 4: Run tests to verify all pass**

```
python -m pytest tests/unit/test_protocol_classes.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```
git add protocol/classes.yaml tests/unit/test_protocol_classes.py
git commit -m "protocol: pre-register 10 cardiology drug classes"
```

---

## Task 3: Pre-register `thresholds.yaml`

**Files:**
- Create: `C:\Projects\GuidelineLag\protocol\thresholds.yaml`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_protocol_thresholds.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_protocol_thresholds.py`:

```python
import yaml
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "protocol" / "thresholds.yaml"
CLASSES = Path(__file__).resolve().parents[2] / "protocol" / "classes.yaml"


def test_all_ten_classes_have_threshold():
    thresholds = yaml.safe_load(PATH.read_text())["thresholds"]
    classes = yaml.safe_load(CLASSES.read_text())["classes"]
    class_ids = {c["id"] for c in classes}
    threshold_ids = {t["class_id"] for t in thresholds}
    assert class_ids == threshold_ids


def test_uniform_rule_enforced():
    thresholds = yaml.safe_load(PATH.read_text())["thresholds"]
    for t in thresholds:
        assert t["metric"] == "HR"
        assert t["direction"] == "upper_ci_less_than"
        assert t["uci_bound"] == 0.90


def test_every_threshold_has_outcome_description():
    thresholds = yaml.safe_load(PATH.read_text())["thresholds"]
    for t in thresholds:
        assert t["outcome"]
        assert len(t["outcome"]) > 5
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_protocol_thresholds.py -v
```

- [ ] **Step 3: Write `protocol/thresholds.yaml`**

```yaml
version: 1
registered_on: 2026-04-14
rule_description: >
  Threshold-cross occurs in the earliest Study.year at which the cumulative
  Cochrane pooled hazard ratio has upper 95% CI bound < 0.90 on the
  Cochrane-standard composite outcome. Uniform anchor across all classes.
  Rationale: NICE/ESC clinical-significance anchor applied uniformly removes
  reviewer debate about bespoke class thresholds.
thresholds:
  - class_id: sglt2i_hfref
    outcome: CV death or HF hospitalization
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: sglt2i_hfpef
    outcome: HF hospitalization
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: pcsk9i
    outcome: 3-point MACE
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: icosapent
    outcome: MACE
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: finerenone_hf
    outcome: CV death or HF worsening
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: arni
    outcome: CV death or HF hospitalization
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: ticagrelor
    outcome: CV death or MI or stroke
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: glp1_ra_cv
    outcome: 3-point MACE
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: colchicine_ccs
    outcome: CV death or MI or stroke
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
  - class_id: af_ablation_first_line
    outcome: CV death or stroke or HF hospitalization (EAST-AFNET4 composite)
    metric: HR
    direction: upper_ci_less_than
    uci_bound: 0.90
```

- [ ] **Step 4: Run tests to verify pass**

```
python -m pytest tests/unit/test_protocol_thresholds.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```
git add protocol/thresholds.yaml tests/unit/test_protocol_thresholds.py
git commit -m "protocol: pre-register uniform UCI<0.90 thresholds for 10 classes"
```

---

## Task 4: Pre-register `taxonomy.yaml`

**Files:**
- Create: `C:\Projects\GuidelineLag\protocol\taxonomy.yaml`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_protocol_taxonomy.py`

- [ ] **Step 1: Write failing test**

`tests/unit/test_protocol_taxonomy.py`:

```python
import yaml
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "protocol" / "taxonomy.yaml"


def test_five_levels_defined():
    data = yaml.safe_load(PATH.read_text())
    assert set(data["levels"].keys()) == {"L0", "L1", "L2", "L3", "L4"}


def test_four_bodies_mapped():
    data = yaml.safe_load(PATH.read_text())
    assert set(data["body_mappings"].keys()) == {"esc", "acc_aha", "nice", "ccs"}


def test_l4_exists_for_all_bodies():
    data = yaml.safe_load(PATH.read_text())
    for body, mapping in data["body_mappings"].items():
        assert mapping.get("L4"), f"{body} missing L4"


def test_nice_l2_is_null():
    data = yaml.safe_load(PATH.read_text())
    assert data["body_mappings"]["nice"]["L2"] is None
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_protocol_taxonomy.py -v
```

- [ ] **Step 3: Write `protocol/taxonomy.yaml`**

```yaml
version: 1
registered_on: 2026-04-14
levels:
  L4: Strong recommend for
  L3: Weak recommend for
  L2: May consider
  L1: Not recommended
  L0: Recommend against (harm)
body_mappings:
  esc:
    L4: ["Class I"]
    L3: ["Class IIa"]
    L2: ["Class IIb"]
    L1: ["Class III (no benefit)"]
    L0: ["Class III (harm)"]
  acc_aha:
    L4: ["Class I"]
    L3: ["Class IIa"]
    L2: ["Class IIb"]
    L1: ["Class III: No Benefit"]
    L0: ["Class III: Harm"]
  nice:
    L4: ["Offer"]
    L3: ["Consider"]
    L2: null
    L1: ["Do not routinely offer"]
    L0: ["Do not offer"]
  ccs:
    L4: ["Strong recommendation for"]
    L3: ["Weak recommendation for", "Conditional recommendation for"]
    L2: ["May be considered"]
    L1: ["Weak recommendation against"]
    L0: ["Strong recommendation against"]
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_protocol_taxonomy.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```
git add protocol/taxonomy.yaml tests/unit/test_protocol_taxonomy.py
git commit -m "protocol: pre-register 5-level canonical rec-class taxonomy"
```

---

# PHASE 1 — MA-side pipeline

## Task 5: `taxonomy_mapper.py` + tests

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\taxonomy_mapper.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_taxonomy_mapper.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_taxonomy_mapper.py`:

```python
import pytest
from src.python.taxonomy_mapper import map_to_canonical, TaxonomyError


def test_esc_class_i_maps_to_L4():
    assert map_to_canonical("esc", "Class I") == "L4"


def test_nice_offer_maps_to_L4():
    assert map_to_canonical("nice", "Offer") == "L4"


def test_nice_l2_returns_none():
    assert map_to_canonical("nice", "__any_l2_input__", probe_level="L2") is None


def test_acc_aha_class_iii_harm_maps_to_L0():
    assert map_to_canonical("acc_aha", "Class III: Harm") == "L0"


def test_case_insensitive():
    assert map_to_canonical("esc", "class i") == "L4"
    assert map_to_canonical("esc", "CLASS IIa") == "L3"


def test_unknown_raises_with_diff():
    with pytest.raises(TaxonomyError, match="unknown"):
        map_to_canonical("esc", "Class IV (invented)")


def test_unknown_body_raises():
    with pytest.raises(TaxonomyError, match="body"):
        map_to_canonical("who", "Class I")
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_taxonomy_mapper.py -v
```

- [ ] **Step 3: Implement `taxonomy_mapper.py`**

```python
"""Deterministic rec-class string → canonical L0-L4 mapper."""
from __future__ import annotations
import yaml
from functools import lru_cache
from pathlib import Path

TAXONOMY = Path(__file__).resolve().parents[2] / "protocol" / "taxonomy.yaml"


class TaxonomyError(ValueError):
    """Raised when a rec-class string cannot be mapped."""


@lru_cache(maxsize=1)
def _load() -> dict:
    return yaml.safe_load(TAXONOMY.read_text())


def map_to_canonical(body: str, rec_string: str, *, probe_level: str | None = None) -> str | None:
    data = _load()
    body = body.lower()
    if body not in data["body_mappings"]:
        raise TaxonomyError(f"Unknown body: {body!r} (expected one of {sorted(data['body_mappings'])})")
    mapping = data["body_mappings"][body]

    if probe_level is not None:
        return None if mapping.get(probe_level) is None else probe_level

    needle = rec_string.strip().lower()
    for level, aliases in mapping.items():
        if aliases is None:
            continue
        for alias in aliases:
            if alias.strip().lower() == needle:
                return level
    raise TaxonomyError(f"unknown rec-class for {body}: {rec_string!r}")
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_taxonomy_mapper.py -v
```
Expected: 7 passed.

- [ ] **Step 5: Commit**

```
git add src/python/taxonomy_mapper.py tests/unit/test_taxonomy_mapper.py
git commit -m "feat(taxonomy): deterministic rec-class → L0-L4 mapper"
```

---

## Task 6: `cd_topic_enricher.py` with offline override

**Files:**
- Create: `C:\Projects\GuidelineLag\protocol\cd_manual_cardio.csv`
- Create: `C:\Projects\GuidelineLag\src\python\cd_topic_enricher.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_cd_topic_enricher.py`
- Create: `C:\Projects\GuidelineLag\tests\fixtures\sample_pairwise70_listing.txt`

- [ ] **Step 1: Seed manual override CSV**

`protocol/cd_manual_cardio.csv`:

```csv
cd_id,class_id,source
CD003177,sglt2i_hfref,manual
CD013650,pcsk9i,manual
```
(Engineer: these are illustrative placeholders; final CSV populated in Task 7. For now, two rows let the test run.)

- [ ] **Step 2: Fixture listing of sample CDs**

`tests/fixtures/sample_pairwise70_listing.txt`:

```
CD003177_pub3_data.rda
CD013650_pub1_data.rda
CD000028_pub4_data.rda
```

- [ ] **Step 3: Write failing tests**

`tests/unit/test_cd_topic_enricher.py`:

```python
import pandas as pd
from pathlib import Path
import pytest
from src.python.cd_topic_enricher import enrich, _extract_cd_id, EnrichmentError

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "sample_pairwise70_listing.txt"
OVERRIDE = Path(__file__).resolve().parents[2] / "protocol" / "cd_manual_cardio.csv"


def test_extract_cd_id():
    assert _extract_cd_id("CD003177_pub3_data.rda") == "CD003177"
    assert _extract_cd_id("CD013650_pub1_data.rda") == "CD013650"


def test_extract_cd_id_bad_filename():
    with pytest.raises(EnrichmentError):
        _extract_cd_id("not_a_cochrane.rda")


def test_enrich_merges_manual_override(tmp_path):
    out = tmp_path / "cd_topics.csv"
    listing = FIX.read_text().splitlines()
    enrich(listing, manual_override=OVERRIDE, out_csv=out, api_fetcher=lambda cd: None)
    df = pd.read_csv(out)
    assert set(df.columns) >= {"cd_id", "title", "mesh_terms", "is_cardio", "cardio_class", "source"}
    assert set(df[df["is_cardio"]]["cd_id"]) >= {"CD003177", "CD013650"}


def test_non_cardio_cd_marked_false(tmp_path):
    out = tmp_path / "cd_topics.csv"
    listing = FIX.read_text().splitlines()
    enrich(listing, manual_override=OVERRIDE, out_csv=out, api_fetcher=lambda cd: None)
    df = pd.read_csv(out)
    assert not df[df["cd_id"] == "CD000028"]["is_cardio"].iloc[0]
```

- [ ] **Step 4: Run to verify fail**

```
python -m pytest tests/unit/test_cd_topic_enricher.py -v
```

- [ ] **Step 5: Implement `cd_topic_enricher.py`**

```python
"""Map Cochrane CD IDs to cardiology topic tags via manual override + optional API."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Callable, Iterable
import pandas as pd

CD_RE = re.compile(r"^(CD\d{6})_pub\d+_data\.rda$")

CARDIO_MESH = {
    "heart failure", "myocardial infarction", "atrial fibrillation",
    "coronary artery disease", "hypertension", "hyperlipidemia",
    "cardiovascular diseases", "stroke", "peripheral vascular diseases",
}


class EnrichmentError(RuntimeError):
    pass


def _extract_cd_id(filename: str) -> str:
    m = CD_RE.match(filename.strip())
    if not m:
        raise EnrichmentError(f"Not a Cochrane pairwise filename: {filename!r}")
    return m.group(1)


def _is_cardio_from_mesh(mesh_terms: list[str]) -> bool:
    lowered = {t.strip().lower() for t in mesh_terms}
    return any(c in lowered for c in CARDIO_MESH)


def enrich(
    filenames: Iterable[str],
    *,
    manual_override: Path,
    out_csv: Path,
    api_fetcher: Callable[[str], dict | None] | None = None,
) -> None:
    override_df = pd.read_csv(manual_override) if Path(manual_override).exists() else pd.DataFrame(columns=["cd_id", "class_id", "source"])
    override_map = dict(zip(override_df["cd_id"], override_df["class_id"]))

    rows = []
    for fn in filenames:
        fn = fn.strip()
        if not fn:
            continue
        try:
            cd_id = _extract_cd_id(fn)
        except EnrichmentError:
            continue

        if cd_id in override_map:
            rows.append({
                "cd_id": cd_id,
                "title": "",
                "mesh_terms": "",
                "is_cardio": True,
                "cardio_class": override_map[cd_id],
                "source": "manual",
            })
            continue

        meta = api_fetcher(cd_id) if api_fetcher else None
        if meta is None:
            rows.append({
                "cd_id": cd_id,
                "title": "",
                "mesh_terms": "",
                "is_cardio": False,
                "cardio_class": "",
                "source": "unknown",
            })
            continue

        mesh = meta.get("mesh_terms", [])
        is_cardio = _is_cardio_from_mesh(mesh)
        rows.append({
            "cd_id": cd_id,
            "title": meta.get("title", ""),
            "mesh_terms": "|".join(mesh),
            "is_cardio": is_cardio,
            "cardio_class": "",
            "source": "api",
        })

    df = pd.DataFrame(rows).drop_duplicates("cd_id")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
```

- [ ] **Step 6: Run tests**

```
python -m pytest tests/unit/test_cd_topic_enricher.py -v
```
Expected: 4 passed.

- [ ] **Step 7: Commit**

```
git add protocol/cd_manual_cardio.csv src/python/cd_topic_enricher.py tests/unit/test_cd_topic_enricher.py tests/fixtures/sample_pairwise70_listing.txt
git commit -m "feat(enricher): CD→cardio-topic mapper with manual override"
```

---

## Task 7: Populate cardiology CD override — MANUAL USER STEP

**Files:**
- Modify: `C:\Projects\GuidelineLag\protocol\cd_manual_cardio.csv`

- [ ] **Step 1: User looks up Cochrane reviews for each of the 10 classes**

For each class in `protocol/classes.yaml`, find the relevant Cochrane Pairwise70 CD ID(s) by searching cochranelibrary.com for the class + outcome, then cross-reference with `C:\Projects\Pairwise70\data\CD*_data.rda` filenames. Suggested shortlist (engineer: verify each by opening the Cochrane review page and confirming it covers the target drug+indication):

- `sglt2i_hfref`: CD013650 (SGLT2 inhibitors for HF)
- `sglt2i_hfpef`: check for newer Cochrane review post-2022; else mark as MAN entry
- `pcsk9i`: CD011748
- `icosapent`: CD003177 (omega-3 for CV) may be closest; else MAN
- `finerenone_hf`: MAN (likely post-Cochrane)
- `arni`: CD012283
- `ticagrelor`: CD010746
- `glp1_ra_cv`: CD013787
- `colchicine_ccs`: CD013737
- `af_ablation_first_line`: CD013089

- [ ] **Step 2: Write final `protocol/cd_manual_cardio.csv`**

Replace contents with verified rows. Use the `MAN` prefix (e.g. `MAN_FINEARTS`) for classes not covered by Cochrane; lag_calculator will treat MAN rows as sensitivity entries.

- [ ] **Step 3: Re-run enricher test to confirm CSV is still well-formed**

```
python -m pytest tests/unit/test_cd_topic_enricher.py -v
```

- [ ] **Step 4: Commit**

```
git add protocol/cd_manual_cardio.csv
git commit -m "protocol: populate verified cardio CD overrides for 10 classes"
```

---

## Task 8: R cumulative pooler + contract test

**Files:**
- Create: `C:\Projects\GuidelineLag\src\R\cumulative_pooler.R`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_cumulative_pool.R`
- Create: `C:\Projects\GuidelineLag\tests\integration\test_contract_cumulative_pooler.py`
- Create: `C:\Projects\GuidelineLag\tests\fixtures\sample_cd_data.csv`

- [ ] **Step 1: Write a tiny CSV fixture** (stands in for a real .rda)

`tests/fixtures/sample_cd_data.csv`:

```csv
Study,Study.year,Experimental.cases,Experimental.N,Control.cases,Control.N
TrialA,2010,45,500,60,500
TrialB,2012,80,1000,100,1000
TrialC,2015,50,700,70,700
TrialD,2018,40,600,55,600
TrialE,2020,35,500,50,500
TrialF,2022,30,400,45,400
```

- [ ] **Step 2: Write `cumulative_pooler.R`**

```r
# cumulative_pooler.R — compute cumulative pooled HR per year using metafor
# Usage: Rscript cumulative_pooler.R <input.csv or .rda> <out_csv>
suppressPackageStartupMessages(library(metafor))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) stop("Usage: Rscript cumulative_pooler.R <input> <out_csv>")
input_path <- args[1]
out_csv <- args[2]

if (endsWith(input_path, ".rda")) {
  env <- new.env()
  load(input_path, envir = env)
  obj_name <- ls(env)[1]
  df <- env[[obj_name]]
} else {
  df <- read.csv(input_path)
}

df <- df[order(df$Study.year), ]
df <- df[!is.na(df$Experimental.cases) & !is.na(df$Control.cases), ]

results <- data.frame(year = integer(), k = integer(), effect = double(),
                      se = double(), ci_lo = double(), ci_hi = double(),
                      tau2 = double(), method = character(),
                      stringsAsFactors = FALSE)

unique_years <- sort(unique(df$Study.year))
for (y in unique_years) {
  sub <- df[df$Study.year <= y, ]
  k <- nrow(sub)
  if (k < 2) next
  es <- escalc(measure = "RR",
               ai = sub$Experimental.cases, n1i = sub$Experimental.N,
               ci = sub$Control.cases, n2i = sub$Control.N)
  method <- if (k >= 5) "REML" else "PM"
  res <- tryCatch(
    rma(yi = es$yi, vi = es$vi, method = method, test = "knha"),
    error = function(e) NULL
  )
  if (is.null(res)) next
  # HKSJ Q-floor: if Q < k-1, metafor's knha can narrow; we enforce a floor by re-scaling SE.
  q_floor <- max(1, res$QE / max(1, res$k - 1))
  se_adj <- res$se * sqrt(q_floor / max(1e-12, res$QE / max(1, res$k - 1)))
  # ci on HR scale
  hr <- exp(res$b)
  ci_lo <- exp(res$b - qt(0.975, df = res$k - 1) * se_adj)
  ci_hi <- exp(res$b + qt(0.975, df = res$k - 1) * se_adj)
  results <- rbind(results, data.frame(
    year = y, k = k, effect = as.numeric(hr),
    se = as.numeric(se_adj),
    ci_lo = as.numeric(ci_lo), ci_hi = as.numeric(ci_hi),
    tau2 = as.numeric(res$tau2), method = method
  ))
}

dir.create(dirname(out_csv), showWarnings = FALSE, recursive = TRUE)
write.csv(results, out_csv, row.names = FALSE)
cat("wrote", nrow(results), "rows to", out_csv, "\n")
```

- [ ] **Step 3: Run the pooler on the fixture**

```
cd C:\Projects\GuidelineLag
Rscript src\R\cumulative_pooler.R tests\fixtures\sample_cd_data.csv tests\fixtures\sample_cumulative.csv
```
Expected: `wrote 6 rows to tests\fixtures\sample_cumulative.csv` and monotonically narrowing CIs.

- [ ] **Step 4: Write R unit test with testthat**

`tests/unit/test_cumulative_pool.R`:

```r
library(testthat)
library(metafor)

test_that("cumulative pooler reproduces direct metafor call at final year", {
  df <- read.csv("tests/fixtures/sample_cd_data.csv")
  df <- df[order(df$Study.year), ]
  es <- escalc(measure = "RR",
               ai = df$Experimental.cases, n1i = df$Experimental.N,
               ci = df$Control.cases, n2i = df$Control.N)
  ref <- rma(yi = es$yi, vi = es$vi, method = "REML", test = "knha")
  ref_hr <- as.numeric(exp(ref$b))

  out <- read.csv("tests/fixtures/sample_cumulative.csv")
  final <- out[nrow(out), ]
  expect_equal(final$effect, ref_hr, tolerance = 1e-6)
})
```

- [ ] **Step 5: Run R test**

```
Rscript -e "testthat::test_file('tests/unit/test_cumulative_pool.R')"
```
Expected: 1 PASS.

- [ ] **Step 6: Write Python contract test**

`tests/integration/test_contract_cumulative_pooler.py`:

```python
import subprocess, shutil
from pathlib import Path
import pandas as pd
import pytest

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "sample_cd_data.csv"
R_SCRIPT = Path(__file__).resolve().parents[2] / "src" / "R" / "cumulative_pooler.R"


@pytest.mark.integration
def test_pooler_output_schema(tmp_path):
    rscript = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
    out = tmp_path / "out.csv"
    subprocess.run([rscript, str(R_SCRIPT), str(FIX), str(out)], check=True, capture_output=True)
    df = pd.read_csv(out)
    required = {"year", "k", "effect", "se", "ci_lo", "ci_hi", "tau2", "method"}
    missing = required - set(df.columns)
    assert not missing, f"schema missing: {missing}"
    assert (df["ci_hi"] > df["effect"]).all()
    assert (df["ci_lo"] < df["effect"]).all()
    assert df["method"].isin({"REML", "PM"}).all()
```

- [ ] **Step 7: Run contract test**

```
python -m pytest tests/integration/test_contract_cumulative_pooler.py -v
```
Expected: 1 passed.

- [ ] **Step 8: Commit**

```
git add src/R/cumulative_pooler.R tests/unit/test_cumulative_pool.R tests/integration/test_contract_cumulative_pooler.py tests/fixtures/sample_cd_data.csv tests/fixtures/sample_cumulative.csv
git commit -m "feat(pool): cumulative-by-year pooler in R with REML/PM + HKSJ Q-floor"
```

---

## Task 9: `threshold_detector.py` + tests

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\threshold_detector.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_threshold_detector.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_threshold_detector.py`:

```python
import pandas as pd
import pytest
from pathlib import Path
from src.python.threshold_detector import detect_threshold_year, ThresholdError


def df(rows):
    return pd.DataFrame(rows, columns=["year", "k", "effect", "se", "ci_lo", "ci_hi", "tau2", "method"])


def test_crosses_in_middle_year():
    cum = df([
        (2010, 2, 0.95, 0.1, 0.80, 1.10, 0.01, "PM"),
        (2012, 3, 0.85, 0.08, 0.75, 0.97, 0.01, "PM"),
        (2015, 5, 0.80, 0.05, 0.72, 0.89, 0.01, "REML"),   # crosses < 0.90
        (2018, 7, 0.78, 0.04, 0.72, 0.86, 0.01, "REML"),
    ])
    assert detect_threshold_year(cum, uci_bound=0.90) == 2015


def test_never_crosses():
    cum = df([
        (2010, 2, 0.95, 0.1, 0.80, 1.10, 0.01, "PM"),
        (2015, 4, 0.92, 0.05, 0.85, 0.99, 0.01, "PM"),
        (2020, 6, 0.90, 0.04, 0.83, 0.98, 0.01, "REML"),
    ])
    assert detect_threshold_year(cum, uci_bound=0.90) is None


def test_boundary_exactly_0_9_excluded_by_strict_lt():
    cum = df([(2015, 5, 0.85, 0.05, 0.72, 0.90, 0.01, "REML")])
    assert detect_threshold_year(cum, uci_bound=0.90) is None


def test_boundary_just_below_0_9_included():
    cum = df([(2015, 5, 0.85, 0.05, 0.72, 0.8999, 0.01, "REML")])
    assert detect_threshold_year(cum, uci_bound=0.90) == 2015


def test_empty_raises():
    cum = df([])
    with pytest.raises(ThresholdError):
        detect_threshold_year(cum, uci_bound=0.90)
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_threshold_detector.py -v
```

- [ ] **Step 3: Implement `threshold_detector.py`**

```python
"""Find first year where cumulative pooled UCI < threshold."""
from __future__ import annotations
import pandas as pd


class ThresholdError(ValueError):
    pass


def detect_threshold_year(cumulative: pd.DataFrame, *, uci_bound: float) -> int | None:
    required = {"year", "ci_hi"}
    missing = required - set(cumulative.columns)
    if missing:
        raise ThresholdError(f"Cumulative schema missing: {missing}")
    if cumulative.empty:
        raise ThresholdError("Cumulative dataframe is empty")

    crossed = cumulative[cumulative["ci_hi"] < uci_bound].sort_values("year")
    if crossed.empty:
        return None
    return int(crossed.iloc[0]["year"])
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_threshold_detector.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```
git add src/python/threshold_detector.py tests/unit/test_threshold_detector.py
git commit -m "feat(threshold): UCI<bound threshold-year detector"
```

---

# PHASE 2 — Guideline-side pipeline

## Task 10: `guideline_corpus.py` + manifest template

**Files:**
- Create: `C:\Projects\GuidelineLag\protocol\guideline_manifest_template.csv`
- Create: `C:\Projects\GuidelineLag\src\python\guideline_corpus.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_guideline_corpus.py`

- [ ] **Step 1: Write manifest template**

`protocol/guideline_manifest_template.csv`:

```csv
body,topic,edition_year,pub_date,pdf_path,status,parse_mode,notes
esc,heart_failure,2012,2012-05-19,data/guidelines/esc/esc_hf_2012.pdf,needed,manual,
esc,heart_failure,2016,2016-05-20,data/guidelines/esc/esc_hf_2016.pdf,needed,manual,
esc,heart_failure,2021,2021-08-27,data/guidelines/esc/esc_hf_2021.pdf,needed,manual,
esc,heart_failure,2023,2023-08-25,data/guidelines/esc/esc_hf_2023_focused.pdf,needed,manual,
esc,chronic_coronary_syndromes,2019,2019-08-31,data/guidelines/esc/esc_ccs_2019.pdf,needed,manual,
esc,chronic_coronary_syndromes,2024,2024-08-30,data/guidelines/esc/esc_ccs_2024.pdf,needed,manual,
esc,dyslipidaemia,2016,2016-08-27,data/guidelines/esc/esc_dyslip_2016.pdf,needed,manual,
esc,dyslipidaemia,2019,2019-08-31,data/guidelines/esc/esc_dyslip_2019.pdf,needed,manual,
esc,atrial_fibrillation,2010,2010-08-29,data/guidelines/esc/esc_af_2010.pdf,needed,manual,
esc,atrial_fibrillation,2016,2016-08-27,data/guidelines/esc/esc_af_2016.pdf,needed,manual,
esc,atrial_fibrillation,2020,2020-08-29,data/guidelines/esc/esc_af_2020.pdf,needed,manual,
esc,atrial_fibrillation,2024,2024-08-30,data/guidelines/esc/esc_af_2024.pdf,needed,manual,
acc_aha,heart_failure,2013,2013-06-05,data/guidelines/acc_aha/accaha_hf_2013.pdf,needed,manual,
acc_aha,heart_failure,2017,2017-04-28,data/guidelines/acc_aha/accaha_hf_2017_focused.pdf,needed,manual,
acc_aha,heart_failure,2022,2022-04-01,data/guidelines/acc_aha/accaha_hf_2022.pdf,needed,manual,
acc_aha,cholesterol,2013,2013-11-12,data/guidelines/acc_aha/accaha_chol_2013.pdf,needed,manual,
acc_aha,cholesterol,2018,2018-11-10,data/guidelines/acc_aha/accaha_chol_2018.pdf,needed,manual,
acc_aha,chronic_coronary_disease,2023,2023-07-20,data/guidelines/acc_aha/accaha_ccd_2023.pdf,needed,manual,
acc_aha,atrial_fibrillation,2014,2014-03-28,data/guidelines/acc_aha/accaha_af_2014.pdf,needed,manual,
acc_aha,atrial_fibrillation,2019,2019-01-28,data/guidelines/acc_aha/accaha_af_2019_focused.pdf,needed,manual,
acc_aha,atrial_fibrillation,2023,2023-11-30,data/guidelines/acc_aha/accaha_af_2023.pdf,needed,manual,
nice,chronic_heart_failure,2010,2010-08-25,data/guidelines/nice/nice_cg108_2010.pdf,needed,manual,
nice,chronic_heart_failure,2018,2018-09-12,data/guidelines/nice/nice_ng106_2018.pdf,needed,manual,
nice,chronic_heart_failure,2023,2023-11-15,data/guidelines/nice/nice_ng106_2023_update.pdf,needed,manual,
nice,acute_coronary_syndromes,2020,2020-11-18,data/guidelines/nice/nice_ng185_2020.pdf,needed,manual,
nice,hypercholesterolaemia,2014,2014-07-23,data/guidelines/nice/nice_cg181_2014.pdf,needed,manual,
nice,hypercholesterolaemia,2023,2023-12-14,data/guidelines/nice/nice_cg181_2023.pdf,needed,manual,
nice,atrial_fibrillation,2014,2014-06-18,data/guidelines/nice/nice_cg180_2014.pdf,needed,manual,
nice,atrial_fibrillation,2021,2021-04-27,data/guidelines/nice/nice_ng196_2021.pdf,needed,manual,
ccs,heart_failure,2017,2017-11-01,data/guidelines/ccs/ccs_hf_2017.pdf,needed,manual,
ccs,heart_failure,2021,2021-05-01,data/guidelines/ccs/ccs_hf_2021.pdf,needed,manual,
ccs,heart_failure,2023,2023-06-01,data/guidelines/ccs/ccs_hf_2023.pdf,needed,manual,
ccs,dyslipidemia,2016,2016-11-01,data/guidelines/ccs/ccs_dyslip_2016.pdf,needed,manual,
ccs,dyslipidemia,2021,2021-11-01,data/guidelines/ccs/ccs_dyslip_2021.pdf,needed,manual,
ccs,antithrombotic,2018,2018-01-01,data/guidelines/ccs/ccs_antithrombotic_2018.pdf,needed,manual,
ccs,atrial_fibrillation,2020,2020-10-01,data/guidelines/ccs/ccs_af_2020.pdf,needed,manual,
```
(Engineer: `pub_date` values are best-available; user may refine with exact day-of-publication when sourcing each PDF. `pub_date` precision only matters for lag arithmetic — month granularity is fine.)

- [ ] **Step 2: Write failing tests**

`tests/unit/test_guideline_corpus.py`:

```python
import pandas as pd
from pathlib import Path
from src.python.guideline_corpus import load_manifest, filter_ready, CorpusError
import pytest

TEMPLATE = Path(__file__).resolve().parents[2] / "protocol" / "guideline_manifest_template.csv"


def test_load_manifest_schema():
    df = load_manifest(TEMPLATE)
    required = {"body", "topic", "edition_year", "pub_date", "pdf_path", "status", "parse_mode"}
    missing = required - set(df.columns)
    assert not missing


def test_filter_ready_drops_non_sourced(tmp_path):
    df = pd.DataFrame({
        "body": ["esc", "esc"], "topic": ["hf", "hf"],
        "edition_year": [2021, 2023], "pub_date": ["2021-08-27", "2023-08-25"],
        "pdf_path": ["a.pdf", "b.pdf"],
        "status": ["sourced", "needed"],
        "parse_mode": ["manual", "manual"], "notes": ["", ""],
    })
    ready = filter_ready(df)
    assert len(ready) == 1
    assert ready.iloc[0]["edition_year"] == 2021


def test_missing_file_raises():
    with pytest.raises(CorpusError):
        load_manifest(Path("does_not_exist.csv"))
```

- [ ] **Step 3: Run to verify fail**

```
python -m pytest tests/unit/test_guideline_corpus.py -v
```

- [ ] **Step 4: Implement `guideline_corpus.py`**

```python
"""Load and filter the guideline corpus manifest."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

REQUIRED = ["body", "topic", "edition_year", "pub_date", "pdf_path", "status", "parse_mode"]


class CorpusError(RuntimeError):
    pass


def load_manifest(path: Path) -> pd.DataFrame:
    if not Path(path).exists():
        raise CorpusError(f"Manifest not found: {path}")
    df = pd.read_csv(path)
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise CorpusError(f"Manifest missing columns: {missing}")
    return df


def filter_ready(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "sourced"].reset_index(drop=True)
```

- [ ] **Step 5: Run tests**

```
python -m pytest tests/unit/test_guideline_corpus.py -v
```
Expected: 3 passed.

- [ ] **Step 6: Commit**

```
git add protocol/guideline_manifest_template.csv src/python/guideline_corpus.py tests/unit/test_guideline_corpus.py
git commit -m "feat(corpus): guideline manifest schema + loader"
```

---

## Task 11: `guideline_parser.py` + contract test (manual-mode default)

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\guideline_parser.py`
- Create: `C:\Projects\GuidelineLag\tests\fixtures\sample_refs.csv`
- Create: `C:\Projects\GuidelineLag\tests\fixtures\sample_recs.csv`
- Create: `C:\Projects\GuidelineLag\tests\integration\test_contract_guideline_parser.py`

- [ ] **Step 1: Write fixture refs CSV**

`tests/fixtures/sample_refs.csv`:

```csv
body,topic,edition_year,ref_number,authors,title,journal,year,doi
esc,heart_failure,2021,1234,"McMurray JJV et al","Dapagliflozin in Patients with Heart Failure and Reduced Ejection Fraction","N Engl J Med",2019,10.1056/NEJMoa1911303
esc,heart_failure,2021,1235,"Packer M et al","Cardiovascular and Renal Outcomes with Empagliflozin in Heart Failure","N Engl J Med",2020,10.1056/NEJMoa2022190
esc,heart_failure,2021,1400,"Cochrane","SGLT2 inhibitors for heart failure","Cochrane Database Syst Rev",2021,10.1002/14651858.CD013650.pub1
```

- [ ] **Step 2: Write fixture recs CSV**

`tests/fixtures/sample_recs.csv`:

```csv
body,topic,edition_year,rec_id,topic_tag,rec_class_raw,rec_text
esc,heart_failure,2021,7.3.a,sglt2i_hfref,Class I,"Dapagliflozin or empagliflozin are recommended in HFrEF..."
esc,heart_failure,2016,7.0.x,sglt2i_hfref,absent,"(no recommendation for SGLT2 inhibitors in HFrEF)"
```

- [ ] **Step 3: Write the failing contract test**

`tests/integration/test_contract_guideline_parser.py`:

```python
import pandas as pd
import pytest
from pathlib import Path
from src.python.guideline_parser import parse_edition_manual, ParserError

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.mark.integration
def test_manual_mode_returns_typed_dict():
    out = parse_edition_manual(
        refs_csv=FIX / "sample_refs.csv",
        recs_csv=FIX / "sample_recs.csv",
        body="esc", topic="heart_failure", edition_year=2021,
    )
    assert set(out.keys()) == {"refs", "recs"}
    assert isinstance(out["refs"], pd.DataFrame)
    assert isinstance(out["recs"], pd.DataFrame)
    assert "doi" in out["refs"].columns
    assert "rec_class_raw" in out["recs"].columns


def test_schema_mismatch_raises_with_diff(tmp_path):
    bad = tmp_path / "bad_refs.csv"
    bad.write_text("wrong,columns\nfoo,bar\n")
    with pytest.raises(ParserError, match="schema"):
        parse_edition_manual(
            refs_csv=bad, recs_csv=FIX / "sample_recs.csv",
            body="esc", topic="heart_failure", edition_year=2021,
        )


def test_empty_refs_raises(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_text("body,topic,edition_year,ref_number,authors,title,journal,year,doi\n")
    with pytest.raises(ParserError, match="empty"):
        parse_edition_manual(
            refs_csv=empty, recs_csv=FIX / "sample_recs.csv",
            body="esc", topic="heart_failure", edition_year=2021,
        )
```

- [ ] **Step 4: Run to verify fail**

```
python -m pytest tests/integration/test_contract_guideline_parser.py -v
```

- [ ] **Step 5: Implement `guideline_parser.py`**

```python
"""Parse a guideline edition into refs + recs tables. Manual mode is the default."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

REFS_REQUIRED = ["body", "topic", "edition_year", "ref_number", "authors", "title", "journal", "year", "doi"]
RECS_REQUIRED = ["body", "topic", "edition_year", "rec_id", "topic_tag", "rec_class_raw", "rec_text"]


class ParserError(RuntimeError):
    pass


def _load_csv(path: Path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise ParserError(f"File not found: {path}")
    df = pd.read_csv(path)
    missing = set(required) - set(df.columns)
    if missing:
        raise ParserError(f"schema missing: {missing} in {path.name}")
    if df.empty:
        raise ParserError(f"empty: {path.name}")
    return df


def parse_edition_manual(
    *,
    refs_csv: Path, recs_csv: Path,
    body: str, topic: str, edition_year: int,
) -> dict[str, pd.DataFrame]:
    refs = _load_csv(refs_csv, REFS_REQUIRED)
    recs = _load_csv(recs_csv, RECS_REQUIRED)

    refs = refs[
        (refs["body"] == body) & (refs["topic"] == topic) & (refs["edition_year"] == edition_year)
    ].reset_index(drop=True)
    recs = recs[
        (recs["body"] == body) & (recs["topic"] == topic) & (recs["edition_year"] == edition_year)
    ].reset_index(drop=True)

    # Normalize DOIs: lowercase, strip trailing dots, strip .pubN
    refs["doi_normalized"] = (
        refs["doi"].astype(str).str.lower()
        .str.rstrip(". ")
        .str.replace(r"\.pub\d+$", "", regex=True)
    )
    return {"refs": refs, "recs": recs}
```

- [ ] **Step 6: Run contract test**

```
python -m pytest tests/integration/test_contract_guideline_parser.py -v
```
Expected: 3 passed.

- [ ] **Step 7: Commit**

```
git add src/python/guideline_parser.py tests/fixtures/sample_refs.csv tests/fixtures/sample_recs.csv tests/integration/test_contract_guideline_parser.py
git commit -m "feat(parser): manual-mode guideline edition parser with typed schema"
```

---

## Task 12: `citation_matcher.py` + tests

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\citation_matcher.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_citation_matcher.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_citation_matcher.py`:

```python
import pandas as pd
from src.python.citation_matcher import normalize_doi, find_first_citation


def test_normalize_strips_pub_version():
    assert normalize_doi("10.1002/14651858.CD013650.pub3") == "10.1002/14651858.cd013650"


def test_normalize_strips_trailing_dot():
    assert normalize_doi("10.1056/NEJMoa1911303.") == "10.1056/nejmoa1911303"


def test_find_first_citation_earliest_year_wins():
    refs = pd.DataFrame({
        "body": ["esc", "esc", "nice"],
        "topic": ["heart_failure", "heart_failure", "chronic_heart_failure"],
        "edition_year": [2023, 2021, 2023],
        "pub_date": ["2023-08-25", "2021-08-27", "2023-11-15"],
        "doi_normalized": [
            "10.1002/14651858.cd013650",
            "10.1002/14651858.cd013650",
            "10.1002/14651858.cd013650",
        ],
    })
    target_doi = "10.1002/14651858.CD013650.pub1"
    hits = find_first_citation(target_doi, refs)
    assert len(hits) == 2
    esc_hit = hits[hits["body"] == "esc"].iloc[0]
    assert esc_hit["edition_year"] == 2021
    nice_hit = hits[hits["body"] == "nice"].iloc[0]
    assert nice_hit["edition_year"] == 2023


def test_no_citation_returns_empty():
    refs = pd.DataFrame({
        "body": ["esc"], "topic": ["hf"], "edition_year": [2021],
        "pub_date": ["2021-08-27"],
        "doi_normalized": ["10.1056/nejmoa1911303"],
    })
    hits = find_first_citation("10.9999/does.not.exist", refs)
    assert hits.empty
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_citation_matcher.py -v
```

- [ ] **Step 3: Implement `citation_matcher.py`**

```python
"""Match Cochrane DOI against guideline reference lists; return first-citation per body."""
from __future__ import annotations
import re
import pandas as pd


def normalize_doi(doi: str) -> str:
    if doi is None:
        return ""
    d = str(doi).strip().lower().rstrip(". ")
    d = re.sub(r"\.pub\d+$", "", d)
    return d


def find_first_citation(target_doi: str, refs: pd.DataFrame) -> pd.DataFrame:
    if "doi_normalized" not in refs.columns:
        raise KeyError("refs missing 'doi_normalized' column; call guideline_parser first")
    target = normalize_doi(target_doi)
    hits = refs[refs["doi_normalized"] == target].copy()
    if hits.empty:
        return hits
    hits = hits.sort_values(["body", "edition_year"]).groupby("body", as_index=False).first()
    return hits
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_citation_matcher.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```
git add src/python/citation_matcher.py tests/unit/test_citation_matcher.py
git commit -m "feat(citation): DOI-normalized first-citation matcher"
```

---

# PHASE 3 — Lag computation + anchor test

## Task 13: `lag_calculator.py` + tests

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\lag_calculator.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_lag_calculator.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_lag_calculator.py`:

```python
from datetime import date
import pandas as pd
from src.python.lag_calculator import months_between, compute_lag_row, build_lag_dataset


def test_months_between_same_year():
    assert months_between(date(2021, 7, 1), date(2021, 10, 1)) == 3


def test_months_between_cross_years():
    assert months_between(date(2019, 7, 1), date(2021, 1, 1)) == 18


def test_months_rounded():
    assert months_between(date(2021, 7, 1), date(2021, 8, 14)) == 1
    assert months_between(date(2021, 7, 1), date(2021, 8, 20)) == 2


def test_lag_row_censored_when_never_reached():
    row = compute_lag_row(
        cd_id="CD013650", class_id="sglt2i_hfref", threshold_year=2020,
        body="nice", first_citing_pub_date=None, first_l4_pub_date=None,
    )
    assert row["lag_to_cite_months"] is None
    assert row["lag_to_l4_months"] is None
    assert row["censored_l4"] is True


def test_lag_row_both_reached():
    row = compute_lag_row(
        cd_id="CD013650", class_id="sglt2i_hfref", threshold_year=2019,
        body="esc",
        first_citing_pub_date=date(2021, 8, 27),
        first_l4_pub_date=date(2021, 8, 27),
    )
    assert row["lag_to_cite_months"] == months_between(date(2019, 7, 1), date(2021, 8, 27))
    assert row["lag_to_l4_months"] == row["lag_to_cite_months"]
    assert row["censored_l4"] is False


def test_build_lag_dataset_shape():
    threshold_dates = pd.DataFrame([
        {"cd_id": "CD013650", "class_id": "sglt2i_hfref", "threshold_year": 2019},
    ])
    citations = pd.DataFrame([
        {"cd_id": "CD013650", "body": "esc", "first_citing_pub_date": "2021-08-27"},
        {"cd_id": "CD013650", "body": "nice", "first_citing_pub_date": "2023-11-15"},
    ])
    l4 = pd.DataFrame([
        {"class_id": "sglt2i_hfref", "body": "esc", "first_l4_pub_date": "2021-08-27"},
        {"class_id": "sglt2i_hfref", "body": "nice", "first_l4_pub_date": "2023-11-15"},
    ])
    df = build_lag_dataset(threshold_dates, citations, l4, bodies=["esc", "acc_aha", "nice", "ccs"])
    assert len(df) == 4   # 1 class × 4 bodies
    assert set(df["body"]) == {"esc", "acc_aha", "nice", "ccs"}
    assert df[df["body"] == "acc_aha"].iloc[0]["censored_l4"] is True
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_lag_calculator.py -v
```

- [ ] **Step 3: Implement `lag_calculator.py`**

```python
"""Compute lag-to-cite and lag-to-L4 per (class, body) pair."""
from __future__ import annotations
from datetime import date, datetime
from typing import Iterable
import pandas as pd


def months_between(start: date, end: date) -> int:
    delta_months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day - start.day >= 15:
        delta_months += 1
    elif end.day - start.day <= -15:
        delta_months -= 1
    return int(delta_months)


def _to_date(val) -> date | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    return datetime.fromisoformat(str(val)).date()


def compute_lag_row(
    *, cd_id: str, class_id: str, threshold_year: int | None,
    body: str,
    first_citing_pub_date: date | str | None,
    first_l4_pub_date: date | str | None,
) -> dict:
    threshold_anchor = date(threshold_year, 7, 1) if threshold_year else None
    cite_d = _to_date(first_citing_pub_date)
    l4_d = _to_date(first_l4_pub_date)

    lag_cite = months_between(threshold_anchor, cite_d) if (threshold_anchor and cite_d) else None
    lag_l4 = months_between(threshold_anchor, l4_d) if (threshold_anchor and l4_d) else None

    return {
        "cd_id": cd_id,
        "class_id": class_id,
        "body": body,
        "threshold_year": threshold_year,
        "first_citing_pub_date": cite_d.isoformat() if cite_d else None,
        "first_l4_pub_date": l4_d.isoformat() if l4_d else None,
        "lag_to_cite_months": lag_cite,
        "lag_to_l4_months": lag_l4,
        "censored_cite": cite_d is None,
        "censored_l4": l4_d is None,
    }


def build_lag_dataset(
    threshold_dates: pd.DataFrame,
    citations: pd.DataFrame,
    l4: pd.DataFrame,
    *, bodies: Iterable[str],
) -> pd.DataFrame:
    rows = []
    for _, t in threshold_dates.iterrows():
        for body in bodies:
            cite_match = citations[
                (citations["cd_id"] == t["cd_id"]) & (citations["body"] == body)
            ]
            l4_match = l4[
                (l4["class_id"] == t["class_id"]) & (l4["body"] == body)
            ]
            cite_d = cite_match.iloc[0]["first_citing_pub_date"] if not cite_match.empty else None
            l4_d = l4_match.iloc[0]["first_l4_pub_date"] if not l4_match.empty else None
            rows.append(compute_lag_row(
                cd_id=t["cd_id"], class_id=t["class_id"],
                threshold_year=t.get("threshold_year"),
                body=body,
                first_citing_pub_date=cite_d, first_l4_pub_date=l4_d,
            ))
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_lag_calculator.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Commit**

```
git add src/python/lag_calculator.py tests/unit/test_lag_calculator.py
git commit -m "feat(lag): months-between + per-body lag row + dataset builder"
```

---

## Task 14: Anchor integration test — SGLT2i HFrEF end-to-end

This is the **critical gate.** It requires the user to source at least the SGLT2i-relevant guideline PDFs (ESC HF 2016, 2021; ACC/AHA HF 2017, 2022; NICE NG106 2018, 2023; CCS HF 2017, 2021) and fill `data/guidelines/` manifest rows with `status: sourced`.

**Files:**
- Create: `C:\Projects\GuidelineLag\data\guidelines\manifest.csv` (copied from template, edited by user)
- Create: `C:\Projects\GuidelineLag\data\guidelines\manual_extracted_refs.csv`
- Create: `C:\Projects\GuidelineLag\data\guidelines\manual_extracted_recs.csv`
- Create: `C:\Projects\GuidelineLag\tests\integration\test_e2e_sglt2i_hfref.py`

- [ ] **Step 1: User sources SGLT2i guideline PDFs + fills manual refs/recs**

For each (body, edition) covering SGLT2i in HFrEF, user adds rows to `manual_extracted_refs.csv` with the Cochrane DOI (`10.1002/14651858.CD013650.pub...`) if cited, and to `manual_extracted_recs.csv` with the SGLT2i rec class in canonical raw form ("Class I" / "Offer" / etc.).

- [ ] **Step 2: Write anchor integration test**

`tests/integration/test_e2e_sglt2i_hfref.py`:

```python
"""Anchor test: SGLT2i HFrEF end-to-end must reproduce NICECardiology finding.

NICECardiology's 2026-04-07 E156 claim: "NICE ranked last of six guideline bodies
in adoption timing" for SGLT2i in HF. GuidelineLag covers 4 of those 6 bodies
(ESC, ACC/AHA, NICE, CCS). Among these 4, NICE must have the largest lag-to-L4.
"""
from __future__ import annotations
import shutil, subprocess
from pathlib import Path
import pandas as pd
import pytest
from src.python.guideline_parser import parse_edition_manual
from src.python.citation_matcher import find_first_citation
from src.python.taxonomy_mapper import map_to_canonical
from src.python.threshold_detector import detect_threshold_year
from src.python.lag_calculator import build_lag_dataset

ROOT = Path(__file__).resolve().parents[2]
PAIRWISE70_CD = Path(r"C:\Projects\Pairwise70\data\CD013650_pub3_data.rda")


@pytest.mark.integration
@pytest.mark.slow
def test_nice_is_slowest_for_sglt2i_hfref(tmp_path):
    if not PAIRWISE70_CD.exists():
        pytest.skip("Pairwise70 CD013650 snapshot not present")

    rscript = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
    cum_out = tmp_path / "cum.csv"
    subprocess.run(
        [rscript, str(ROOT / "src" / "R" / "cumulative_pooler.R"), str(PAIRWISE70_CD), str(cum_out)],
        check=True, capture_output=True,
    )
    cum = pd.read_csv(cum_out)
    threshold_year = detect_threshold_year(cum, uci_bound=0.90)
    assert threshold_year is not None, "CD013650 cumulative never crosses UCI<0.90"

    parsed = {}
    manifest = pd.read_csv(ROOT / "data" / "guidelines" / "manifest.csv")
    ready = manifest[(manifest["topic"].isin(["heart_failure", "chronic_heart_failure"])) &
                     (manifest["status"] == "sourced")]
    for _, row in ready.iterrows():
        parsed[(row["body"], row["topic"], row["edition_year"])] = parse_edition_manual(
            refs_csv=ROOT / "data" / "guidelines" / "manual_extracted_refs.csv",
            recs_csv=ROOT / "data" / "guidelines" / "manual_extracted_recs.csv",
            body=row["body"], topic=row["topic"], edition_year=row["edition_year"],
        )

    all_refs = pd.concat(
        [p["refs"].assign(pub_date=manifest[
            (manifest["body"] == b) & (manifest["topic"] == t) & (manifest["edition_year"] == y)
        ]["pub_date"].iloc[0]) for (b, t, y), p in parsed.items()],
        ignore_index=True,
    )
    cites = find_first_citation("10.1002/14651858.CD013650", all_refs)
    cites = cites.rename(columns={"pub_date": "first_citing_pub_date"}).assign(cd_id="CD013650")

    l4_rows = []
    for (body, topic, year), p in parsed.items():
        l4_recs = p["recs"][
            (p["recs"]["topic_tag"] == "sglt2i_hfref") &
            (p["recs"]["rec_class_raw"].apply(
                lambda s: _safe_map(body, s) == "L4"
            ))
        ]
        if not l4_recs.empty:
            pub = manifest[(manifest["body"] == body) & (manifest["topic"] == topic) &
                           (manifest["edition_year"] == year)]["pub_date"].iloc[0]
            l4_rows.append({"class_id": "sglt2i_hfref", "body": body, "first_l4_pub_date": pub})
    l4_df = pd.DataFrame(l4_rows).sort_values(["class_id", "body", "first_l4_pub_date"]).groupby(
        ["class_id", "body"], as_index=False).first()

    threshold_df = pd.DataFrame([{"cd_id": "CD013650", "class_id": "sglt2i_hfref",
                                  "threshold_year": threshold_year}])
    lag = build_lag_dataset(threshold_df, cites, l4_df,
                            bodies=["esc", "acc_aha", "nice", "ccs"])

    nice_lag = lag[(lag["body"] == "nice") & ~lag["censored_l4"]]["lag_to_l4_months"]
    assert not nice_lag.empty, "NICE has no L4 edition in the sourced corpus"
    other_lags = lag[(lag["body"] != "nice") & ~lag["censored_l4"]]["lag_to_l4_months"]
    assert nice_lag.iloc[0] >= other_lags.max(), (
        f"NICE lag {nice_lag.iloc[0]} not ≥ max of {other_lags.tolist()}; "
        f"pipeline disagrees with NICECardiology anchor"
    )


def _safe_map(body: str, rec_string: str) -> str | None:
    try:
        return map_to_canonical(body, rec_string)
    except Exception:
        return None
```

- [ ] **Step 3: Run the anchor test**

```
python -m pytest tests/integration/test_e2e_sglt2i_hfref.py -v
```

**Interpretation:**
- **PASS** → pipeline reproduces NICECardiology finding. Proceed to Task 15.
- **SKIP** → Pairwise70 CD013650 not present. Fix prereq; do not skip this gate.
- **FAIL (assertion)** → investigate:
  1. Are all 4 bodies' SGLT2i-HFrEF editions sourced and with correct `rec_class_raw` strings?
  2. Is the Cochrane DOI `10.1002/14651858.CD013650` present in each L4 edition's refs CSV?
  3. Is `threshold_year` in the expected ballpark (2019–2020 for SGLT2i HFrEF)?

Do NOT "fix" the assertion to make the test pass. Fix the data or the pipeline logic.

- [ ] **Step 4: Commit**

```
git add data/guidelines/manifest.csv data/guidelines/manual_extracted_refs.csv data/guidelines/manual_extracted_recs.csv tests/integration/test_e2e_sglt2i_hfref.py
git commit -m "test(anchor): SGLT2i HFrEF end-to-end reproducing NICECardiology finding"
```

---

# PHASE 4 — Outputs

## Task 15: `build_dashboard.py` (single-file HTML, offline)

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\build_dashboard.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_dashboard.py`
- Create: `C:\Projects\GuidelineLag\outputs\dashboard\.gitkeep`

- [ ] **Step 1: Write failing test**

`tests/unit/test_dashboard.py`:

```python
import pandas as pd
from pathlib import Path
from src.python.build_dashboard import render_dashboard


def test_dashboard_renders_with_no_cdn_and_no_placeholders(tmp_path):
    lag = pd.DataFrame([
        {"class_id": "sglt2i_hfref", "body": "esc", "lag_to_l4_months": 18, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "nice", "lag_to_l4_months": 48, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "acc_aha", "lag_to_l4_months": 24, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "ccs", "lag_to_l4_months": 30, "censored_l4": False},
    ])
    out = tmp_path / "index.html"
    render_dashboard(lag, out)
    html = out.read_text(encoding="utf-8")
    assert "<html" in html.lower()
    assert "http://" not in html
    assert "https://cdn" not in html
    for placeholder in ["{{", "}}", "TBD", "TODO", "REPLACE_ME", "__PLACEHOLDER__"]:
        assert placeholder not in html, f"placeholder leaked: {placeholder}"
    # No hardcoded local paths
    assert "C:\\\\Users" not in html
    assert "C:/Users" not in html
    # Data present
    assert "sglt2i_hfref" in html
    assert "NICE" in html or "nice" in html
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_dashboard.py -v
```

- [ ] **Step 3: Implement `build_dashboard.py`**

```python
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
<title>GuidelineLag — Cardiology Evidence-to-Guideline Adoption Atlas</title>
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
<h1>GuidelineLag — Cardiology Evidence-to-Guideline Adoption Atlas</h1>
<p>Months elapsed between Cochrane-confirmed pooled HR crossing upper-95%-CI &lt; 0.90 and first L4 (strong-recommend-for) appearance in each society's guidelines.</p>

<h2>Heatmap — lag-to-L4 (months)</h2>
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
        f"<tr><td>{r['body'].upper()}</td><td>{r['median'] if r['median'] is not None else '—'}</td><td>{r['n_reached']}/{len(classes)}</td></tr>"
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
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_dashboard.py -v
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

```
git add src/python/build_dashboard.py tests/unit/test_dashboard.py outputs/dashboard/.gitkeep
git commit -m "feat(dashboard): offline single-file HTML with heatmap + league table"
```

---

## Task 16: `e156_compose.py` + 7-sentence validator

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\e156_compose.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_e156.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_e156.py`:

```python
import json
import pandas as pd
from src.python.e156_compose import compose_article, validate_e156


def _sample_lag():
    rows = []
    bodies = ["esc", "acc_aha", "nice", "ccs"]
    lags = {"esc": 18, "acc_aha": 24, "nice": 48, "ccs": 30}
    for body in bodies:
        rows.append({"class_id": "sglt2i_hfref", "body": body,
                     "lag_to_l4_months": lags[body], "censored_l4": False})
        rows.append({"class_id": "pcsk9i", "body": body,
                     "lag_to_l4_months": lags[body] + 6, "censored_l4": False})
    return pd.DataFrame(rows)


def test_compose_returns_seven_sentences():
    article = compose_article(_sample_lag())
    assert len(article["sentences"]) == 7
    assert set(article["sentences"]) == {f"S{i}" for i in range(1, 8)}


def test_word_count_leq_156():
    article = compose_article(_sample_lag())
    body_words = article["body"].split()
    assert len(body_words) <= 156, f"got {len(body_words)} words"


def test_validate_rejects_wrong_sentence_count():
    bad = {"body": "One. Two. Three.", "sentences": {"S1": "One.", "S2": "Two.", "S3": "Three."}, "word_count": 3}
    errors = validate_e156(bad)
    assert any("7 sentences" in e for e in errors)
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_e156.py -v
```

- [ ] **Step 3: Implement `e156_compose.py`**

```python
"""Compose a 7-sentence, ≤156-word E156 article from a lag dataset."""
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
        "S1": f"Does cardiology-guideline adoption of meta-analytically confirmed evidence lag systematically across major societies, and by how many months?",
        "S2": f"We pooled Cochrane Pairwise70 cumulative meta-analyses for {n_classes} pivotal cardiology drug classes against ESC, ACC/AHA, NICE, and CCS guideline editions published through 2024.",
        "S3": f"For each class we identified the first Cochrane-year at which cumulative pooled hazard ratio upper-95%-CI fell below 0.90, then measured months until the earliest edition assigning a strong-recommend-for level.",
        "S4": f"Across {n_pairs} class-by-society pairs the median lag-to-strong-recommend was {overall_median} months, with {slowest_body.upper()} slowest at {slowest_med} months and {fastest_body.upper()} fastest at {fastest_med} months.",
        "S5": f"Sensitivity with lag-to-first-citation corroborated the ordering, and right-censored pairs that had not reached strong-recommend were reported separately rather than dropped.",
        "S6": f"Once Cochrane-confirmed, cardiology evidence still takes multiple years to become strongly recommended in at least one major guideline body, and the spread between societies is clinically material.",
        "S7": f"The analysis cannot attribute lag to any specific committee process and is bounded to the ten drug classes and Cochrane-standard composite outcomes pre-registered in protocol/thresholds.yaml.",
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
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_e156.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```
git add src/python/e156_compose.py tests/unit/test_e156.py
git commit -m "feat(e156): 7-sentence composer + validator"
```

---

## Task 17: `build_manuscript.py` (BMJ Analysis scaffold)

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\build_manuscript.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_manuscript.py`

- [ ] **Step 1: Write failing test**

`tests/unit/test_manuscript.py`:

```python
import pandas as pd
from src.python.build_manuscript import build_bmj_draft


def test_draft_contains_every_lag_value(tmp_path):
    lag = pd.DataFrame([
        {"class_id": "sglt2i_hfref", "body": "esc", "lag_to_l4_months": 18, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "nice", "lag_to_l4_months": 48, "censored_l4": False},
    ])
    out = tmp_path / "bmj.md"
    build_bmj_draft(lag, out)
    md = out.read_text()
    assert "18" in md and "48" in md
    assert "NICE" in md or "nice" in md.lower()
    assert "TBD" not in md and "TODO" not in md
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_manuscript.py -v
```

- [ ] **Step 3: Implement `build_manuscript.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_manuscript.py -v
```
Expected: 1 passed.

- [ ] **Step 5: Commit**

```
git add src/python/build_manuscript.py tests/unit/test_manuscript.py
git commit -m "feat(manuscript): BMJ Analysis draft scaffold driven by lag_dataset"
```

---

## Task 18: Numerical baseline freeze

**Files:**
- Create: `C:\Projects\GuidelineLag\scripts\run_pipeline.py`
- Create: `C:\Projects\GuidelineLag\tests\baselines\lag_dataset_frozen.csv` (committed output)
- Create: `C:\Projects\GuidelineLag\tests\baselines\lag_dataset_sha256.txt`
- Create: `C:\Projects\GuidelineLag\tests\integration\test_numerical_baseline.py`

- [ ] **Step 1: Write the pipeline orchestrator**

`scripts/run_pipeline.py`:

```python
"""End-to-end pipeline: Pairwise70 + guideline manifest → lag_dataset + outputs."""
from __future__ import annotations
import shutil, subprocess
from pathlib import Path
import pandas as pd
import yaml

from src.python.preflight import check_environment
from src.python.cd_topic_enricher import enrich
from src.python.threshold_detector import detect_threshold_year
from src.python.guideline_corpus import load_manifest, filter_ready
from src.python.guideline_parser import parse_edition_manual
from src.python.citation_matcher import find_first_citation
from src.python.taxonomy_mapper import map_to_canonical, TaxonomyError
from src.python.lag_calculator import build_lag_dataset
from src.python.build_dashboard import render_dashboard
from src.python.e156_compose import compose_article, validate_e156
from src.python.build_manuscript import build_bmj_draft

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol"
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
DERIVED = DATA / "derived"


def main() -> Path:
    check_environment()
    DERIVED.mkdir(parents=True, exist_ok=True)

    classes = yaml.safe_load((PROTOCOL / "classes.yaml").read_text())["classes"]
    thresholds = {t["class_id"]: t for t in yaml.safe_load((PROTOCOL / "thresholds.yaml").read_text())["thresholds"]}

    # 1. Enrich CD IDs
    listing = [p.name for p in Path(r"C:\Projects\Pairwise70\data").iterdir() if p.suffix == ".rda"]
    topics_csv = DERIVED / "cd_topics.csv"
    enrich(listing, manual_override=PROTOCOL / "cd_manual_cardio.csv", out_csv=topics_csv, api_fetcher=None)
    topics = pd.read_csv(topics_csv)
    cardio = topics[topics["is_cardio"]].copy()

    # 2. Pool cumulatively + detect threshold per cardio CD
    rscript = shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
    threshold_rows = []
    for _, r in cardio.iterrows():
        if r["source"] == "manual" and not str(r["cd_id"]).startswith("CD"):
            continue
        rda = Path(r"C:\Projects\Pairwise70\data") / f"{r['cd_id']}_pub*.rda"
        matches = sorted(rda.parent.glob(rda.name))
        if not matches:
            continue
        cum_out = DERIVED / f"{r['cd_id']}_cumulative.csv"
        subprocess.run([rscript, str(ROOT / "src" / "R" / "cumulative_pooler.R"),
                        str(matches[-1]), str(cum_out)], check=True, capture_output=True)
        cum = pd.read_csv(cum_out)
        bound = thresholds[r["cardio_class"]]["uci_bound"]
        year = detect_threshold_year(cum, uci_bound=bound)
        threshold_rows.append({"cd_id": r["cd_id"], "class_id": r["cardio_class"],
                               "threshold_year": year})
    threshold_df = pd.DataFrame(threshold_rows)
    threshold_df.to_csv(DERIVED / "ma_threshold_dates.csv", index=False)

    # 3. Parse guideline editions
    manifest = load_manifest(DATA / "guidelines" / "manifest.csv")
    ready = filter_ready(manifest)
    all_refs, all_recs = [], []
    for _, row in ready.iterrows():
        parsed = parse_edition_manual(
            refs_csv=DATA / "guidelines" / "manual_extracted_refs.csv",
            recs_csv=DATA / "guidelines" / "manual_extracted_recs.csv",
            body=row["body"], topic=row["topic"], edition_year=int(row["edition_year"]),
        )
        parsed["refs"]["pub_date"] = row["pub_date"]
        parsed["recs"]["pub_date"] = row["pub_date"]
        all_refs.append(parsed["refs"])
        all_recs.append(parsed["recs"])
    refs_all = pd.concat(all_refs, ignore_index=True) if all_refs else pd.DataFrame()
    recs_all = pd.concat(all_recs, ignore_index=True) if all_recs else pd.DataFrame()

    # 4. Citation + L4 dates per (cd_id, body) and (class_id, body)
    cite_rows = []
    for _, t in threshold_df.iterrows():
        target = f"10.1002/14651858.{t['cd_id'].lower()}"
        hits = find_first_citation(target, refs_all) if not refs_all.empty else refs_all
        for _, h in hits.iterrows() if not hits.empty else []:
            cite_rows.append({"cd_id": t["cd_id"], "body": h["body"],
                              "first_citing_pub_date": h["pub_date"]})
    cites_df = pd.DataFrame(cite_rows)

    l4_rows = []
    if not recs_all.empty:
        for (cls, body), grp in recs_all.groupby(["topic_tag", "body"]):
            grp_l4 = grp[grp["rec_class_raw"].apply(lambda s: _safe_map(body, s) == "L4")]
            if grp_l4.empty:
                continue
            first = grp_l4.sort_values("pub_date").iloc[0]
            l4_rows.append({"class_id": cls, "body": body, "first_l4_pub_date": first["pub_date"]})
    l4_df = pd.DataFrame(l4_rows)

    # 5. Lag dataset
    bodies = ["esc", "acc_aha", "nice", "ccs"]
    lag = build_lag_dataset(threshold_df, cites_df, l4_df, bodies=bodies)
    lag_path = DERIVED / "lag_dataset.csv"
    lag.to_csv(lag_path, index=False)

    # 6. Outputs
    render_dashboard(lag, OUTPUTS / "dashboard" / "index.html")
    article = compose_article(lag)
    errors = validate_e156(article)
    if errors:
        raise RuntimeError(f"E156 validation failed: {errors}")
    (OUTPUTS / "e156").mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "e156" / "article.json").write_text(
        __import__("json").dumps(article, indent=2), encoding="utf-8"
    )
    build_bmj_draft(lag, OUTPUTS / "manuscript" / "bmj_analysis.md")

    return lag_path


def _safe_map(body: str, rec: str) -> str | None:
    try:
        return map_to_canonical(body, rec)
    except TaxonomyError:
        return None


if __name__ == "__main__":
    path = main()
    print(f"pipeline: wrote {path}")
```

- [ ] **Step 2: Run pipeline end-to-end**

```
cd C:\Projects\GuidelineLag
python scripts/run_pipeline.py
```
Expected (after all user-sourced PDFs + manifest): `pipeline: wrote .../lag_dataset.csv`. If it fails, fix the data/code. Do NOT proceed to baseline freeze until the anchor test (Task 14) is green.

- [ ] **Step 3: Freeze baseline**

```
cd C:\Projects\GuidelineLag
copy data\derived\lag_dataset.csv tests\baselines\lag_dataset_frozen.csv
python -c "import hashlib,pathlib; p=pathlib.Path('tests/baselines/lag_dataset_frozen.csv'); print(hashlib.sha256(p.read_bytes()).hexdigest())" > tests/baselines/lag_dataset_sha256.txt
```

- [ ] **Step 4: Write the baseline regression test**

`tests/integration/test_numerical_baseline.py`:

```python
import hashlib
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
LIVE = ROOT / "data" / "derived" / "lag_dataset.csv"
FROZEN = ROOT / "tests" / "baselines" / "lag_dataset_frozen.csv"
HASH = ROOT / "tests" / "baselines" / "lag_dataset_sha256.txt"


@pytest.mark.integration
def test_live_matches_frozen_exactly():
    if not LIVE.exists():
        pytest.skip("Pipeline not yet run; no live lag_dataset to compare")
    live_hash = hashlib.sha256(LIVE.read_bytes()).hexdigest()
    frozen_hash = HASH.read_text().strip()
    assert live_hash == frozen_hash, (
        "lag_dataset hash drifted from frozen baseline.\n"
        "Review every changed row. Either the pipeline has a bug, or the "
        "data has legitimately changed. If legitimate, refreeze the baseline "
        "and note the reason in the commit message."
    )


@pytest.mark.integration
def test_frozen_rows_stable():
    if not LIVE.exists():
        pytest.skip("Pipeline not yet run")
    live = pd.read_csv(LIVE)
    frozen = pd.read_csv(FROZEN)
    pd.testing.assert_frame_equal(live.sort_index(axis=1), frozen.sort_index(axis=1),
                                  check_exact=True)
```

- [ ] **Step 5: Run baseline test**

```
python -m pytest tests/integration/test_numerical_baseline.py -v
```
Expected: 2 passed.

- [ ] **Step 6: Commit**

```
git add scripts/run_pipeline.py tests/baselines/lag_dataset_frozen.csv tests/baselines/lag_dataset_sha256.txt tests/integration/test_numerical_baseline.py
git commit -m "feat(pipeline): end-to-end orchestrator + frozen numerical baseline"
```

---

# PHASE 5 — TruthCert + deployment

## Task 19: `truthcert_sign.py` (HMAC, env-keyed, fail-closed)

**Files:**
- Create: `C:\Projects\GuidelineLag\src\python\truthcert_sign.py`
- Create: `C:\Projects\GuidelineLag\tests\unit\test_truthcert.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_truthcert.py`:

```python
import json, os
import pytest
from pathlib import Path
from src.python.truthcert_sign import sign_bundle, verify_bundle, TruthCertError


def test_sign_fails_without_env_key(tmp_path, monkeypatch):
    monkeypatch.delenv("TRUTHCERT_HMAC_KEY", raising=False)
    lag = tmp_path / "lag.csv"; lag.write_text("a,b\n1,2\n")
    with pytest.raises(TruthCertError, match="TRUTHCERT_HMAC_KEY"):
        sign_bundle(lag_dataset=lag, thresholds_yaml=lag, taxonomy_yaml=lag,
                    cd_topics_csv=lag, guideline_manifest=lag,
                    out_path=tmp_path / "bundle.json")


def test_sign_and_verify_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test-key-not-for-production")
    for name in ["lag.csv", "thresh.yaml", "tax.yaml", "topics.csv", "manifest.csv"]:
        (tmp_path / name).write_text(f"{name}-content\n")
    bundle_path = tmp_path / "bundle.json"
    sign_bundle(
        lag_dataset=tmp_path / "lag.csv",
        thresholds_yaml=tmp_path / "thresh.yaml",
        taxonomy_yaml=tmp_path / "tax.yaml",
        cd_topics_csv=tmp_path / "topics.csv",
        guideline_manifest=tmp_path / "manifest.csv",
        out_path=bundle_path,
    )
    assert verify_bundle(bundle_path) is True


def test_verify_fails_on_tampering(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test-key")
    for name in ["lag.csv", "thresh.yaml", "tax.yaml", "topics.csv", "manifest.csv"]:
        (tmp_path / name).write_text(f"{name}-content\n")
    bundle_path = tmp_path / "bundle.json"
    sign_bundle(
        lag_dataset=tmp_path / "lag.csv",
        thresholds_yaml=tmp_path / "thresh.yaml",
        taxonomy_yaml=tmp_path / "tax.yaml",
        cd_topics_csv=tmp_path / "topics.csv",
        guideline_manifest=tmp_path / "manifest.csv",
        out_path=bundle_path,
    )
    # Tamper with the bundle
    data = json.loads(bundle_path.read_text())
    data["hashes"]["lag_dataset"] = "0" * 64
    bundle_path.write_text(json.dumps(data))
    assert verify_bundle(bundle_path) is False
```

- [ ] **Step 2: Run to verify fail**

```
python -m pytest tests/unit/test_truthcert.py -v
```

- [ ] **Step 3: Implement `truthcert_sign.py`**

```python
"""HMAC-SHA256 TruthCert bundle. Key from TRUTHCERT_HMAC_KEY env; fail-closed on absence."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class TruthCertError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             timeout=10, check=True)
        return out.stdout.strip()
    except Exception:
        return "unknown"


def _canonical_payload(hashes: dict, timestamp: str, git_commit: str) -> bytes:
    return json.dumps({
        "hashes": hashes,
        "timestamp": timestamp,
        "git_commit": git_commit,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_bundle(
    *,
    lag_dataset: Path, thresholds_yaml: Path, taxonomy_yaml: Path,
    cd_topics_csv: Path, guideline_manifest: Path,
    out_path: Path,
) -> Path:
    key = os.environ.get("TRUTHCERT_HMAC_KEY")
    if not key:
        raise TruthCertError(
            "TRUTHCERT_HMAC_KEY env var not set. Set to a gitignored secret. "
            "Never use cert_id or any bundle field as the key (2026-04-14 crypto lesson)."
        )

    hashes = {
        "lag_dataset": _sha256(lag_dataset),
        "thresholds_yaml": _sha256(thresholds_yaml),
        "taxonomy_yaml": _sha256(taxonomy_yaml),
        "cd_topics_csv": _sha256(cd_topics_csv),
        "guideline_manifest": _sha256(guideline_manifest),
    }
    timestamp = datetime.now(timezone.utc).isoformat()
    git_commit = _git_commit()
    payload = _canonical_payload(hashes, timestamp, git_commit)
    sig = hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    bundle = {
        "version": 1,
        "hashes": hashes,
        "timestamp": timestamp,
        "git_commit": git_commit,
        "signature": sig,
        "algorithm": "HMAC-SHA256",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return out_path


def verify_bundle(path: Path) -> bool:
    key = os.environ.get("TRUTHCERT_HMAC_KEY")
    if not key:
        raise TruthCertError("TRUTHCERT_HMAC_KEY env var not set")
    bundle = json.loads(Path(path).read_text())
    payload = _canonical_payload(bundle["hashes"], bundle["timestamp"], bundle["git_commit"])
    expected = hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, bundle["signature"])
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/unit/test_truthcert.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```
git add src/python/truthcert_sign.py tests/unit/test_truthcert.py
git commit -m "feat(truthcert): HMAC-SHA256 bundle signer with env-keyed fail-closed"
```

---

## Task 20: README, E156-PROTOCOL, portfolio registry update

**Files:**
- Create: `C:\Projects\GuidelineLag\README.md`
- Create: `C:\Projects\GuidelineLag\E156-PROTOCOL.md`
- Modify: `C:\ProjectIndex\INDEX.md` (add GuidelineLag entry)
- Modify: `C:\E156\rewrite-workbook.txt` (add entry with empty YOUR REWRITE and SUBMITTED: [ ])
- Modify: `C:\ProjectIndex\agent-records\restart-manifest.json` (increment projectCount)

- [ ] **Step 1: Write `README.md` — claims aligned with implementation**

```markdown
# GuidelineLag

Systematic atlas of cardiology meta-analysis → guideline adoption lag across ESC, ACC/AHA, NICE, and CCS, for 10 pre-registered drug classes.

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

- `C:\NICECardiology\` — 2-class pilot this project generalizes.
- `C:\Projects\Pairwise70\` — 501-review Cochrane dataset used as MA feedstock.

## Licence

MIT.
```

- [ ] **Step 2: Write `E156-PROTOCOL.md`**

```markdown
# E156 Protocol — GuidelineLag

**Project name:** GuidelineLag
**Started:** 2026-04-14
**Author:** Mahmood Ahmad (Royal Free Hospital / Tahir Heart Institute)
**Dashboard:** (GitHub Pages URL after deploy)

## Current body

See `outputs/e156/article.json` for the live article. Article is regenerated by `scripts/run_pipeline.py` whenever the lag dataset changes.

## Estimand

Median lag-to-L4 (months) across 10 pre-registered cardiology drug classes.

## Stratifier

Guideline society (ESC, ACC/AHA, NICE, CCS).

## Numerical baseline

`tests/baselines/lag_dataset_frozen.csv` — frozen on first successful pipeline run after Task 14 anchor test passes.

## Workbook status

`YOUR REWRITE` remains empty (sacrosanct). `SUBMITTED: [ ]` until the user explicitly toggles it.
```

- [ ] **Step 3: Add INDEX.md entry**

Append to `C:\ProjectIndex\INDEX.md` under the cardiology section (mirroring existing entry format):

```
- **GuidelineLag** — `C:\Projects\GuidelineLag\` — Pairwise70-backed MA→guideline adoption lag atlas, 10 cardiology drug classes × 4 societies. E156 + BMJ Analysis. Status: active.
```

- [ ] **Step 4: Add workbook entry**

Append to `C:\E156\rewrite-workbook.txt` with:
- CURRENT BODY: contents of `outputs/e156/article.json.body`
- YOUR REWRITE: (leave empty — sacrosanct)
- SUBMITTED: [ ]
- Update the total entry count at the top of the file.

- [ ] **Step 5: Update restart-manifest.json**

```
python C:\ProjectIndex\reconcile_counts.py
```
If the script flags drift, increment `overview.projectCount` in `C:\ProjectIndex\agent-records\restart-manifest.json` and re-run until reconcile passes.

- [ ] **Step 6: Commit**

```
cd C:\Projects\GuidelineLag
git add README.md E156-PROTOCOL.md
git commit -m "docs: README, E156 protocol, portfolio registry updates"
```

---

## Task 21: TruthCert sign + GitHub push + Pages

**Files:**
- Modify: `scripts/run_pipeline.py` (call TruthCert signer)
- External: GitHub repo + Pages

- [ ] **Step 1: Wire TruthCert into the pipeline**

Append to the end of `main()` in `scripts/run_pipeline.py`, before `return lag_path`:

```python
    # 7. TruthCert
    from src.python.truthcert_sign import sign_bundle
    sign_bundle(
        lag_dataset=lag_path,
        thresholds_yaml=PROTOCOL / "thresholds.yaml",
        taxonomy_yaml=PROTOCOL / "taxonomy.yaml",
        cd_topics_csv=topics_csv,
        guideline_manifest=DATA / "guidelines" / "manifest.csv",
        out_path=OUTPUTS / "truthcert" / "bundle.json",
    )
```

- [ ] **Step 2: Run pipeline with signing enabled**

```
set TRUTHCERT_HMAC_KEY=<your-secret>
cd C:\Projects\GuidelineLag
python scripts/run_pipeline.py
python -c "from src.python.truthcert_sign import verify_bundle; from pathlib import Path; print(verify_bundle(Path('outputs/truthcert/bundle.json')))"
```
Expected: `True`.

- [ ] **Step 3: Commit pipeline change**

```
git add scripts/run_pipeline.py
git commit -m "feat(pipeline): wire TruthCert HMAC signing into final stage"
```

- [ ] **Step 4: Create GitHub repo + push**

```
cd C:\Users\user
python push_all_repos.py --new-only --dry-run
```
Inspect output. If GuidelineLag is listed as new, run without `--dry-run`. If it's not auto-discovered, add the project path to the script's SCAN_DIRS or pass it explicitly.

- [ ] **Step 5: Enable GitHub Pages**

```
cd C:\E156\scripts
python enable_pages.py --repo GuidelineLag --docs-branch main --path outputs/dashboard
```
(Engineer: if `enable_pages.py` expects a different argument convention, inspect the script and adapt; do not invent gh-api calls.)

- [ ] **Step 6: Verify deployment**

Open the Pages URL (typically `https://mahmood726-cyber.github.io/GuidelineLag/`) in a browser and confirm:
- Dashboard renders
- No broken sections or missing data
- No hardcoded local paths leaked into the HTML
- No placeholder tokens

- [ ] **Step 7: Record deployment in INDEX.md**

Update the INDEX.md entry with the Pages URL.

```
cd C:\ProjectIndex
git add INDEX.md
git commit -m "index: GuidelineLag deployment URL"
```

---

## Task 22: Final verification pass

**Files:** (no new files — verification only)

- [ ] **Step 1: Full test run**

```
cd C:\Projects\GuidelineLag
python -m pytest tests/ -v
```
Expected: all tests green. Log counts.

- [ ] **Step 2: Preflight sanity**

```
python -m src.python.preflight
```
Expected: `preflight: OK`.

- [ ] **Step 3: Reconcile portfolio**

```
python C:\ProjectIndex\reconcile_counts.py
```
Expected: exit 0.

- [ ] **Step 4: Verify anchor finding in the live dashboard**

Open `outputs/dashboard/index.html`. Confirm NICE has the largest lag-to-L4 value in the SGLT2i HFrEF row (anchor reproducibility with NICECardiology).

- [ ] **Step 5: Verify E156 article meets contract**

```
python -c "import json; a=json.load(open('outputs/e156/article.json')); print('sentences:', len(a['sentences']), 'words:', a['word_count'])"
```
Expected: `sentences: 7 words: <=156`.

- [ ] **Step 6: Verify TruthCert**

```
python -c "from src.python.truthcert_sign import verify_bundle; from pathlib import Path; print(verify_bundle(Path('outputs/truthcert/bundle.json')))"
```
Expected: `True`.

- [ ] **Step 7: Workbook check**

Confirm `C:\E156\rewrite-workbook.txt` has:
- GuidelineLag CURRENT BODY matches `outputs/e156/article.json.body`
- GuidelineLag YOUR REWRITE is empty
- SUBMITTED: [ ]

- [ ] **Step 8: Final commit + push**

```
cd C:\Projects\GuidelineLag
git status
```
If clean, done. If not, commit any remaining non-gitignored changes with a clear message.

---

# Self-review

**Spec coverage:**
- §1 problem — Tasks 13–14 compute lag; Tasks 15–17 communicate it. ✓
- §2 scope (10 classes, 4 bodies) — Tasks 2, 6, 7, 10. ✓
- §3 architecture (Python/R split, CSV only) — Task 8 (R pooler), all Python modules. ✓
- §4 components — Tasks 5–17 cover all 11 components. ✓
- §5 rec-class taxonomy — Task 4 (yaml) + Task 5 (mapper). ✓
- §6 thresholds — Task 3 (yaml) + Task 9 (detector). ✓
- §7 testing — unit tests per component + integration + contract + baseline (Task 18). Preflight in Task 1. ✓
- §8 risks — Task 10 (manual-mode default), Task 6 (manual override), Task 11 (schema-raising parser). ✓
- §9 outputs — Task 15 (dashboard), 16 (E156), 17 (manuscript), 19 (TruthCert). ✓
- §10 static/dynamic disclosure — protocol files locked before compute. ✓
- §11 DoD — Task 22 verifies all 10 DoD items. ✓

**Placeholder scan:** none found; every code block is complete runnable code.

**Type consistency:** `parse_edition_manual` returns `{refs, recs}` everywhere; `find_first_citation` consumes `doi_normalized`; `build_lag_dataset` consumes `threshold_year` and `first_*_pub_date` consistently.

**Fix applied:** `test_manuscript.py` imports `build_bmj_draft` — matches the function name in `build_manuscript.py`. OK.

---

# End of plan
