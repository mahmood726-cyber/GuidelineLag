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
