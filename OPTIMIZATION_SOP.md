# 🚀 STANDARD OPERATING PROCEDURE - OPTIMIZATION

## PROCEDURE: Reality-Checked Parameter Optimization

### PURPOSE:
Eliminate fantasy profits and ensure all optimization results are achievable with actual market data.

### SCOPE: 
All parameter optimization activities for trading strategies.

### RESPONSIBILITIES:
- **Trader**: Follow SOP strictly, no exceptions
- **System**: Provide reality-checked results only
- **Validation**: Automatic and manual checks required

---

## 📋 DETAILED PROCEDURE:

### STEP 1: PREPARATION (5 minutes)
1. Open `PRE_OPTIMIZATION_CHECKLIST.md`
2. Complete ALL checklist items
3. Verify data file is current (within 24 hours)
4. Backup previous optimization results

### STEP 2: REALITY CHECK VALIDATION (3 minutes)
```bash
# Test reality checker is working
python -c "from web_reality_check import WebAppRealityChecker; print('Reality checker OK')"

# Verify data loading
python reality_check_optimizer.py --test-mode
```

### STEP 3: PARAMETER RANGE DEFINITION (10 minutes)
```python
# CONSERVATIVE STARTING RANGES:
param_ranges = {
    'sl': [2.0, 3.0, 4.0, 5.0],        # Stop loss %
    'be': [0.5, 1.0, 1.5, 2.0],        # Breakeven %  
    'ts_trig': [2.0, 3.0, 4.0, 5.0],   # Trailing trigger %
    'ts_step': [0.1, 0.2, 0.3, 0.5]    # Trailing step %
}
```

### STEP 4: RUN OPTIMIZATION (Variable time)
```bash
# ALWAYS use reality check optimizer
python reality_check_optimizer.py

# NEVER use old tools:
# python backtest_gridsearch_slbe_ts_Version3.py  # ❌ BANNED
```

### STEP 5: RESULT VALIDATION (10 minutes)
1. Check reality_score for ALL results (must be >0.8)
2. Verify fantasy_rate is <10%
3. Manually spot-check top 3 results:
   ```bash
   python emergency_reality_check.py --validate-result SL=X BE=Y TS=Z
   ```

### STEP 6: DOCUMENTATION (5 minutes)
Create result summary:
```
OPTIMIZATION SUMMARY - [DATE]
=============================
Data Period: [START] to [END]
Total Combinations Tested: [N]
Reality Score Range: [MIN] to [MAX]
Fantasy Results Detected: [N] ([%])
Top Result: SL=[X]% BE=[Y]% TS=[Z]% (Reality: [SCORE]%)
Validation Status: [PASS/FAIL]
```

### STEP 7: IMPLEMENTATION PREP (15 minutes)
1. Paper trade test with top parameters
2. Set position size to minimum for first week
3. Monitor vs expected performance
4. Document any deviations

---

## 🚨 EMERGENCY STOPS:

### IMMEDIATE STOP CONDITIONS:
- Reality score <80% on any result used
- Fantasy profit detected in live trading
- Results don't match expected performance
- System reports "FANTASY" flag

### ESCALATION PROCEDURE:
1. Stop all trading immediately
2. Run full audit: `python historical_auditor.py`
3. Validate all recent optimizations
4. Re-optimize with stricter parameters
5. Resume only after full validation

---

## 📊 QUALITY CONTROL:

### WEEKLY CHECKS:
- [ ] Reality checker still functional
- [ ] Data file updated regularly  
- [ ] No fantasy results in recent optimizations
- [ ] Live performance matches backtests

### MONTHLY REVIEWS:
- [ ] Full historical audit
- [ ] SOP effectiveness review
- [ ] Parameter range adjustments if needed
- [ ] System improvements identification

---

## 🎯 SUCCESS METRICS:

### OPTIMIZATION QUALITY:
- Reality Score Average: >85%
- Fantasy Detection Rate: <5%
- Live vs Backtest Match: >90%
- Parameter Stability: Consistent over time

### PROCESS EFFICIENCY:
- Setup Time: <10 minutes
- Optimization Time: <60 minutes  
- Validation Time: <15 minutes
- Total Cycle Time: <90 minutes

---

**GOLDEN RULE: If in doubt, validate again. Fantasy profits cost more than missed opportunities.**
