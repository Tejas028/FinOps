from normalization.maps.service_map import normalize_service

def test_known_aws_service():
    assert normalize_service("AmazonEC2") == "compute"

def test_known_azure_service():
    assert normalize_service("Azure Blob Storage") == "storage"

def test_known_gcp_service():
    assert normalize_service("BigQuery") == "database"

def test_unknown_service():
    assert normalize_service("SomeFutureService") == "other"

def test_case_insensitivity():
    assert normalize_service("AMAZON S3") == normalize_service("amazon s3")
