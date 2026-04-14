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
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
    out_path = Path(out_path)
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
