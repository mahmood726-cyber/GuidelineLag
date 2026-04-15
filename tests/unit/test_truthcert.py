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


def test_dev_mode_bundle_carries_synthetic_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "dev-key")
    for name in ["lag.csv", "thresh.yaml", "tax.yaml", "topics.csv", "manifest.csv"]:
        (tmp_path / name).write_text(f"{name}-content\n")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"overall_median": 28}))
    mode_manifest = tmp_path / "mode.json"
    mode_manifest.write_text(json.dumps({"mode": "dev-release-blocked", "synthetic": True}))
    bundle_path = tmp_path / "bundle.json"
    sign_bundle(
        lag_dataset=tmp_path / "lag.csv",
        thresholds_yaml=tmp_path / "thresh.yaml",
        taxonomy_yaml=tmp_path / "tax.yaml",
        cd_topics_csv=tmp_path / "topics.csv",
        guideline_manifest=tmp_path / "manifest.csv",
        baseline=baseline,
        mode_manifest=mode_manifest,
        out_path=bundle_path,
    )
    assert verify_bundle(bundle_path) is True
    bundle = json.loads(bundle_path.read_text())
    assert bundle["mode"] == "dev-release-blocked"
    assert bundle["synthetic"] is True
    assert "baseline" in bundle["hashes"]
    assert "mode_manifest" in bundle["hashes"]


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
