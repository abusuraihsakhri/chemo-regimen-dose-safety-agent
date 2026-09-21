import test from "node:test";
import assert from "node:assert/strict";
import { auditOrder, mostellerBsa, InputValidationError } from "../docs/calculator.mjs";

test("Mosteller BSA matches Python reference", () => {
  assert.ok(Math.abs(mostellerBsa(170, 70) - 1.818118685772619) < 1e-12);
});

test("reference dose calculation and tolerance flag", () => {
  const result = auditOrder({
    case_id: "WEB-1", height_cm: 170, weight_kg: 70,
    reference_dose_mg_per_m2: 75, ordered_dose_mg: 135,
    deviation_tolerance_percent: 5,
  });
  assert.ok(Math.abs(result.expected_dose_mg - 136.35890143294643) < 1e-9);
  assert.equal(result.calculation_status, "WITHIN_INPUT_RULES");
});

test("caps and cumulative rule trigger", () => {
  const result = auditOrder({
    case_id: "WEB-2", height_cm: 190, weight_kg: 120,
    reference_dose_mg_per_m2: 100, ordered_dose_mg: 200,
    bsa_cap_m2: 2, absolute_cap_mg: 180,
    previous_cumulative_mg_per_m2: 400, cumulative_limit_mg_per_m2: 450,
    deviation_tolerance_percent: 5,
  });
  assert.equal(result.expected_dose_mg, 180);
  assert.equal(result.calculation_status, "REVIEW_INPUTS");
  assert.ok(result.flags.some((flag) => flag.code === "BSA_CAP_APPLIED"));
  assert.ok(result.flags.some((flag) => flag.code === "ABSOLUTE_DOSE_CAP_APPLIED"));
  assert.ok(result.flags.some((flag) => flag.code === "PROJECTED_CUMULATIVE_LIMIT_EXCEEDED"));
});

test("invalid inputs reject", () => {
  assert.throws(() => auditOrder({
    case_id: "", height_cm: 170, weight_kg: 70,
    reference_dose_mg_per_m2: 75, ordered_dose_mg: 135,
  }), InputValidationError);
});
