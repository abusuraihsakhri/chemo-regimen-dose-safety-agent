# Chemo Regimen Dose Safety Agent

> **Domain:** Medical Oncology, Clinical Pharmacology & Patient Safety  
> **Clinical Guidelines & Standards:** ASCO/ONS Chemotherapy Administration Safety Standards, NCCN Chemotherapy Order Templates, CPIC Pharmacogenomic Guidelines, CAP/CLSI Analytical Standards

---

## 📖 Clinical Overview

The **Chemo Regimen Dose Safety Agent** provides automated independent verification of antineoplastic chemotherapy orders prior to pharmacy dispensing and clinical administration. It cross-checks body surface area (BSA) calculations, enforces standard regimen dose capping rules, tracks cumulative lifetime anthracycline/bleomycin toxicity limits, and screens for pharmacogenomic toxicity variants (e.g., *DPYD*, *TPMT*, *UGT1A1*).

### Algorithmic Guardrails & Verification Modules

| Safety Module | Clinical Parameter Checked | Safety Threshold / Guideline | Intervention |
|:---|:---|:---|:---|
| **BSA Dose Cap Auditor** | Body Surface Area calculation (Mosteller / DuBois) | Cap standard doses at $BSA = 2.0 - 2.2\,\text{m}^2$ (e.g., Vincristine 2 mg max) | Hard dose cap warning |
| **Lifetime Toxicity Limit Tracker** | Cumulative anthracycline (Doxorubicin) / Bleomycin exposure | Doxorubicin $\le 450 - 550\,\text{mg/m}^2$, Bleomycin $\le 400\,\text{units}$ | Critical cardiotoxicity / pulmonary toxicity halt |
| **Pharmacogenomic Screen** | *DPYD*, *TPMT*, *NUDT15*, *UGT1A1* genotype alerts | Intermediate or poor metabolizer phenotypes | 50% dose reduction or alternative drug |
| **Organ Dysfunction Adjustments** | CrCl (Cockcroft-Gault) & Total Bilirubin/AST | Renal (Cisplatin, Carboplatin AUC) & Hepatic dose adjustments | Dose recalibration recommendation |

---

## 💻 CLI Quickstart & Usage

### 1. Single Task / Regimen Audit
```bash
python cli.py audit --task-id REG-001 --target DOXORUBICIN --primary 25.4 --secondary 14.2 --status NORMAL
```

### 2. Batch Process Chemotherapy Orders CSV
```bash
python cli.py batch -i sample.csv -o out_results.csv
```

### 3. Verify HMAC Cryptographic Audit Trail
```bash
python cli.py verify-audit
```

---

## 🧪 Verification & Testing

Execute comprehensive unit tests via pytest:
```bash
python -m pytest -p no:zarr
```
