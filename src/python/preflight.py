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
        raise PreflightError(f"Pairwise70 has only {rda_count} .rda files, need >= {MIN_RDA_COUNT}")

    banner = _rscript_version()
    major, minor = _parse_r_version(banner)
    if (major, minor) < MIN_R_VERSION:
        raise PreflightError(f"Rscript {major}.{minor} < required {'.'.join(map(str, MIN_R_VERSION))}")

    if not _metafor_installed():
        raise PreflightError("R package 'metafor' not installed. Run: install.packages('metafor')")


if __name__ == "__main__":
    check_environment()
    print("preflight: OK")
