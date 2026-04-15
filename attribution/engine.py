import time
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from rich.table import Table
from rich.console import Console

import pandas as pd

from attribution.config import MIN_ROWS_FOR_TRAINING, SHAP_FEATURE_COLUMNS
from attribution.model import AttributionModel
from attribution.repository import AttributionRepository
from shared.schemas.attribution import AttributionRecord

class AttributionEngineResult(BaseModel):
    groups_processed: int
    groups_skipped: int
    attributions_written: int
    duration_seconds: float
    avg_r2_score: float
    errors: List[str] = []

class AttributionEngine:
    def __init__(self, repository: AttributionRepository):
        self.repo = repository
        self.console = Console()

    def run(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,
        force_retrain: bool = False
    ) -> AttributionEngineResult:
        
        start_time = time.time()
        result = AttributionEngineResult(
            groups_processed=0,
            groups_skipped=0,
            attributions_written=0,
            duration_seconds=0.0,
            avg_r2_score=0.0,
            errors=[]
        )
        
        # Get target groups
        groups = self.repo.get_all_groups()
        if cloud_provider and cloud_provider.lower() != 'all':
            groups = [g for g in groups if g['cloud_provider'] == cloud_provider]
            
        r2_scores = []
        summary_rows = []

        for group in groups:
            cloud = group['cloud_provider']
            service = group['service_category']
            
            try:
                # 1. Fetch features
                raw_data = self.repo.get_features_for_group(cloud, service, start_date, end_date)
                df = pd.DataFrame(raw_data)
                
                # 2. Skip condition
                if df.empty or len(df) < MIN_ROWS_FOR_TRAINING:
                    result.groups_skipped += 1
                    continue
                    
                # 3. Model init
                model = AttributionModel(cloud_provider=cloud, service_category=service)
                if force_retrain or not model.load():
                    fit_stats = model.fit(df)
                    
                # 4. Explain features
                shap_df = model.explain(df)
                
                # 5. Build records
                records_to_write = []
                # Keep track of the top driver for the group summary table
                group_top_driver = None
                
                for idx, row in shap_df.iterrows():
                    shap_vals = {feat: float(row[feat]) for feat in SHAP_FEATURE_COLUMNS if feat in row}
                    top_drivers = model.extract_top_drivers(pd.Series(shap_vals), n=3)
                    
                    if not group_top_driver and top_drivers:
                        group_top_driver = top_drivers[0]["feature"]
                    
                    # Safely extract top 1, 2, 3
                    td_names = [None, None, None]
                    td_vals = [None, None, None]
                    for i, td in enumerate(top_drivers):
                        td_names[i] = td["feature"]
                        td_vals[i] = td["value"]
                        
                    # Reference original df for account, environment, team
                    orig_row = raw_data[idx] 
                        
                    record = AttributionRecord(
                        attribution_date=row['usage_date'],
                        cloud_provider=cloud,
                        service_category=service,
                        account_id=orig_row['account_id'],
                        environment=orig_row['environment'],
                        team=orig_row['team'],
                        total_cost_usd=float(row['total_cost_usd']),
                        shap_values=shap_vals,
                        top_driver_1=td_names[0],
                        top_driver_1_value=td_vals[0],
                        top_driver_2=td_names[1],
                        top_driver_2_value=td_vals[1],
                        top_driver_3=td_names[2],
                        top_driver_3_value=td_vals[2],
                        model_r2_score=model.r2_score_,
                        feature_count=len(shap_vals)
                    )
                    records_to_write.append(record)
                
                # 6. Push to DB
                written = self.repo.upsert_attributions(records_to_write)
                result.attributions_written += written
                result.groups_processed += 1
                
                if model.r2_score_ is not None:
                    r2_scores.append(model.r2_score_)
                    
                summary_rows.append((cloud, service, str(len(df)), f"{model.r2_score_:.2f}", group_top_driver or "None"))
                
            except Exception as e:
                err_msg = f"Error processing {cloud}/{service}: {e}"
                result.errors.append(err_msg)
                print(err_msg)

        # 7. Aggregate results
        if r2_scores:
            result.avg_r2_score = sum(r2_scores) / len(r2_scores)
            
        result.duration_seconds = time.time() - start_time
        
        # 8. Print Summary
        table = Table(title="[bold blue]Attribution Summary[/bold blue]")
        table.add_column("Cloud", style="cyan")
        table.add_column("Service", style="magenta")
        table.add_column("Rows", justify="right")
        table.add_column("R²", justify="right")
        table.add_column("Top Driver", justify="left")
        
        for r in summary_rows:
            table.add_row(*r)
            
        print("\n" + "="*50)
        self.console.print(table)
        print("="*50 + "\n")
        
        return result
