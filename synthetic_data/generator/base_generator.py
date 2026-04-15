import numpy as np
from datetime import date
import math
import calendar

from .config import RANDOM_SEED

def get_region_multiplier(region: str) -> float:
    if not region:
        return 1.0

    r = region.lower()
    if r in ['us-east-1', 'eastus', 'us-central1']:
        return 1.0
    if r in ['us-west-2', 'westus2', 'us-west1']:
        return 1.05
    if r in ['eu-west-1', 'westeurope', 'europe-west1']:
        return 1.12
    if r in ['ap-southeast-1', 'southeastasia', 'asia-east1']:
        return 1.18
        
    return 1.08

def get_baseline_multiplier(d: date, rng: np.random.Generator) -> float:
    """Calculates the baseline temporal multiplier for a given date."""
    cost_multiplier = 1.0

    # 1. WEEKDAY vs WEEKEND
    if d.weekday() >= 5:
        cost_multiplier *= 0.55
    
    # 2. END-OF-MONTH SPIKE
    _, last_day = calendar.monthrange(d.year, d.month)
    if d.day >= last_day - 2:
        cost_multiplier *= 1.25

    # 3. SEASONAL TREND
    month = d.month
    if 4 <= month <= 6:
        cost_multiplier *= 1.08
    elif 7 <= month <= 9:
        cost_multiplier *= 1.15
    elif 10 <= month <= 12:
        cost_multiplier *= 1.22
    
    # 4. YEAR-OVER-YEAR GROWTH: 0.8% per month
    months_diff = (d.year - 2023) * 12 + (d.month - 1)
    if months_diff > 0:
        cost_multiplier *= math.pow(1.008, months_diff)

    # 5. GAUSSIAN NOISE: ±12%
    # Use standard deviation of 0.04 so 3-sigma is 12%
    noise = rng.normal(1.0, 0.04) 
    noise = max(0.88, min(1.12, noise)) # cap to exactly +-12% boundary just in case
    cost_multiplier *= noise

    return cost_multiplier

def get_rng() -> np.random.Generator:
    """Returns a numpy random generator initialized with the seed from config."""
    return np.random.default_rng(RANDOM_SEED)
