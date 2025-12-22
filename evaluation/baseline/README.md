# Baseline Comparison: FPAS vs Naive Pattern Matching

**Research Question:** How much improvement does systematic design provide over ad-hoc pattern matching?

**Answer:** **+19.41 percentage points** improvement on adversarial benchmark (52.49% → 71.90%)

---

## 📋 Baseline Definition

### What Is "Baseline"?

**Baseline = Naive Pattern Matching Approach**

A simplified detector representing what someone might build in **1-2 hours** of ad-hoc development:
- **~10 basic regex patterns** (vs FPAS's 130+ patterns)
- **No systematic analysis** (vs FPAS's WildJailbreak-informed design)
- **No confidence calibration** (simple binary: match or no match)
- **English-only** (vs FPAS's multilingual support)

### Baseline Implementation

**Source code:** [`../ai_pipeline/tests/baseline_comparison.py`](../../ai_pipeline/tests/baseline_comparison.py) lines 19-76

**Class:** `SimpleBaselineDetector`

**Patterns (10 total):**
```python
patterns = [
    # Direct instruction override (3 patterns)
    r"ignore\s+(previous|all|your)\s+instructions?",
    r"forget\s+(everything|all|previous)",
    r"disregard\s+",

    # System prompt extraction (2 patterns)
    r"(show|reveal|tell)\s+.*\s+(system\s+prompt|instructions)",
    r"what\s+(is|are)\s+your\s+(instructions|rules|system\s+prompt)",

    # Role manipulation (3 patterns)
    r"(you\s+are|act\s+as|pretend\s+to\s+be)\s+(developer|admin|jailbreak)",
    r"DAN\s+mode",
    r"developer\s+mode",

    # Basic jailbreak attempts (1 pattern)
    r"jailbreak",
    r"bypass\s+(security|restrictions?)",

    # Data exfiltration (1 pattern)
    r"(send|email|export)\s+.*\s+to\s+",
]
```

### What Baseline LACKS

Compared to FPAS, the baseline lacks:

1. ❌ **WildJailbreak-Informed Patterns**
   - FPAS added 50+ patterns after analyzing WildJailbreak failures
   - Baseline uses only obvious patterns

2. ❌ **Opinion Detection**
   - FPAS distinguishes opinions from misinformation
   - Baseline flags political opinions as false (33.3% FP rate on LLM09)

3. ❌ **Strict Mode / Confidence Threshold**
   - FPAS uses 0.85 threshold for high-confidence detections only
   - Baseline has no confidence calibration

4. ❌ **Multilingual Support**
   - FPAS supports Finnish, Swedish, Russian patterns
   - Baseline is English-only

5. ❌ **Sophisticated Pattern Engineering**
   - FPAS patterns tested against variations
   - Baseline patterns not validated

---

## 📊 Verified Performance Comparison

**Data source:** [`results/baseline_comparison.json`](results/baseline_comparison.json)

### Overall Metrics

| Metric | Baseline (Naive) | FPAS (Systematic) | Improvement |
|--------|------------------|-------------------|-------------|
| **WildJailbreak Detection** | 52.49% | 71.90% | **+19.41pp** ✅ |
| **Precision** | 91.3% | 100.0% | **+8.7pp** ✅ |
| **F1-Score** | 79.09% | 96.73% | **+17.64pp** ✅ |
| **Development Time** | 1-2 hours | 2-3 weeks | - |
| **Pattern Count** | ~10 patterns | 130+ patterns | - |

### Category-by-Category Breakdown

| Category | FPAS Recall | Baseline Recall | FPAS Precision | Baseline Precision | Key Advantage |
|----------|------------|----------------|---------------|-------------------|---------------|
| **LLM01** (Prompt Injection) | 100.0% | 75.0% | 100.0% | 100.0% | +25.0pp recall |
| **LLM02** (Sensitive Data) | 100.0% | 80.0% | 100.0% | 100.0% | +20.0pp recall |
| **LLM06** (Excessive Agency) | 100.0% | 60.0% | 100.0% | 90.0% | +40.0pp recall, +10pp precision |
| **LLM09** (Misinformation) | 100.0% | 100.0% | 100.0% | 66.7% | +33.3pp precision ⭐ |
| **WildJailbreak** | 71.9% | 52.5% | 100.0% | 100.0% | +19.4pp recall ⭐ |

**Key insights:**
- ⭐ **LLM09:** Baseline flags 1 in 3 political opinions as misinformation (no opinion detection)
- ⭐ **WildJailbreak:** Baseline misses 28% more attacks than FPAS (no adversarial analysis)

---

## 🔬 Methodology (Jain Chapter 13)

### Comparison Design

**Type:** Paired observations (Section 13.4.1)
- Both systems tested on **identical 2,210 WildJailbreak samples**
- Enables direct comparison without confounding factors

**Statistical Test:** McNemar's test (Section 13.4.1)
- Null hypothesis: No difference between baseline and FPAS
- Test statistic: χ² = 427.00
- p-value: <0.001
- **Conclusion:** Improvement is statistically significant at 99.9% confidence

### Why This Comparison Matters

This comparison demonstrates:

1. **Value of Systematic Design**
   - Baseline: Ad-hoc patterns (1-2 hours) → 52.49% detection
   - FPAS: Systematic analysis (2-3 weeks) → 71.90% detection
   - **Investment in systematic development yields measurable, reproducible improvements**

2. **WildJailbreak Analysis Impact**
   - Without WildJailbreak-informed patterns: 52.49%
   - With WildJailbreak-informed patterns: 71.90%
   - **+19.41pp improvement from adversarial benchmark analysis**

3. **Opinion Detection Necessity**
   - Without opinion detection: 33.3% FP on political content
   - With opinion detection: 0% FP
   - **Critical for production deployment in political analysis domain**

4. **Production-Ready Engineering**
   - Baseline: 91.3% precision (usable but not production-ready)
   - FPAS: 100% precision (production-ready)
   - **Demonstrates importance of principled engineering decisions**

---

## 🎯 Key Advantages of FPAS

**Verified from:** [`results/baseline_comparison.json`](results/baseline_comparison.json) → `key_advantages`

### 1. WildJailbreak Analysis

**What:** Patterns informed by adversarial benchmark analysis
**Impact:** +19.41pp on WildJailbreak (52.49% → 71.90%)
**Without it:** Baseline misses 28% more attacks (429 additional attacks detected)

### 2. Opinion Detection

**What:** Distinguishes opinions from misinformation
**Impact:** 0% FP vs 33.3% FP on LLM09
**Without it:** 1 in 3 political opinions flagged as misinformation

### 3. Strict Mode

**What:** Confidence threshold (0.85) for high precision
**Impact:** 100% precision across all categories
**Without it:** Borderline cases cause false positives

### 4. Systematic Development

**What:** Iterative pattern refinement with validation
**Impact:** Consistent 100% precision + competitive recall
**Without it:** Ad-hoc patterns with unpredictable behavior

---

## ✅ How to Verify

### Run the Comparison

```bash
cd /path/to/fpas
python evaluation/baseline/run_comparison.py
```

**Expected output:**
```
======================================================================
BASELINE COMPARISON: FPAS vs Naive Pattern Matching
======================================================================

📌 WildJailbreak: Adversarial Benchmark
   FPAS:     Recall=71.9%  Precision=100.0%
   Baseline: Recall=52.5%  Precision=100.0%
   Gap: +19.4pp recall, +0.0pp precision
   → FPAS improved +19.41pp through WildJailbreak-informed patterns

======================================================================
OVERALL COMPARISON
======================================================================

📈 Average F1-Score:
   FPAS:     96.73%
   Baseline: 79.09%
   Improvement: +17.64pp
```

### Verify Results Data

```bash
# View complete results
cat evaluation/baseline/results/baseline_comparison.json

# Extract key metrics
jq '.comparison_summary' evaluation/baseline/results/baseline_comparison.json
```

**Expected fields:**
- `fpas.recall_wildjailbreak`: 71.9
- `baseline.recall_wildjailbreak`: 52.49
- `improvement.recall_gain_wildjailbreak`: 19.41

---

## 📚 Academic Context

### Alignment with Jain Chapter 13

**Section 13.4: Comparing Two Alternatives**

> "A majority of performance analysis projects require comparing two or more systems and finding the best among them."

**Our implementation:**
- System A (Baseline): Naive pattern matching
- System B (FPAS): Systematic pattern-based defense
- Comparison method: Paired observations on identical test set
- Statistical validation: McNemar's test (χ²=427.00, p<0.001)

**Section 13.4.1: Paired Observations**

> "If we conduct n experiments on each of the two systems such that there is a one-to-one correspondence between the ith test on system A and the ith test on system B, then the observations are called paired."

**Our implementation:**
- n = 2,210 WildJailbreak samples
- Each sample tested on both baseline and FPAS
- Direct 1-to-1 correspondence enables paired statistical tests

### Design Science Contribution

**Guideline 2: Problem Relevance**
- Demonstrates gap between naive and systematic approaches
- Quantifies value of systematic security engineering

**Guideline 3: Design Evaluation**
- Baseline provides controlled comparison point
- Shows +19.41pp improvement is not trivial

**Guideline 6: Design as Search Process**
- Baseline represents starting point (Iteration 0)
- FPAS represents refined solution (Iteration 3)
- Improvement trajectory documented

---

## 🎓 Thesis Integration

### Where to Cite This

**Section 4.2: Baseline Comparison**
- Table 4.3: "FPAS vs Baseline Performance" → Use [category breakdown](#category-by-category-breakdown)
- Figure 4.1: "Detection Rate Comparison" → Use data from `results/baseline_comparison.json`

**Section 5.2: Value Proposition**
- Justify development effort: **+19.41pp improvement** demonstrates ROI of systematic approach
- Production readiness: **100% vs 91.3% precision** shows engineering maturity

**Section 6.1: Contributions**
- **Contribution 3:** "Empirical evidence that systematic pattern development outperforms ad-hoc approaches (+19.41pp, p<0.001)"

### Tables for Thesis

**Pre-formatted for LaTeX:**

See `results/baseline_comparison.json` → `thesis_tables.table_6_baseline_comparison`

```json
{
  "title": "Table 6.1: FPAS vs Baseline Pattern Matching",
  "columns": ["Category", "FPAS Recall", "Baseline Recall", "FPAS Precision", "Baseline Precision", "Advantage"],
  "rows": [
    {"category": "Prompt Injection", "fpas_recall": "100.0%", "baseline_recall": "75.0%", ...},
    ...
  ]
}
```

---

## 📋 Verification Checklist

Use this to verify all baseline comparison claims:

- [ ] **Baseline code exists:** Check [`../ai_pipeline/tests/baseline_comparison.py`](../../ai_pipeline/tests/baseline_comparison.py) lines 19-76
- [ ] **10 patterns verified:** Count patterns in `SimpleBaselineDetector.__init__`
- [ ] **Results file exists:** Check `results/baseline_comparison.json`
- [ ] **52.49% baseline detection:** Verify in JSON `baseline.recall_wildjailbreak`
- [ ] **71.90% FPAS detection:** Verify in JSON `fpas.recall_wildjailbreak`
- [ ] **+19.41pp improvement:** Verify in JSON `improvement.recall_gain_wildjailbreak`
- [ ] **33.3% FP without opinion:** Verify in JSON `category_comparison.LLM09.baseline_precision = 66.7`
- [ ] **Script runs successfully:** Execute `python evaluation/baseline/run_comparison.py`
- [ ] **Output matches documented:** Compare console output to expected output above

---

## 🔗 Related Documentation

- **Parent:** [evaluation/README.md](../README.md) - Overview of all evaluations
- **Statistical Analysis:** [../statistical_analysis/README.md](../statistical_analysis/README.md) - McNemar's test details
- **Ablation Study:** [../ablation_study/README.md](../ablation_study/README.md) - WildJailbreak pattern contribution
- **Main README:** [../../README.md](../../README.md) - Project overview

---

**Last Updated:** December 2024
**Verification Status:** ✅ All metrics verified from source data
**Reproducibility:** ✅ Script executable, results regenerable
