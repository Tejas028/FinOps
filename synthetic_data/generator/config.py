# Config file

DATE_RANGE_START     = "2023-01-01"
DATE_RANGE_END       = "2024-12-31"   # 2 years of data
RANDOM_SEED          = 42

# Record volume per cloud
AWS_RECORDS_PER_DAY  = 80    # ~58,400 records total over 2 years
AZURE_RECORDS_PER_DAY = 60
GCP_RECORDS_PER_DAY  = 50

# Anomaly injection rates (% of days that get an anomaly event)
ANOMALY_INJECTION_RATE = 0.08   # 8% of days carry an anomaly

# Edge case rates
DUPLICATE_RATE       = 0.005   # 0.5% duplicate records
BACKDATED_RATE       = 0.03    # 3% of records are backdated 3-5 days
NULL_REGION_RATE     = 0.04    # 4% of records have null region (global services)
NULL_RESOURCE_RATE   = 0.06    # 6% of records have null resource_id
NEGATIVE_COST_RATE   = 0.01    # 1% credits/refunds/adjustments
CURRENCY_DIST = {
    "USD": 0.60, "EUR": 0.15,
    "GBP": 0.10, "CNY": 0.10, "INR": 0.05
}

MONTHLY_BUDGET_USD = {
    "aws": 180000,
    "azure": 160000,
    "gcp": 140000
}
