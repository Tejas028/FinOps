import uuid
import datetime
import random
from typing import Dict, List, Tuple, Any

from .config import (
    DATE_RANGE_START, DATE_RANGE_END, MONTHLY_BUDGET_USD,
    RANDOM_SEED
)
from .aws_generator import AWS_SERVICES, AWS_REGIONS
from .azure_generator import AZURE_SERVICES, AZURE_REGIONS
from .gcp_generator import GCP_SERVICES, GCP_REGIONS
from .base_generator import get_baseline_multiplier, get_rng

def build_anomaly_schedule() -> Tuple[Dict[str, Dict[Tuple[str, str, str], Dict[str, Any]]], List[Dict[str, Any]]]:
    """
    Builds the global AnomalySchedule table.
    schedule[date_str][(cloud, service, region)] = { multiplier, anomaly_id, type, severity }
    """
    rng = get_rng()
    start_date = datetime.date.fromisoformat(DATE_RANGE_START)
    end_date = datetime.date.fromisoformat(DATE_RANGE_END)
    delta = end_date - start_date
    total_days = delta.days + 1
    dates = [start_date + datetime.timedelta(days=i) for i in range(total_days)]

    # Flat lists of entities
    clouds = ['aws', 'azure', 'gcp']
    services_by_cloud = {
        'aws': list(AWS_SERVICES.keys()),
        'azure': list(AZURE_SERVICES.keys()),
        'gcp': list(GCP_SERVICES.keys())
    }
    regions_by_cloud = {
        'aws': AWS_REGIONS,
        'azure': AZURE_REGIONS,
        'gcp': GCP_REGIONS
    }

    schedule = {d.isoformat(): {} for d in dates}
    anomalies_manifest = []

    def add_anomaly(a_type: str, start_d: datetime.date, end_d: datetime.date, cloud: str, service: str, region: str, severity: str, desc: str, mult_func):
        a_id = str(uuid.uuid4())
        # Track for manifest
        anom_entry = {
            "anomaly_id": a_id,
            "anomaly_type": a_type,
            "cloud_provider": cloud,
            "service": service,
            "region": region,
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "severity": severity,
            "description": desc,
            "affected_record_ids": [] # Will be populated during generation
        }
        anomalies_manifest.append(anom_entry)

        # Apply to schedule
        curr_d = start_d
        day_offset = 0
        total_a_days = (end_d - start_d).days + 1
        while curr_d <= end_d:
            d_str = curr_d.isoformat()
            if d_str not in schedule:
                curr_d += datetime.timedelta(days=1)
                day_offset += 1
                continue
            
            mult = mult_func(day_offset, total_a_days)
            key = (cloud, service, region)
            
            existing = schedule[d_str].get(key)
            if existing is None or mult > existing["multiplier"]:
                schedule[d_str][key] = {
                    "multiplier": mult,
                    "anomaly_id": a_id,
                    "anomaly_type": a_type,
                    "severity": severity,
                    "is_anomaly": True
                }
                
            curr_d += datetime.timedelta(days=1)
            day_offset += 1

    # 1. Budget Breach Pass (Pass 1)
    # Estimate baseline per month. Instead of doing full random sum, we just mark events.
    # 2 events per cloud per year -> 4 total per cloud.
    for cloud in clouds:
        years = [start_date.year, start_date.year + 1] # approx 2 years
        events_injected = 0
        while events_injected < 4:
            yr = random.choice(years)
            mo = random.randint(1, 12)
            # Find an arbitrary 10-day period in the first half of the month to spike costs 3x
            # to trigger the breach mid-month.
            try:
                dt_spike_start = datetime.date(yr, mo, 5)
            except ValueError:
                continue
            dt_spike_end = dt_spike_start + datetime.timedelta(days=9)
            if dt_spike_end > end_date:
                continue
            
            # Month end
            import calendar
            _, last = calendar.monthrange(yr, mo)
            dt_month_end = datetime.date(yr, mo, last)

            d_str_start = dt_spike_start.isoformat()
            d_str_end = dt_month_end.isoformat()
            
            a_id = str(uuid.uuid4())
            anom_entry = {
                "anomaly_id": a_id,
                "anomaly_type": "budget_breach",
                "cloud_provider": cloud,
                "service": "multiple",
                "region": "multiple",
                "start_date": d_str_start,
                "end_date": d_str_end,
                "severity": "critical",
                "description": f"{cloud} Budget Breach in {yr}-{mo:02}",
                "affected_record_ids": []
            }
            anomalies_manifest.append(anom_entry)

            curr_d = dt_spike_start
            while curr_d <= dt_month_end:
                d_str = curr_d.isoformat()
                if d_str in schedule:
                    mult = 3.0 if curr_d <= dt_spike_end else 1.5 # Elevated cost 
                    for svc in services_by_cloud[cloud]:
                        for reg in regions_by_cloud[cloud]:
                            key = (cloud, svc, reg)
                            existing = schedule[d_str].get(key)
                            if existing is None or mult > existing["multiplier"]:
                                schedule[d_str][key] = {
                                    "multiplier": mult,
                                    "anomaly_id": a_id,
                                    "anomaly_type": "budget_breach",
                                    "severity": "critical",
                                    "is_anomaly": True
                                }
                curr_d += datetime.timedelta(days=1)
            events_injected += 1

    # Apply standard random anomalies
    for d in dates:
        # POINT_SPIKE (3% of days)
        if rng.random() < 0.03:
            c = rng.choice(clouds)
            s = rng.choice(services_by_cloud[c])
            r = rng.choice(regions_by_cloud[c])
            mlt = rng.uniform(4.5, 8.0)
            sev = rng.choice(["high", "critical"])
            add_anomaly("point_spike", d, d, c, s, r, sev, f"Point spike {mlt:.1f}x", lambda off, tot: mlt)

        # SUSTAINED_ELEVATION (2% of days)
        if rng.random() < 0.02:
            c = rng.choice(clouds)
            s = rng.choice(services_by_cloud[c])
            r = rng.choice(regions_by_cloud[c])
            duration = rng.integers(5, 14)
            mlt = rng.uniform(2.0, 3.5)
            # Find end date safely
            end_d = d + datetime.timedelta(days=int(duration))
            if end_d <= end_date:
                add_anomaly("sustained_elevation", d, end_d, c, s, r, rng.choice(["medium", "high"]), f"Sustained {mlt:.1f}x", lambda off, tot: mlt)

    # GRADUAL_DRIFT (4 instances total)
    for _ in range(4):
        c = rng.choice(clouds)
        s = rng.choice(services_by_cloud[c])
        r = rng.choice(regions_by_cloud[c])
        dur = rng.integers(21, 45)
        d_idx = rng.integers(0, total_days - dur - 1)
        start_d = dates[d_idx]
        end_d = start_d + datetime.timedelta(days=int(dur))
        
        def drift_mult(off, tot_days):
            progress = off / max(1, (tot_days - 1))
            return 1.0 + (1.8 * progress)
            
        add_anomaly("gradual_drift", start_d, end_d, c, s, r, "medium", "Cost drift 1.0x to 2.8x", drift_mult)

    # SUDDEN_DROP (6 instances total)
    for _ in range(6):
        c = rng.choice(clouds)
        s = rng.choice(services_by_cloud[c])
        r = rng.choice(regions_by_cloud[c])
        dur = rng.integers(1, 3)
        d_idx = rng.integers(0, total_days - dur - 1)
        start_d = dates[d_idx]
        end_d = start_d + datetime.timedelta(days=int(dur))
        mlt = rng.uniform(0.05, 0.15)
        add_anomaly("sudden_drop", start_d, end_d, c, s, r, "medium", f"Drop to {mlt:.2f}x", lambda off, tot: mlt)

    # MULTI_SERVICE_CASCADE (3 instances total)
    for _ in range(3):
        c = rng.choice(clouds)
        # pick primary and 2 secondaries
        svcs = rng.choice(services_by_cloud[c], size=3, replace=False)
        r = rng.choice(regions_by_cloud[c])
        dur = rng.integers(3, 7)
        d_idx = rng.integers(0, total_days - dur - 1)
        start_d = dates[d_idx]
        end_d = start_d + datetime.timedelta(days=int(dur))
        
        # Primary
        add_anomaly("multi_service_cascade", start_d, end_d, c, svcs[0], r, "critical", "Cascade primary 4x", lambda off, tot: 4.0)
        # Secondary
        sec_start = start_d + datetime.timedelta(days=1)
        add_anomaly("multi_service_cascade", sec_start, end_d, c, svcs[1], r, "critical", "Cascade secondary 2.5x", lambda off, tot: 2.5)
        add_anomaly("multi_service_cascade", sec_start, end_d, c, svcs[2], r, "critical", "Cascade secondary 2.5x", lambda off, tot: 2.5)

    # ZERO_COST_GAP (5 instances total)
    for _ in range(5):
        c = rng.choice(clouds)
        s = rng.choice(services_by_cloud[c])
        r = rng.choice(regions_by_cloud[c])
        dur = rng.integers(2, 4)
        d_idx = rng.integers(0, total_days - dur - 1)
        start_d = dates[d_idx]
        end_d = start_d + datetime.timedelta(days=int(dur))
        add_anomaly("zero_cost_gap", start_d, end_d, c, s, r, "medium", "API Failure (0 cost)", lambda off, tot: 0.0)

    # TAG_EXPLOSION (4 instances total)
    for _ in range(4):
        c = rng.choice(clouds)
        s = rng.choice(services_by_cloud[c])
        r = rng.choice(regions_by_cloud[c])
        d_idx = rng.integers(0, total_days - 1)
        d = dates[d_idx]
        add_anomaly("tag_explosion", d, d, c, s, r, "low", "Tag Explosion", lambda off, tot: 1.0) # 1.0 mult, handled in generator

    # CROSS_REGION_TRANSFER_SPIKE (5 instances total)
    transfer_svcs = {"aws": ["S3"], "azure": ["Blob Storage"], "gcp": ["Cloud Storage"]}
    for _ in range(5):
        c = rng.choice(clouds)
        s = transfer_svcs[c][0]
        r = rng.choice(regions_by_cloud[c])
        dur = rng.integers(1, 3)
        d_idx = rng.integers(0, total_days - dur - 1)
        start_d = dates[d_idx]
        end_d = start_d + datetime.timedelta(days=int(dur))
        mlt = rng.uniform(5.0, 9.0)
        add_anomaly("cross_region_transfer_spike", start_d, end_d, c, s, r, "high", f"X-Region Spike {mlt:.1f}x", lambda off, tot: mlt)

    # RESERVED_INSTANCE_EXPIRY (6 instances total)
    vm_svcs = {"aws": ["EC2"], "azure": ["Virtual Machines"], "gcp": ["Compute Engine"]}
    for _ in range(6):
        c = rng.choice(clouds)
        s = vm_svcs[c][0]
        r = rng.choice(regions_by_cloud[c])
        dur = 7
        d_idx = rng.integers(0, total_days - dur - 1)
        start_d = dates[d_idx]
        end_d = start_d + datetime.timedelta(days=dur)
        mlt = rng.uniform(2.2, 2.8)
        add_anomaly("reserved_instance_expiry", start_d, end_d, c, s, r, "medium", f"RI Expiry {mlt:.1f}x", lambda off, tot: mlt)

    return schedule, anomalies_manifest
