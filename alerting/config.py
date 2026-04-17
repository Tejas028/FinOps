Z_SCORE_THRESHOLDS = {
    "low":      2.0,
    "medium":   2.5,
    "high":     3.0,
    "critical": 4.0
}
SPEND_SPIKE_PCT_THRESHOLD = 50.0   # pct_change_1d > 50% -> alert
BUDGET_WARNING_PCT        = 85.0   # projected >= 85% of budget -> alert
BUDGET_BREACH_PCT         = 100.0  # projected >= 100% -> critical alert
