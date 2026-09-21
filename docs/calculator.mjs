export class InputValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "InputValidationError";
  }
}

function positive(name, value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) {
    throw new InputValidationError(`${name} must be a finite value greater than 0`);
  }
  return number;
}

function optionalNonNegative(name, value) {
  if (value === "" || value === null || value === undefined) return null;
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) {
    throw new InputValidationError(`${name} must be a finite value greater than or equal to 0`);
  }
  return number;
}

export function mostellerBsa(heightCm, weightKg) {
  return Math.sqrt((positive("height_cm", heightCm) * positive("weight_kg", weightKg)) / 3600);
}

export function auditOrder(input) {
  const caseId = String(input.case_id ?? "").trim();
  if (!caseId) throw new InputValidationError("case_id must not be empty");

  const referenceDose = positive("reference_dose_mg_per_m2", input.reference_dose_mg_per_m2);
  const orderedDose = positive("ordered_dose_mg", input.ordered_dose_mg);
  const tolerance = optionalNonNegative("deviation_tolerance_percent", input.deviation_tolerance_percent ?? 5);
  const bsa = mostellerBsa(input.height_cm, input.weight_kg);
  const bsaCap = optionalNonNegative("bsa_cap_m2", input.bsa_cap_m2);
  const absoluteCap = optionalNonNegative("absolute_cap_mg", input.absolute_cap_mg);
  const previous = optionalNonNegative("previous_cumulative_mg_per_m2", input.previous_cumulative_mg_per_m2);
  const cumulativeLimit = optionalNonNegative("cumulative_limit_mg_per_m2", input.cumulative_limit_mg_per_m2);

  if (bsaCap === 0) throw new InputValidationError("bsa_cap_m2 must be greater than 0 when provided");
  if (absoluteCap === 0) throw new InputValidationError("absolute_cap_mg must be greater than 0 when provided");
  if (cumulativeLimit === 0) throw new InputValidationError("cumulative_limit_mg_per_m2 must be greater than 0 when provided");

  const flags = [];
  let doseBsa = bsa;
  if (bsaCap !== null && bsa > bsaCap) {
    doseBsa = bsaCap;
    flags.push({ code: "BSA_CAP_APPLIED", level: "info", message: `User-supplied BSA cap of ${bsaCap.toFixed(3)} m² was applied.` });
  }

  let expectedDose = referenceDose * doseBsa;
  if (absoluteCap !== null && expectedDose > absoluteCap) {
    expectedDose = absoluteCap;
    flags.push({ code: "ABSOLUTE_DOSE_CAP_APPLIED", level: "info", message: `User-supplied absolute dose cap of ${absoluteCap.toFixed(2)} mg was applied.` });
  }

  const differenceMg = orderedDose - expectedDose;
  const differencePercent = (differenceMg / expectedDose) * 100;
  if (Math.abs(differencePercent) > tolerance) {
    flags.push({
      code: "ORDERED_DOSE_OUTSIDE_USER_TOLERANCE",
      level: "review",
      message: `Ordered dose differs from the calculated reference by ${differencePercent >= 0 ? "+" : ""}${differencePercent.toFixed(2)}%, outside the user-supplied ±${tolerance.toFixed(2)}% tolerance.`,
    });
  }

  const plannedExposure = orderedDose / bsa;
  let projectedCumulative = null;
  let cumulativeUtilization = null;
  if (previous !== null || cumulativeLimit !== null) projectedCumulative = (previous ?? 0) + plannedExposure;
  if (cumulativeLimit !== null) {
    cumulativeUtilization = (projectedCumulative / cumulativeLimit) * 100;
    if (projectedCumulative > cumulativeLimit) {
      flags.push({
        code: "PROJECTED_CUMULATIVE_LIMIT_EXCEEDED",
        level: "review",
        message: `Projected cumulative exposure (${projectedCumulative.toFixed(2)} mg/m²) exceeds the user-supplied limit (${cumulativeLimit.toFixed(2)} mg/m²).`,
      });
    } else if (Math.abs(projectedCumulative - cumulativeLimit) <= 1e-12) {
      flags.push({ code: "PROJECTED_CUMULATIVE_LIMIT_REACHED", level: "review", message: "Projected cumulative exposure reaches the user-supplied limit." });
    }
  }

  return {
    case_id: caseId,
    bsa_m2: bsa,
    dose_bsa_used_m2: doseBsa,
    expected_dose_mg: expectedDose,
    ordered_dose_mg: orderedDose,
    dose_difference_mg: differenceMg,
    dose_difference_percent: differencePercent,
    planned_exposure_mg_per_m2: plannedExposure,
    projected_cumulative_mg_per_m2: projectedCumulative,
    cumulative_limit_utilization_percent: cumulativeUtilization,
    calculation_status: flags.some((flag) => flag.level === "review") ? "REVIEW_INPUTS" : "WITHIN_INPUT_RULES",
    flags,
  };
}
