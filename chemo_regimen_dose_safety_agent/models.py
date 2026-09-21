"""Data models for deterministic chemotherapy dose calculations.

The package intentionally does not encode regimen-specific prescribing rules.
Users provide any BSA cap, absolute dose cap, deviation tolerance, and cumulative
exposure limit that apply to their validated protocol or institutional policy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class OrderInput:
    """Inputs required for a single BSA-based dose calculation/check."""

    case_id: str
    height_cm: float
    weight_kg: float
    reference_dose_mg_per_m2: float
    ordered_dose_mg: float
    bsa_cap_m2: Optional[float] = None
    absolute_cap_mg: Optional[float] = None
    previous_cumulative_mg_per_m2: Optional[float] = None
    cumulative_limit_mg_per_m2: Optional[float] = None
    deviation_tolerance_percent: float = 5.0


@dataclass(frozen=True)
class CheckFlag:
    """A calculation finding. ``level`` is informational or requires review."""

    code: str
    level: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class AuditResult:
    """Deterministic calculation output for one order."""

    case_id: str
    bsa_m2: float
    dose_bsa_used_m2: float
    expected_dose_mg: float
    ordered_dose_mg: float
    dose_difference_mg: float
    dose_difference_percent: float
    planned_exposure_mg_per_m2: float
    projected_cumulative_mg_per_m2: Optional[float]
    cumulative_limit_utilization_percent: Optional[float]
    calculation_status: str
    flags: tuple[CheckFlag, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["flags"] = [flag.to_dict() for flag in self.flags]
        return data
