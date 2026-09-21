"""Core deterministic calculations for BSA-based antineoplastic dose checks."""
from __future__ import annotations

import math
from typing import Optional

from .models import AuditResult, CheckFlag, OrderInput


class InputValidationError(ValueError):
    """Raised when a calculation input is missing, non-finite, or out of range."""


def _positive(name: str, value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"{name} must be numeric") from exc
    if not math.isfinite(number) or number <= 0:
        raise InputValidationError(f"{name} must be a finite value greater than 0")
    return number


def _non_negative_optional(name: str, value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"{name} must be numeric when provided") from exc
    if not math.isfinite(number) or number < 0:
        raise InputValidationError(f"{name} must be a finite value greater than or equal to 0")
    return number


def mosteller_bsa(height_cm: float, weight_kg: float) -> float:
    """Return body surface area in m² using the Mosteller equation."""

    height = _positive("height_cm", height_cm)
    weight = _positive("weight_kg", weight_kg)
    return math.sqrt((height * weight) / 3600.0)


def audit_order(order: OrderInput) -> AuditResult:
    """Calculate a reference dose and compare it with an entered order.

    No regimen-specific thresholds are embedded. Optional caps and cumulative
    limits are treated solely as user-supplied protocol inputs.
    """

    if not str(order.case_id).strip():
        raise InputValidationError("case_id must not be empty")

    reference_dose = _positive("reference_dose_mg_per_m2", order.reference_dose_mg_per_m2)
    ordered_dose = _positive("ordered_dose_mg", order.ordered_dose_mg)
    tolerance = _non_negative_optional("deviation_tolerance_percent", order.deviation_tolerance_percent)
    assert tolerance is not None

    bsa = mosteller_bsa(order.height_cm, order.weight_kg)
    bsa_cap = _non_negative_optional("bsa_cap_m2", order.bsa_cap_m2)
    absolute_cap = _non_negative_optional("absolute_cap_mg", order.absolute_cap_mg)
    previous_cumulative = _non_negative_optional(
        "previous_cumulative_mg_per_m2", order.previous_cumulative_mg_per_m2
    )
    cumulative_limit = _non_negative_optional(
        "cumulative_limit_mg_per_m2", order.cumulative_limit_mg_per_m2
    )

    if bsa_cap == 0:
        raise InputValidationError("bsa_cap_m2 must be greater than 0 when provided")
    if absolute_cap == 0:
        raise InputValidationError("absolute_cap_mg must be greater than 0 when provided")
    if cumulative_limit == 0:
        raise InputValidationError("cumulative_limit_mg_per_m2 must be greater than 0 when provided")

    flags: list[CheckFlag] = []
    dose_bsa = bsa
    if bsa_cap is not None and bsa > bsa_cap:
        dose_bsa = bsa_cap
        flags.append(
            CheckFlag(
                code="BSA_CAP_APPLIED",
                level="info",
                message=f"User-supplied BSA cap of {bsa_cap:.3f} m² was applied.",
            )
        )

    expected_dose = reference_dose * dose_bsa
    if absolute_cap is not None and expected_dose > absolute_cap:
        expected_dose = absolute_cap
        flags.append(
            CheckFlag(
                code="ABSOLUTE_DOSE_CAP_APPLIED",
                level="info",
                message=f"User-supplied absolute dose cap of {absolute_cap:.2f} mg was applied.",
            )
        )

    difference_mg = ordered_dose - expected_dose
    difference_percent = (difference_mg / expected_dose) * 100.0
    if abs(difference_percent) > tolerance:
        flags.append(
            CheckFlag(
                code="ORDERED_DOSE_OUTSIDE_USER_TOLERANCE",
                level="review",
                message=(
                    f"Ordered dose differs from the calculated reference by {difference_percent:+.2f}%, "
                    f"outside the user-supplied ±{tolerance:.2f}% tolerance."
                ),
            )
        )

    planned_exposure = ordered_dose / bsa
    projected_cumulative: Optional[float] = None
    cumulative_utilization: Optional[float] = None
    if previous_cumulative is not None or cumulative_limit is not None:
        previous = previous_cumulative or 0.0
        projected_cumulative = previous + planned_exposure

    if cumulative_limit is not None:
        assert projected_cumulative is not None
        cumulative_utilization = (projected_cumulative / cumulative_limit) * 100.0
        if projected_cumulative > cumulative_limit:
            flags.append(
                CheckFlag(
                    code="PROJECTED_CUMULATIVE_LIMIT_EXCEEDED",
                    level="review",
                    message=(
                        f"Projected cumulative exposure ({projected_cumulative:.2f} mg/m²) exceeds "
                        f"the user-supplied limit ({cumulative_limit:.2f} mg/m²)."
                    ),
                )
            )
        elif math.isclose(projected_cumulative, cumulative_limit, rel_tol=1e-12, abs_tol=1e-12):
            flags.append(
                CheckFlag(
                    code="PROJECTED_CUMULATIVE_LIMIT_REACHED",
                    level="review",
                    message="Projected cumulative exposure reaches the user-supplied limit.",
                )
            )

    status = "REVIEW_INPUTS" if any(flag.level == "review" for flag in flags) else "WITHIN_INPUT_RULES"

    return AuditResult(
        case_id=str(order.case_id).strip(),
        bsa_m2=bsa,
        dose_bsa_used_m2=dose_bsa,
        expected_dose_mg=expected_dose,
        ordered_dose_mg=ordered_dose,
        dose_difference_mg=difference_mg,
        dose_difference_percent=difference_percent,
        planned_exposure_mg_per_m2=planned_exposure,
        projected_cumulative_mg_per_m2=projected_cumulative,
        cumulative_limit_utilization_percent=cumulative_utilization,
        calculation_status=status,
        flags=tuple(flags),
    )
