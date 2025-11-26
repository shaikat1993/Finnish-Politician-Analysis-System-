# Running Comprehensive Security Tests for FPAS

## Prerequisites

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Add your API keys:
     ```
     OPENAI_API_KEY=your_key_here
     HUGGINGFACE_TOKEN=your_hf_token_here
     ```

## Run All Tests (Comprehensive Suite)

### Single Command to Run Everything:

```bash
python ai_pipeline/tests/run_comprehensive_security_evaluation.py
```

This will:
- ✅ Evaluate **LLM01** (Prompt Injection) - 100 test cases
- ✅ Evaluate **LLM02** (Sensitive Information) - 50 test cases  
- ✅ Evaluate **LLM06** (Excessive Agency) - 30 test cases
- ✅ Evaluate **LLM09** (Misinformation) - 20 test cases
- ✅ Evaluate **WildJailbreak** (External Validation) - 2,210 adversarial samples

**Total runtime:** Approximately 10-15 minutes (WildJailbreak takes 5-10 minutes)

## Test Outputs

After running, you'll find:

1. **JSON Results:** `test_reports/comprehensive_security_evaluation.json`
   - Raw metrics and detailed results
   - Machine-readable format

2. **Thesis Report:** `test_reports/THESIS_CHAPTER_4_RESULTS_DATA.md`
   - Formatted for thesis Chapter 4
   - Tables and statistics ready for academic writing

## Expected Results

### Target Metrics:
- **LLM01, LLM02, LLM06, LLM09:** >95% defense effectiveness
- **WildJailbreak:** >70% detection rate (pattern-based benchmark)
- **False Positive Rate:** <5% across all categories

### Sample Output:
```
================================================================================
 OVERALL RESULTS SUMMARY
================================================================================

📊 Defense Effectiveness by Category:
   LLM01               :  97.00%  ✅ PASS (target: >95%)
   LLM02               :  96.00%  ✅ PASS (target: >95%)
   LLM06               :  96.67%  ✅ PASS (target: >95%)
   LLM09               : 100.00%  ✅ PASS (target: >95%)
   WildJailbreak       :  71.90%  ✅ PASS (target: >70%)

📈 Overall Metrics:
   Overall Defense Effectiveness: 92.31%
   Overall False Positive Rate:   0.00%
```

## Quick Verification Checklist

Before committing, verify:
- [ ] All categories show ✅ PASS
- [ ] WildJailbreak detection ≥70%
- [ ] False positive rate <5%
- [ ] `test_reports/comprehensive_security_evaluation.json` generated
- [ ] `test_reports/THESIS_CHAPTER_4_RESULTS_DATA.md` generated

## Troubleshooting

### Missing HuggingFace Token:
```
Error: Hugging Face token not found
```
**Solution:** Add `HUGGINGFACE_TOKEN` to `.env` file

### Missing OpenAI Key:
```
Error: OpenAI API key not configured
```
**Solution:** Add `OPENAI_API_KEY` to `.env` file

### Import Errors:
```
ModuleNotFoundError: No module named 'datasets'
```
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

## Individual Test Scripts (Optional)

If you want to run tests separately:

### 1. WildJailbreak Only:
```bash
python ai_pipeline/security/evaluate_wildjailbreak.py --split eval
```

### 2. Analyze False Negatives:
```bash
python ai_pipeline/security/wildjailbreak/analyze_wildjailbreak_misses.py test_reports/wildjailbreak_eval_*.json
```

## For Thesis Writing

Use the generated `test_reports/THESIS_CHAPTER_4_RESULTS_DATA.md` directly in your thesis Chapter 4.

It includes:
- Complete results tables
- Detection rates by category
- WildJailbreak external validation results
- Statistical analysis ready for academic submission
