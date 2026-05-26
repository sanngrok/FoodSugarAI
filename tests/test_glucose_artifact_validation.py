import json
import subprocess
from pathlib import Path


def test_validate_glucose_artifacts_outputs_reports():
    subprocess.run(
        [
            "python3",
            "scripts/validate_glucose_artifacts.py",
            "--model-dir",
            "data/processed/glucose_models_enriched",
            "--report-dir",
            "reports/glucose_forecasting",
        ],
        check=True,
    )

    report_dir = Path("reports/glucose_forecasting")
    validation_path = report_dir / "artifact_validation_report.json"
    evidence_path = report_dir / "glucose_next_stage_evidence_summary.md"

    assert validation_path.exists()
    assert (report_dir / "artifact_validation_report.md").exists()
    assert evidence_path.exists()

    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    assert validation["status"] == "pass"
    assert validation["error_count"] == 0
    assert "hypo_threshold_sweep" in validation["artifacts"]

    evidence = evidence_path.read_text(encoding="utf-8")
    assert "Raw vs Calibrated MAE" in evidence
    assert "Selected Hypo Classifier" in evidence
    assert "의료 진단이나 치료 지침이 아니다" in evidence
