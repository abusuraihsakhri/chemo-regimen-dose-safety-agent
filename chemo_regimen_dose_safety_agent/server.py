"""Optional FastAPI wrapper around the deterministic calculation engine."""
from __future__ import annotations

from . import __version__
from .engine import InputValidationError, audit_order
from .models import OrderInput


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, ConfigDict
    except ImportError as exc:  # pragma: no cover - exercised by CLI import guard
        raise ImportError("Install the API dependencies with: pip install '.[api]'") from exc

    app = FastAPI(
        title="Chemo Regimen Dose Safety Calculator API",
        description=(
            "Deterministic BSA-based dose calculations using user-supplied protocol limits. "
            "This API does not encode regimen-specific prescribing recommendations."
        ),
        version=__version__,
    )

    class AuditRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        case_id: str = "CASE-001"
        height_cm: float
        weight_kg: float
        reference_dose_mg_per_m2: float
        ordered_dose_mg: float
        bsa_cap_m2: float | None = None
        absolute_cap_mg: float | None = None
        previous_cumulative_mg_per_m2: float | None = None
        cumulative_limit_mg_per_m2: float | None = None
        deviation_tolerance_percent: float = 5.0

    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__}

    @app.post("/api/audit")
    def api_audit(request: AuditRequest):
        try:
            result = audit_order(OrderInput(**request.model_dump()))
        except InputValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.to_dict()

    return app
