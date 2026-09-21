import math
import pytest

from chemo_regimen_dose_safety_agent import InputValidationError, OrderInput, audit_order, mosteller_bsa


def test_mosteller_bsa():
    expected = math.sqrt((170 * 70) / 3600)
    assert mosteller_bsa(170, 70) == pytest.approx(expected)


def test_reference_dose_without_caps_is_within_tolerance():
    bsa = mosteller_bsa(170, 70)
    order = OrderInput(
        case_id="CASE-1",
        height_cm=170,
        weight_kg=70,
        reference_dose_mg_per_m2=50,
        ordered_dose_mg=50 * bsa,
        deviation_tolerance_percent=1,
    )
    result = audit_order(order)
    assert result.calculation_status == "WITHIN_INPUT_RULES"
    assert result.expected_dose_mg == pytest.approx(50 * bsa)
    assert result.dose_difference_percent == pytest.approx(0)
    assert not [f for f in result.flags if f.level == "review"]


def test_bsa_and_absolute_caps_are_applied_in_order():
    order = OrderInput(
        case_id="CASE-2",
        height_cm=200,
        weight_kg=120,
        reference_dose_mg_per_m2=100,
        ordered_dose_mg=150,
        bsa_cap_m2=2.0,
        absolute_cap_mg=150,
    )
    result = audit_order(order)
    assert result.bsa_m2 > 2.0
    assert result.dose_bsa_used_m2 == pytest.approx(2.0)
    assert result.expected_dose_mg == pytest.approx(150.0)
    assert {f.code for f in result.flags} >= {"BSA_CAP_APPLIED", "ABSOLUTE_DOSE_CAP_APPLIED"}
    assert result.calculation_status == "WITHIN_INPUT_RULES"


def test_outside_tolerance_requires_review():
    order = OrderInput(
        case_id="CASE-3",
        height_cm=170,
        weight_kg=70,
        reference_dose_mg_per_m2=50,
        ordered_dose_mg=120,
        deviation_tolerance_percent=5,
    )
    result = audit_order(order)
    assert result.calculation_status == "REVIEW_INPUTS"
    assert "ORDERED_DOSE_OUTSIDE_USER_TOLERANCE" in {f.code for f in result.flags}


def test_cumulative_limit_uses_actual_bsa_normalization():
    bsa = mosteller_bsa(170, 70)
    order = OrderInput(
        case_id="CASE-4",
        height_cm=170,
        weight_kg=70,
        reference_dose_mg_per_m2=50,
        ordered_dose_mg=100,
        previous_cumulative_mg_per_m2=400,
        cumulative_limit_mg_per_m2=450,
        deviation_tolerance_percent=100,
    )
    result = audit_order(order)
    assert result.planned_exposure_mg_per_m2 == pytest.approx(100 / bsa)
    assert result.projected_cumulative_mg_per_m2 == pytest.approx(400 + (100 / bsa))
    assert "PROJECTED_CUMULATIVE_LIMIT_EXCEEDED" in {f.code for f in result.flags}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"height_cm": 0},
        {"weight_kg": -1},
        {"reference_dose_mg_per_m2": float("nan")},
        {"ordered_dose_mg": 0},
        {"bsa_cap_m2": 0},
        {"deviation_tolerance_percent": -0.1},
    ],
)
def test_invalid_values_are_rejected(kwargs):
    values = dict(
        case_id="CASE-X",
        height_cm=170,
        weight_kg=70,
        reference_dose_mg_per_m2=50,
        ordered_dose_mg=90,
    )
    values.update(kwargs)
    with pytest.raises(InputValidationError):
        audit_order(OrderInput(**values))
