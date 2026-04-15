from typing import List
from datetime import datetime
import time

from pydantic import BaseModel
from shared.schemas.billing import BillingRecord
from shared.schemas.normalized import NormalizedRecord

from .tag_parser import TagParser
from .currency import CurrencyNormalizer
from .deduplicator import Deduplicator, generate_fingerprint
from .maps.service_map import normalize_service
from .maps.region_map import normalize_region

class NormalizationResult(BaseModel):
    records: List[NormalizedRecord]
    input_count: int
    output_count: int
    duplicate_count: int
    processing_time_seconds: float
    errors: List[str] = []

class NormalizationPipeline:
    def __init__(self):
        self.tag_parser = TagParser()
        self.currency_normalizer = CurrencyNormalizer()
        self.deduplicator = Deduplicator()

    def normalize(self, records: List[BillingRecord], deduplicate: bool = True) -> NormalizationResult:
        start_time = time.time()
        
        normalized_records = []
        duplicate_count = 0
        input_count = len(records)
        errors = []

        for record in records:
            fp = generate_fingerprint(record)
            if deduplicate and self.deduplicator.is_duplicate(fp):
                duplicate_count += 1
                continue
                
            if deduplicate:
                self.deduplicator.mark_seen(fp)

            try:
                norm_record = self.normalize_single(record, override_fingerprint=fp)
                normalized_records.append(norm_record)
            except Exception as e:
                errors.append(f"Error normalizing record {record.record_id}: {str(e)}")

        process_time = time.time() - start_time
        
        return NormalizationResult(
            records=normalized_records,
            input_count=input_count,
            output_count=len(normalized_records),
            duplicate_count=duplicate_count,
            processing_time_seconds=process_time,
            errors=errors
        )

    def normalize_single(self, record: BillingRecord, override_fingerprint: str = None) -> NormalizedRecord:
        fp = override_fingerprint or generate_fingerprint(record)
        
        tags_dict, env, team = self.tag_parser.parse(record.tags)
        
        service_category = normalize_service(record.service)
        region = normalize_region(record.region or "")
        cost_usd = self.currency_normalizer.to_usd(record.cost_usd, record.original_currency)

        return NormalizedRecord(
            fingerprint=fp,
            cloud_provider=record.cloud_provider,
            account_id=record.account_id,
            service_name_raw=record.service,
            service_category=service_category,
            region=region,
            resource_id=record.resource_id,
            usage_date=record.usage_date,
            cost_original=record.original_cost,
            currency_original=record.original_currency,
            cost_usd=cost_usd,
            usage_quantity=None, # Not in billing output currently
            usage_unit=None, # Not in billing output currently
            tags_raw=record.tags,
            tags=tags_dict,
            environment=env,
            team=team
        )
