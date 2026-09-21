# Chemo Regimen Dose Safety Agent

A deterministic calculation utility for checking BSA-based antineoplastic doses against **user-supplied** protocol parameters. It calculates Mosteller body surface area, applies optional BSA and absolute dose caps, compares an entered dose with the calculated reference dose, and can project cumulative exposure against a user-entered limit.

> **Scope:** This project is a calculation and verification aid. It does not contain a regimen library, make treatment recommendations, infer dose modifications for organ dysfunction, or implement pharmacogenomic prescribing rules. Protocol-specific values must come from an independently validated source. It is not a substitute for oncology pharmacy or clinician verification.

## Features

- Mosteller BSA calculation from metric height and weight.
- BSA-based reference dose calculation in mg/m².
- Optional user-supplied BSA cap and absolute dose cap.
- Ordered-vs-calculated dose difference in mg and percent.
- User-defined deviation tolerance for review flags.
- Optional projected cumulative exposure and user-defined cumulative limit.
- Single-case CLI, CSV batch processing, optional FastAPI endpoint, and browser-only interface.
- No external service is required for the calculator; browser inputs remain in the browser.

The 2024 ASCO/ONS antineoplastic therapy administration safety standards include verification of height/weight, dose-calculation methodology, dosage, and cumulative lifetime dose when applicable. This repository implements calculation primitives only; it does not claim to implement the full standard.

## Browser application

The GitHub Pages interface is deployed from `docs/` after the CI and Pages workflow passes. A verified live link will be placed here after deployment.

## CLI

Install locally:

```bash
python -m pip install -e .
```

Check one order:

```bash
chemo-regimen-dose-safety-agent audit \
  --case-id CASE-001 \
  --height-cm 170 \
  --weight-kg 70 \
  --reference-dose 50 \
  --ordered-dose 91 \
  --tolerance 5
```

Optional protocol inputs include `--bsa-cap`, `--absolute-cap`, `--previous-cumulative`, and `--cumulative-limit`.

Batch processing:

```bash
chemo-regimen-dose-safety-agent batch -i sample.csv -o results.csv
```

## Optional API

```bash
python -m pip install -e '.[api]'
chemo-regimen-dose-safety-agent serve
```

The API exposes `/health` and `/api/audit`. It uses the same deterministic calculation engine as the CLI.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
node --test tests/test_web.mjs
```

The GitHub Actions workflow runs the Python suite on Python 3.10-3.13 and tests the browser calculation module with Node.

## Privacy and data handling

The browser interface performs calculations locally and does not send entered values to a server. It does not request names, medical record numbers, dates of birth, or other direct identifiers. The theme preference may be stored in the browser. The optional local API processes data supplied to that local service; deployment and logging policy are the responsibility of the operator.

## References

- ASCO/ONS Antineoplastic Therapy Administration Safety Standards, 2024: https://www.ons.org/ascoons-chemotherapy-administration-safety-standards
- Mosteller RD. Simplified calculation of body-surface area. *N Engl J Med.* 1987;317:1098. doi:10.1056/NEJM198710223171717

## License

MIT. See `LICENSE`.
