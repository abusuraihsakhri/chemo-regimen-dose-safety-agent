import { auditOrder } from "./calculator.mjs";

const form = document.querySelector("#dose-form");
const resultPanel = document.querySelector("#results");
const statusEl = document.querySelector("#result-status");
const metricsEl = document.querySelector("#result-metrics");
const flagsEl = document.querySelector("#result-flags");
const errorEl = document.querySelector("#form-error");
const themeButton = document.querySelector("#theme-toggle");
const exampleButton = document.querySelector("#load-example");

const fields = [
  "case_id", "height_cm", "weight_kg", "reference_dose_mg_per_m2", "ordered_dose_mg",
  "bsa_cap_m2", "absolute_cap_mg", "previous_cumulative_mg_per_m2",
  "cumulative_limit_mg_per_m2", "deviation_tolerance_percent",
];

function value(name) {
  return form.elements[name].value.trim();
}

function payloadFromForm() {
  return Object.fromEntries(fields.map((name) => [name, value(name)]));
}

function number(value, digits = 2, suffix = "") {
  if (value === null || value === undefined) return "—";
  return `${Number(value).toFixed(digits)}${suffix}`;
}

function render(result) {
  const review = result.calculation_status === "REVIEW_INPUTS";
  statusEl.textContent = review ? "Review inputs" : "Within input rules";
  statusEl.dataset.state = review ? "review" : "ok";

  const metrics = [
    ["BSA", number(result.bsa_m2, 3, " m²")],
    ["Dose BSA", number(result.dose_bsa_used_m2, 3, " m²")],
    ["Reference dose", number(result.expected_dose_mg, 2, " mg")],
    ["Ordered dose", number(result.ordered_dose_mg, 2, " mg")],
    ["Variance", number(result.dose_difference_percent, 2, "%")],
    ["Planned exposure", number(result.planned_exposure_mg_per_m2, 2, " mg/m²")],
    ["Projected cumulative", number(result.projected_cumulative_mg_per_m2, 2, " mg/m²")],
    ["Limit use", number(result.cumulative_limit_utilization_percent, 1, "%")],
  ];
  metricsEl.replaceChildren(...metrics.map(([label, val]) => {
    const item = document.createElement("div");
    item.className = "metric";
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = val;
    item.append(dt, dd);
    return item;
  }));

  flagsEl.replaceChildren();
  if (!result.flags.length) {
    const li = document.createElement("li");
    li.className = "flag flag-ok";
    li.textContent = "No cap or review flag was triggered by the supplied rules.";
    flagsEl.append(li);
  } else {
    result.flags.forEach((flag) => {
      const li = document.createElement("li");
      li.className = `flag flag-${flag.level}`;
      const strong = document.createElement("strong");
      strong.textContent = flag.code.replaceAll("_", " ");
      const span = document.createElement("span");
      span.textContent = flag.message;
      li.append(strong, span);
      flagsEl.append(li);
    });
  }
  resultPanel.hidden = false;
}

function run(event) {
  event?.preventDefault();
  errorEl.textContent = "";
  try {
    render(auditOrder(payloadFromForm()));
  } catch (error) {
    resultPanel.hidden = true;
    errorEl.textContent = error instanceof Error ? error.message : "Unable to calculate.";
  }
}

form.addEventListener("submit", run);
form.addEventListener("reset", () => {
  requestAnimationFrame(() => {
    resultPanel.hidden = true;
    errorEl.textContent = "";
  });
});

exampleButton.addEventListener("click", () => {
  const example = {
    case_id: "EXAMPLE-001", height_cm: "170", weight_kg: "72", reference_dose_mg_per_m2: "75",
    ordered_dose_mg: "125", bsa_cap_m2: "2.0", absolute_cap_mg: "150",
    previous_cumulative_mg_per_m2: "280", cumulative_limit_mg_per_m2: "450", deviation_tolerance_percent: "5",
  };
  Object.entries(example).forEach(([name, val]) => { form.elements[name].value = val; });
  run();
});

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeButton.setAttribute("aria-pressed", String(theme === "dark"));
  themeButton.querySelector("span").textContent = theme === "dark" ? "Light" : "Dark";
  try { localStorage.setItem("theme", theme); } catch { /* storage may be disabled */ }
}

let initialTheme = "light";
try { initialTheme = localStorage.getItem("theme") || "light"; } catch { /* ignore */ }
setTheme(initialTheme === "dark" ? "dark" : "light");
themeButton.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
