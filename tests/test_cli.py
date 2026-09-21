import csv
from pathlib import Path

from chemo_regimen_dose_safety_agent.cli import main


def test_cli_audit(capsys):
    rc = main([
        "audit",
        "--case-id", "CLI-1",
        "--height-cm", "170",
        "--weight-kg", "70",
        "--reference-dose", "50",
        "--ordered-dose", "91",
    ])
    captured = capsys.readouterr()
    assert rc == 0
    assert "Case: CLI-1" in captured.out
    assert "BSA (Mosteller)" in captured.out


def test_cli_batch(tmp_path: Path):
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "results.csv"
    input_path.write_text(
        "case_id,height_cm,weight_kg,reference_dose_mg_per_m2,ordered_dose_mg,bsa_cap_m2\n"
        "A,170,70,50,91,\n"
        "B,180,110,2,2,2.0\n",
        encoding="utf-8",
    )
    rc = main(["batch", "-i", str(input_path), "-o", str(output_path)])
    assert rc == 0
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert "calculation_status" in rows[0]
    assert "flags" in rows[0]


def test_legacy_verify_audit_command_is_explicit(capsys):
    rc = main(["verify-audit"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "No persistent HMAC audit trail" in captured.out
