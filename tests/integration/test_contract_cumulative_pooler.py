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
