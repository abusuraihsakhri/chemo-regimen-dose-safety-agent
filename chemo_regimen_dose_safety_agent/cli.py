"""Command-line interface for the chemotherapy dose calculation utility."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

from .engine import InputValidationError, audit_order
from .models import OrderInput


CSV_INPUT_FIELDS = (
    "case_id",
    "height_cm",
    "weight_kg",
    "reference_dose_mg_per_m2",
    "ordered_dose_mg",
)
CSV_OUTPUT_FIELDS = (
    "bsa_m2",
    "dose_bsa_used_m2",
    "expected_dose_mg",
    "dose_difference_mg",
    "dose_difference_percent",
    "planned_exposure_mg_per_m2",
    "projected_cumulative_mg_per_m2",
    "cumulative_limit_utilization_percent",
    "calculation_status",
    "flags",
)


def _optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    return float(text)


def _order_from_mapping(row: dict[str, object]) -> OrderInput:
    missing = [name for name in CSV_INPUT_FIELDS if str(row.get(name, "")).strip() == ""]
    if missing:
        raise InputValidationError(f"missing required field(s): {', '.join(missing)}")
    return OrderInput(
        case_id=str(row["case_id"]),
        height_cm=float(row["height_cm"]),
        weight_kg=float(row["weight_kg"]),
        reference_dose_mg_per_m2=float(row["reference_dose_mg_per_m2"]),
        ordered_dose_mg=float(row["ordered_dose_mg"]),
        bsa_cap_m2=_optional_float(row.get("bsa_cap_m2")),
        absolute_cap_mg=_optional_float(row.get("absolute_cap_mg")),
        previous_cumulative_mg_per_m2=_optional_float(row.get("previous_cumulative_mg_per_m2")),
        cumulative_limit_mg_per_m2=_optional_float(row.get("cumulative_limit_mg_per_m2")),
        deviation_tolerance_percent=float(row.get("deviation_tolerance_percent") or 5.0),
    )


def _add_order_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--case-id", default="CASE-001")
    parser.add_argument("--height-cm", type=float, required=True)
    parser.add_argument("--weight-kg", type=float, required=True)
    parser.add_argument("--reference-dose", dest="reference_dose_mg_per_m2", type=float, required=True,
                        help="Protocol/reference dose in mg/m²")
    parser.add_argument("--ordered-dose", dest="ordered_dose_mg", type=float, required=True,
                        help="Entered total dose in mg")
    parser.add_argument("--bsa-cap", dest="bsa_cap_m2", type=float)
    parser.add_argument("--absolute-cap", dest="absolute_cap_mg", type=float)
    parser.add_argument("--previous-cumulative", dest="previous_cumulative_mg_per_m2", type=float)
    parser.add_argument("--cumulative-limit", dest="cumulative_limit_mg_per_m2", type=float)
    parser.add_argument("--tolerance", dest="deviation_tolerance_percent", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chemo-regimen-dose-safety-agent",
        description="Deterministic BSA-based dose calculation and order-check utility.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="Check one order against user-supplied calculation rules")
    _add_order_arguments(audit)

    batch = subparsers.add_parser("batch", help="Check orders from a CSV file")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")

    serve = subparsers.add_parser("serve", help="Run the optional FastAPI service")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    subparsers.add_parser(
        "verify-audit",
        help="Legacy compatibility command; this version does not create a persistent HMAC audit log",
    )
    return parser


def _print_result(result) -> None:
    print(f"Case: {result.case_id}")
    print(f"Calculation status: {result.calculation_status}")
    print(f"BSA (Mosteller): {result.bsa_m2:.4f} m²")
    print(f"BSA used for dose: {result.dose_bsa_used_m2:.4f} m²")
    print(f"Calculated reference dose: {result.expected_dose_mg:.2f} mg")
    print(f"Ordered dose: {result.ordered_dose_mg:.2f} mg")
    print(f"Difference: {result.dose_difference_mg:+.2f} mg ({result.dose_difference_percent:+.2f}%)")
    if result.projected_cumulative_mg_per_m2 is not None:
        print(f"Projected cumulative exposure: {result.projected_cumulative_mg_per_m2:.2f} mg/m²")
    if result.flags:
        print("Findings:")
        for flag in result.flags:
            print(f" - [{flag.level.upper()}] {flag.message}")
    else:
        print("Findings: none")


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "audit":
            order = OrderInput(
                case_id=args.case_id,
                height_cm=args.height_cm,
                weight_kg=args.weight_kg,
                reference_dose_mg_per_m2=args.reference_dose_mg_per_m2,
                ordered_dose_mg=args.ordered_dose_mg,
                bsa_cap_m2=args.bsa_cap_m2,
                absolute_cap_mg=args.absolute_cap_mg,
                previous_cumulative_mg_per_m2=args.previous_cumulative_mg_per_m2,
                cumulative_limit_mg_per_m2=args.cumulative_limit_mg_per_m2,
                deviation_tolerance_percent=args.deviation_tolerance_percent,
            )
            result = audit_order(order)
            if args.json:
                print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            else:
                _print_result(result)
            return 0

        if args.command == "batch":
            input_path = Path(args.input)
            output_path = Path(args.output)
            with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                source_fields = list(reader.fieldnames or [])

            output_rows: list[dict[str, object]] = []
            for index, row in enumerate(rows, start=2):
                try:
                    result = audit_order(_order_from_mapping(row))
                except (ValueError, InputValidationError) as exc:
                    raise InputValidationError(f"row {index}: {exc}") from exc
                enriched = dict(row)
                result_dict = result.to_dict()
                for field in CSV_OUTPUT_FIELDS:
                    value = result_dict[field]
                    if field == "flags":
                        value = json.dumps(value, separators=(",", ":"))
                    enriched[field] = value
                output_rows.append(enriched)

            output_fields = source_fields + [field for field in CSV_OUTPUT_FIELDS if field not in source_fields]
            with output_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=output_fields)
                writer.writeheader()
                writer.writerows(output_rows)
            print(f"Processed {len(output_rows)} row(s) -> {output_path}")
            return 0

        if args.command == "serve":
            try:
                import uvicorn
                from .server import create_app
            except ImportError:
                print("FastAPI/uvicorn are optional. Install with: pip install '.[api]'", file=sys.stderr)
                return 1
            uvicorn.run(create_app(), host=args.host, port=args.port)
            return 0

        if args.command == "verify-audit":
            print(
                "No persistent HMAC audit trail is created by this version. "
                "The previous implementation used an embedded default secret and did not cryptographically re-verify entries."
            )
            return 0

    except (InputValidationError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
