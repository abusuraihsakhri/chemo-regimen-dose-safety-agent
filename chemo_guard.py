"""Backward-compatible imports for the former single-file implementation."""
from chemo_regimen_dose_safety_agent import (  # noqa: F401
    AuditResult,
    CheckFlag,
    InputValidationError,
    OrderInput,
    audit_order,
    mosteller_bsa,
)
from chemo_regimen_dose_safety_agent.agents import ChemoGuardCoordinator  # noqa: F401
from chemo_regimen_dose_safety_agent.cli import main  # noqa: F401


if __name__ == "__main__":
    raise SystemExit(main())
