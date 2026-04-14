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
