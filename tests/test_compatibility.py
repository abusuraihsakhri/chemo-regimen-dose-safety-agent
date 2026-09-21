import chemo_guard
from chemo_regimen_dose_safety_agent import OrderInput


def test_legacy_module_exports_coordinator():
    coordinator = chemo_guard.ChemoGuardCoordinator()
    result = coordinator.process_case(
        OrderInput(
            case_id="LEGACY-1",
            height_cm=170,
            weight_kg=70,
            reference_dose_mg_per_m2=50,
            ordered_dose_mg=91,
        )
    )
    assert result["case_id"] == "LEGACY-1"
    assert "calculation_status" in result
