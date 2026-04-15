CLOUD_PROVIDERS = ["aws", "azure", "gcp"]

ANOMALY_TYPES = [
    "point_spike", "sustained_elevation", "gradual_drift", "sudden_drop",
    "multi_service_cascade", "budget_breach", "zero_cost_gap",
    "tag_explosion", "cross_region_transfer_spike", "reserved_instance_expiry"
]

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

FORECAST_HORIZONS = [7, 14, 30, 90]   # days

DATA_PATH = "synthetic_data/output"   # relative to repo root
