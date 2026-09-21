"""Compatibility facade for earlier coordinator-based imports.

The previous repository exposed several named "agents" with generic thresholds
that did not correspond to chemotherapy dosing variables. The compatibility
coordinator now delegates to the deterministic calculation engine.
"""
from __future__ import annotations

from .engine import audit_order
from .models import OrderInput


class ChemoGuardCoordinator:
    """Compatibility wrapper around :func:`audit_order`."""

    def process_case(self, case: OrderInput):
        if not isinstance(case, OrderInput):
            raise TypeError("process_case now expects an OrderInput instance")
        return audit_order(case).to_dict()

    def query_supervisory_chat(self, user_query: str) -> str:
        _ = user_query
        return (
            "This package performs deterministic BSA, dose-variance, and user-defined cumulative-limit calculations. "
            "It does not provide regimen-specific prescribing or pharmacogenomic recommendations."
        )
