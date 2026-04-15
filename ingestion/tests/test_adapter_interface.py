import pytest
import os
from datetime import date
from ingestion.base_adapter import BaseIngestionAdapter
from ingestion.adapters.aws_adapter import AWSCURAdapter
from ingestion.adapters.azure_adapter import AzureCostAdapter
from ingestion.adapters.gcp_adapter import GCPBillingAdapter

def test_adapters_implement_interface():
    aws = AWSCURAdapter()
    azure = AzureCostAdapter()
    gcp = GCPBillingAdapter()
    
    for adapter in [aws, azure, gcp]:
        assert isinstance(adapter, BaseIngestionAdapter)
        assert hasattr(adapter, 'fetch')
        assert hasattr(adapter, 'validate_connection')
        assert hasattr(adapter, 'cloud_provider')

def test_validate_connection_returns_false_without_creds(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    
    aws = AWSCURAdapter()
    azure = AzureCostAdapter()
    gcp = GCPBillingAdapter()
    
    for adapter in [aws, azure, gcp]:
        assert adapter.validate_connection() is False

def test_fetch_returns_empty_without_creds(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    
    aws = AWSCURAdapter()
    azure = AzureCostAdapter()
    gcp = GCPBillingAdapter()
    
    for adapter in [aws, azure, gcp]:
        res = adapter.fetch(date(2023, 1, 1), date(2023, 1, 2))
        assert res == []
