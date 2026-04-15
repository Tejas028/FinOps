from typing import Dict

SERVICE_CATEGORY_MAP: Dict[str, str] = {
    # ── Compute ───────────────────────────────────────────────
    "amazonec2": "compute",
    "amazon ec2": "compute",
    "virtual machines": "compute",
    "compute engine": "compute",
    "aws lambda": "compute",
    "azure functions": "compute",
    "cloud functions": "compute",
    "amazon lightsail": "compute",
    "azure kubernetes service": "compute",
    "google kubernetes engine": "compute",
    "amazon eks": "compute",
    "aks": "compute",

    # ── Storage ───────────────────────────────────────────────
    "amazon s3": "storage",
    "amazon s3 glacier": "storage",
    "azure blob storage": "storage",
    "cloud storage": "storage",
    "amazon ebs": "storage",
    "azure disk storage": "storage",
    "persistent disk": "storage",
    "amazon efs": "storage",
    "azure files": "storage",
    "filestore": "storage",

    # ── Database ──────────────────────────────────────────────
    "amazon rds": "database",
    "amazon dynamodb": "database",
    "amazon redshift": "database",
    "amazon elasticache": "database",
    "azure sql database": "database",
    "azure cosmos db": "database",
    "azure cache for redis": "database",
    "cloud sql": "database",
    "cloud spanner": "database",
    "cloud bigtable": "database",
    "bigquery": "database",
    "firestore": "database",

    # ── Networking ────────────────────────────────────────────
    "amazon vpc": "networking",
    "amazon cloudfront": "networking",
    "amazon route 53": "networking",
    "azure virtual network": "networking",
    "azure load balancer": "networking",
    "azure application gateway": "networking",
    "cloud cdn": "networking",
    "cloud dns": "networking",
    "cloud load balancing": "networking",
    "aws direct connect": "networking",
    "azure expressroute": "networking",
    "cloud interconnect": "networking",

    # ── AI / ML ───────────────────────────────────────────────
    "amazon sagemaker": "ai_ml",
    "amazon rekognition": "ai_ml",
    "amazon comprehend": "ai_ml",
    "azure machine learning": "ai_ml",
    "azure cognitive services": "ai_ml",
    "azure openai service": "ai_ml",
    "vertex ai": "ai_ml",
    "cloud ai platform": "ai_ml",

    # ── Monitoring / Management ───────────────────────────────
    "amazon cloudwatch": "monitoring",
    "aws cloudtrail": "monitoring",
    "azure monitor": "monitoring",
    "log analytics": "monitoring",
    "cloud monitoring": "monitoring",
    "cloud logging": "monitoring",
    "aws config": "monitoring",

    # ── Security ──────────────────────────────────────────────
    "aws waf": "security",
    "aws shield": "security",
    "aws kms": "security",
    "amazon guardduty": "security",
    "azure defender": "security",
    "azure key vault": "security",
    "cloud armor": "security",
    "cloud kms": "security",
    "secret manager": "security",

    # ── Support / Tax ─────────────────────────────────────────
    "aws support": "support",
    "azure support": "support",
    "tax": "tax",
}

def normalize_service(service_name_raw: str) -> str:
    if not service_name_raw:
        return "other"
    lower_name = service_name_raw.lower().strip()
    return SERVICE_CATEGORY_MAP.get(lower_name, "other")
