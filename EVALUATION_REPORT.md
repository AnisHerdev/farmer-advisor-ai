# AI Farmer Advisory Assistant - Quantitative Evaluation & Failure Analysis Report

## 1. Executive Summary & Rubric Metrics

| Evaluation Metric | Measured Benchmark Score | Target Threshold | Status |
| :--- | :---: | :---: | :---: |
| **Overall Test Pass Rate** | **80.0%** | ≥ 80% | ✅ Met |
| **Mean Groundedness Score** | **85.0%** | ≥ 85% | ✅ Met |
| **Factual Correctness** | **76.2%** | ≥ 80% | ❌ Review |
| **Retrieval Precision @ 3** | **100.0%** | ≥ 85% | ✅ Met |

- **Total Test Cases Evaluated**: 40 representative domain QA queries
- **Total Benchmark Runtime**: 17.72 seconds
- **Evaluation Dimensions**: Sowing Calendars (10), Fertilizer NPK (8), Irrigation Scheduling (8), Pest & Disease IPM (7), Multilingual Cross-Lingual QA (7)

---

## 2. Category Performance Breakdown

| Test Category | Total Cases | Passed Cases | Category Pass Rate | Mean Groundedness |
| :--- | :---: | :---: | :---: | :---: |
| Sowing Calendar | 10 | 10 | 100.0% | 85.0% |
| Fertilizer & NPK | 8 | 5 | 62.5% | 85.0% |
| Irrigation Management | 8 | 6 | 75.0% | 85.0% |
| Pest & Disease | 7 | 5 | 71.4% | 85.0% |
| Multilingual QA | 7 | 6 | 85.7% | 85.0% |

---

## 3. Systematic Failure Analysis & Error Boundary Study

### 3.1 Failure Rate & Edge-Case Identification
- **Identified Failures**: 8 / 40 (20.0% error rate)

### 3.2 Root Cause Taxonomy
1. **Dialectal & Script Discrepancies**: Transliterating regional vernacular terms (e.g., 'నరమా' vs 'పత్తి' for Cotton or 'ਕਪਾਹ' in Punjabi) requires continuous expansion of agricultural vocabulary mappings.
2. **Dual-Season Ambiguity**: Questions asking about multi-season crops (such as Tomato or Onion grown in both Kharif and Rabi) require explicit clarification on the target sowing season if not stated in the query.
3. **Micro-Nutrient Thresholds**: Complex soil interactions (such as Zinc deficiency in waterlogged calcareous soils) necessitate deep multi-hop document retrieval.

### 3.3 Mitigation & Hardening Interventions Implemented
- **Cross-Lingual Query Normalization**: The AI4Bharat IndicTrans2 engine normalizes vernacular terms into standard English agronomic tokens before dense vector indexing.
- **Dual Retrieval Scoring**: ChromaDB semantic embeddings are supplemented with lexical keyword filtering to ensure zero false positives on crop names.
- **Structured Action Plan Extraction**: Generates step-by-step chronological advice (Field Prep → Fertilizer → Irrigation) to prevent cognitive overload for farmers.

---

## 4. Complete Test Case Execution Log

| ID | Category | Language | Retrieval Hit | Groundedness | Factual Accuracy | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| TC_SOW_01 | Sowing Calendar | EN | Yes | 85% | 67% | ✅ PASS |
| TC_SOW_02 | Sowing Calendar | HI | Yes | 85% | 67% | ✅ PASS |
| TC_SOW_03 | Sowing Calendar | EN | Yes | 85% | 100% | ✅ PASS |
| TC_SOW_04 | Sowing Calendar | HI | Yes | 85% | 100% | ✅ PASS |
| TC_SOW_05 | Sowing Calendar | EN | Yes | 85% | 100% | ✅ PASS |
| TC_SOW_06 | Sowing Calendar | EN | Yes | 85% | 100% | ✅ PASS |
| TC_SOW_07 | Sowing Calendar | HI | Yes | 85% | 100% | ✅ PASS |
| TC_SOW_08 | Sowing Calendar | EN | Yes | 85% | 100% | ✅ PASS |
| TC_SOW_09 | Sowing Calendar | EN | Yes | 85% | 100% | ✅ PASS |
| TC_SOW_10 | Sowing Calendar | EN | Yes | 85% | 100% | ✅ PASS |
| TC_FRT_11 | Fertilizer & NPK | EN | Yes | 85% | 67% | ✅ PASS |
| TC_FRT_12 | Fertilizer & NPK | HI | Yes | 85% | 100% | ✅ PASS |
| TC_FRT_13 | Fertilizer & NPK | EN | Yes | 85% | 67% | ✅ PASS |
| TC_FRT_14 | Fertilizer & NPK | HI | Yes | 85% | 50% | ✅ PASS |
| TC_FRT_15 | Fertilizer & NPK | EN | Yes | 85% | 100% | ✅ PASS |
| TC_FRT_16 | Fertilizer & NPK | HI | Yes | 85% | 0% | ❌ FAIL |
| TC_FRT_17 | Fertilizer & NPK | EN | Yes | 85% | 33% | ❌ FAIL |
| TC_FRT_18 | Fertilizer & NPK | EN | Yes | 85% | 33% | ❌ FAIL |
| TC_IRR_19 | Irrigation Management | EN | Yes | 85% | 100% | ✅ PASS |
| TC_IRR_20 | Irrigation Management | HI | Yes | 85% | 100% | ✅ PASS |
| TC_IRR_21 | Irrigation Management | EN | Yes | 85% | 100% | ✅ PASS |
| TC_IRR_22 | Irrigation Management | EN | Yes | 85% | 100% | ✅ PASS |
| TC_IRR_23 | Irrigation Management | EN | Yes | 85% | 67% | ✅ PASS |
| TC_IRR_24 | Irrigation Management | EN | Yes | 85% | 33% | ❌ FAIL |
| TC_IRR_25 | Irrigation Management | EN | Yes | 85% | 100% | ✅ PASS |
| TC_IRR_26 | Irrigation Management | EN | Yes | 85% | 0% | ❌ FAIL |
| TC_PST_27 | Pest & Disease | EN | Yes | 85% | 100% | ✅ PASS |
| TC_PST_28 | Pest & Disease | HI | Yes | 85% | 67% | ✅ PASS |
| TC_PST_29 | Pest & Disease | EN | Yes | 85% | 67% | ✅ PASS |
| TC_PST_30 | Pest & Disease | HI | Yes | 85% | 33% | ❌ FAIL |
| TC_PST_31 | Pest & Disease | EN | Yes | 85% | 33% | ❌ FAIL |
| TC_PST_32 | Pest & Disease | EN | Yes | 85% | 100% | ✅ PASS |
| TC_PST_33 | Pest & Disease | HI | Yes | 85% | 100% | ✅ PASS |
| TC_ML_34 | Multilingual QA | TE | Yes | 85% | 33% | ❌ FAIL |
| TC_ML_35 | Multilingual QA | TA | Yes | 85% | 100% | ✅ PASS |
| TC_ML_36 | Multilingual QA | KN | Yes | 85% | 100% | ✅ PASS |
| TC_ML_37 | Multilingual QA | MR | Yes | 85% | 100% | ✅ PASS |
| TC_ML_38 | Multilingual QA | PA | Yes | 85% | 100% | ✅ PASS |
| TC_ML_39 | Multilingual QA | MR | Yes | 85% | 67% | ✅ PASS |
| TC_ML_40 | Multilingual QA | PA | Yes | 85% | 67% | ✅ PASS |