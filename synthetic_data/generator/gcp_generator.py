GCP_SERVICES = {
    "Compute Engine": (3600, 380),
    "Cloud Storage": (820,  95),
    "BigQuery": (1500, 200),
    "Cloud SQL": (1100, 130),
    "GKE": (1800, 240),
    "Cloud Run": (290,  55),
    "Pub/Sub": (340,  40),
    "Vertex AI": (870,  190),
    "Cloud Spanner": (1200, 160),
    "Dataflow": (680,  85),
    "Firestore": (420,  50),
    "Cloud Armor": (210,  30)
}

GCP_REGIONS = [
    "us-central1", "us-west1", "europe-west1", "asia-east1",
    "australia-southeast1", "northamerica-northeast1"
]

GCP_GLOBAL_SERVICES = ["BigQuery", "Pub/Sub"]

GCP_PROJECT_IDS = ["gcp-proj-001", "gcp-proj-002", "gcp-proj-003"]
