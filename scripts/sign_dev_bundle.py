"""Sign the dev-mode TruthCert bundle.

Key resolution order (fail-closed if none):
  1. TRUTHCERT_HMAC_KEY env var
  2. .secrets/truthcert_dev_key.txt (gitignored)

Never silent-defaults, never uses a bundle field as key (2026-04-14 crypto lesson).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "python"))

from truthcert_sign import TruthCertError, sign_bundle, verify_bundle


def _resolve_key() -> str:
    key = os.environ.get("TRUTHCERT_HMAC_KEY")
    if key:
        return key
    keyfile = ROOT / ".secrets" / "truthcert_dev_key.txt"
    if keyfile.exists():
        k = keyfile.read_text(encoding="utf-8").strip()
        if k:
            os.environ["TRUTHCERT_HMAC_KEY"] = k
            return k
    print(
        "TRUTHCERT_HMAC_KEY unresolved. Fix with one of:\n"
        "  export TRUTHCERT_HMAC_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')\n"
        "  OR write a random key to .secrets/truthcert_dev_key.txt (gitignored).\n",
        file=sys.stderr,
    )
    raise SystemExit(2)


def main() -> int:
    _resolve_key()

    bundle_path = ROOT / "outputs" / "truthcert" / "bundle_dev.json"
    try:
        sign_bundle(
            lag_dataset=ROOT / "outputs" / "lag_dataset.csv",
            thresholds_yaml=ROOT / "protocol" / "thresholds.yaml",
            taxonomy_yaml=ROOT / "protocol" / "taxonomy.yaml",
            cd_topics_csv=ROOT / "protocol" / "cd_manual_cardio.csv",
            guideline_manifest=ROOT / "protocol" / "guideline_manifest_template.csv",
            baseline=ROOT / "outputs" / "baseline_dev.json",
            mode_manifest=ROOT / "outputs" / "mode.json",
            out_path=bundle_path,
        )
    except TruthCertError as e:
        print(f"TruthCertError: {e}", file=sys.stderr)
        return 3

    if not verify_bundle(bundle_path):
        print("Bundle failed self-verification. Aborting.", file=sys.stderr)
        return 4

    print(f"[dev-mode] bundle signed + verified: {bundle_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
