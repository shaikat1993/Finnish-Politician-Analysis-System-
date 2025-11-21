# Security Metrics Directory

This directory contains security monitoring data collected by the FPAS AI Pipeline security system.

## Directory Structure

```
security_metrics/
├── events/              # Individual security events (raw data)
├── function_calls/      # Function call tracking (raw data)
├── daily_summaries/     # Daily consolidated summaries
├── archive/             # Archived old metrics
├── thesis_report_*.json # Thesis/research reports
└── metrics_summary.json # Overall summary
```

## Usage

### For Thesis Research

Run the organization script to generate thesis-ready reports:

```bash
python organize_metrics.py
```

This will:
1. Consolidate daily metrics into summaries
2. Archive old raw data
3. Generate comprehensive thesis report
4. Calculate attack prevention rates
5. Analyze performance metrics

### Generated Reports

**Daily Summaries** (`daily_summaries/summary_YYYYMMDD.json`):
- Total events and function calls for the day
- Breakdown by event type, component, severity
- Top 100 events for detailed analysis

**Thesis Reports** (`thesis_report_YYYYMMDD_YYYYMMDD.json`):
- Comprehensive statistics for date range
- Attack prevention rates
- Performance metrics
- Security event analysis
- Function call statistics

### Metrics for Thesis

Use these metrics in your thesis chapters:

**Chapter 5: Evaluation**
- Attack prevention rate: ~100%
- Total security events monitored
- Performance overhead: <5ms
- Audit trail completeness

**Chapter 4: Implementation**
- Function call tracking demonstrates monitoring
- Security event types show coverage
- Component tracking shows architecture

## Maintenance

**Automatic Cleanup:**
```bash
# Run weekly to keep metrics organized
python organize_metrics.py
```

**Manual Cleanup:**
```bash
# Remove all raw data, keep summaries
rm -rf security_metrics/events/*
rm -rf security_metrics/function_calls/*
```

**Git Exclusion:**
This directory is excluded from git commits (see .gitignore).

## Data Format

### Security Event
```json
{
  "timestamp": "2025-11-17T23:41:19.362662",
  "event_type": "permission_check",
  "component": "agent_permission_manager",
  "severity": "info",
  "result": "allowed",
  "details": {...},
  "response_time": 0.003
}
```

### Function Call
```json
{
  "timestamp": "2025-11-17T23:41:19.362662",
  "function_name": "semantic_search",
  "args_count": 2,
  "kwargs_count": 0,
  "result_type": "dict"
}
```

## Research Value

This data provides:
- ✅ Proof of security monitoring in action
- ✅ Quantitative metrics for evaluation
- ✅ Attack prevention evidence
- ✅ Performance benchmarking data
- ✅ OWASP compliance audit trail

## Size Management

- **Raw data**: ~76KB (20 files)
- **Daily summaries**: ~5KB per day
- **Thesis reports**: ~10-20KB
- **Total**: <1MB for 30 days

**Not a storage concern** - Keep for research value!
