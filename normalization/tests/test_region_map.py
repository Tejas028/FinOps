from normalization.maps.region_map import normalize_region

def test_aws_region_code():
    assert normalize_region("us-east-1") == "us-east"

def test_azure_region_name():
    assert normalize_region("eastus") == "us-east"

def test_gcp_region():
    assert normalize_region("europe-west1") == "europe-west"

def test_unknown_region_passes_through():
    assert normalize_region("mars-north-1") == "mars-north-1"

def test_empty_string():
    assert normalize_region("") == "unknown"
