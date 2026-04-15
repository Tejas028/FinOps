from typing import Dict

REGION_NORMALIZATION_MAP: Dict[str, str] = {
    # ── US East ───────────────────────────────────────────────
    "us-east-1": "us-east",
    "us-east-2": "us-east",
    "eastus": "us-east",
    "eastus2": "us-east",
    "us-east1": "us-east",
    "us-east4": "us-east",

    # ── US West ───────────────────────────────────────────────
    "us-west-1": "us-west",
    "us-west-2": "us-west",
    "westus": "us-west",
    "westus2": "us-west",
    "westus3": "us-west",
    "us-west1": "us-west",
    "us-west2": "us-west",
    "us-west3": "us-west",
    "us-west4": "us-west",
    "us-central1": "us-central",
    "centralus": "us-central",

    # ── Europe ────────────────────────────────────────────────
    "eu-west-1": "europe-west",
    "eu-west-2": "europe-west",
    "eu-west-3": "europe-west",
    "eu-central-1": "europe-central",
    "eu-north-1": "europe-north",
    "eu-south-1": "europe-south",
    "northeurope": "europe-north",
    "westeurope": "europe-west",
    "germanywestcentral": "europe-central",
    "swedencentral": "europe-north",
    "europe-west1": "europe-west",
    "europe-west2": "europe-west",
    "europe-west3": "europe-central",
    "europe-west4": "europe-west",
    "europe-west6": "europe-central",
    "europe-north1": "europe-north",
    "europe-central2": "europe-central",

    # ── Asia Pacific ──────────────────────────────────────────
    "ap-southeast-1": "asia-southeast",
    "ap-southeast-2": "asia-southeast",
    "ap-northeast-1": "asia-northeast",
    "ap-northeast-2": "asia-northeast",
    "ap-northeast-3": "asia-northeast",
    "ap-south-1": "asia-south",
    "ap-east-1": "asia-east",
    "southeastasia": "asia-southeast",
    "eastasia": "asia-east",
    "japaneast": "asia-northeast",
    "koreacentral": "asia-northeast",
    "australiaeast": "asia-pacific",
    "asia-east1": "asia-east",
    "asia-east2": "asia-east",
    "asia-northeast1": "asia-northeast",
    "asia-northeast2": "asia-northeast",
    "asia-southeast1": "asia-southeast",
    "asia-southeast2": "asia-southeast",
    "asia-south1": "asia-south",

    # ── South America ─────────────────────────────────────────
    "sa-east-1": "south-america",
    "brazilsouth": "south-america",
    "southamerica-east1": "south-america",

    # ── Middle East / Africa ──────────────────────────────────
    "me-south-1": "middle-east",
    "uaenorth": "middle-east",
    "af-south-1": "africa",

    # ── Global / Unknown ──────────────────────────────────────
    "global": "global"
}

def normalize_region(region_raw: str) -> str:
    if not region_raw:
        return "unknown"
    lower_reg = region_raw.lower().strip()
    return REGION_NORMALIZATION_MAP.get(lower_reg, region_raw)
