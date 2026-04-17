import logging
from datetime import date
from typing import List
from rich.table import Table
from rich.console import Console

import pandas as pd
from storage.client import StorageClient
from storage.db import DatabaseManager
from forecasting import config
from forecasting.models.prophet_model import ProphetModel
from forecasting.models.lightgbm_model import LightGBMModel
from forecasting.models.ensemble import EnsembleForecaster
from shared.schemas.forecast import ForecastResult

logger = logging.getLogger(__name__)

class ForecastingEngine:
    def __init__(self, storage_client: StorageClient, force_retrain: bool = False):
        self.storage_client = storage_client
        self.force_retrain = force_retrain
        self.ensemble = EnsembleForecaster()
        self.console = Console()

    def run(self, cloud_provider: str, start_date: date, end_date: date) -> List[ForecastResult]:
        logger.info(f"Starting forecasting for {cloud_provider} from {start_date} to {end_date}")
        
        # Step 1: LOAD FEATURES
        # Ensure we alias to match prompt API constraints natively!
        query = """
        SELECT 
            feature_date as usage_date, 
            cloud_provider, 
            service_category as service,
            SUM(total_cost_usd) as cost_usd,
            AVG(rolling_mean_7d) as rolling_mean_7d,
            AVG(rolling_mean_30d) as rolling_mean_30d,
            AVG(rolling_std_7d) as rolling_std_7d,
            AVG(rolling_std_30d) as rolling_std_30d,
            AVG(cost_lag_1d) as lag_1d,
            AVG(cost_lag_7d) as lag_7d,
            AVG(cost_lag_30d) as lag_30d,
            AVG(pct_change_7d) as pct_change_7d,
            AVG(day_of_week) as day_of_week,
            MAX(is_weekend::int) as is_weekend,
            MAX(is_month_end::int) as is_month_end
        FROM spend_features
        WHERE feature_date BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if cloud_provider and cloud_provider.lower() != "all":
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)

        query += " GROUP BY feature_date, cloud_provider, service_category ORDER BY feature_date ASC"

        with DatabaseManager.get_connection() as conn:
            df = pd.read_sql(query, conn, params=tuple(params))

        if df.empty:
            logger.warning("No data found for the given criteria.")
            print("No data found in spend_features.")
            return []
            
        # Step 2: PREPARE PER-GROUP DataFrames
        groups = df.groupby(['cloud_provider', 'service'])
        
        all_forecasts: List[ForecastResult] = []
        all_metadata: List[dict] = []
        
        summary_rows = []

        # Enforce max horizon calculation
        max_horizon = max(config.FORECAST_HORIZONS)

        for (cloud, service), group_df in groups:
            group_df = group_df.sort_values(by="usage_date").reset_index(drop=True)
            
            n_rows = len(group_df)
            if n_rows < config.MIN_ROWS_FOR_LGBM:
                logger.info(f"Skipping {cloud}-{service}: too few rows ({n_rows})")
                continue

            # Step 3: FIT MODELS
            prophet = ProphetModel(cloud_provider=cloud, service=service)
            lgbm = LightGBMModel(cloud_provider=cloud, service=service)

            p_mape = -1.0
            l_mape = -1.0
            
            if not self.force_retrain:
                try:
                    prophet.load(config.MODEL_REGISTRY_PATH)
                    if hasattr(prophet, 'metadata') and "test_mape" in prophet.metadata:
                        p_mape = prophet.metadata["test_mape"]
                except Exception as e:
                    logger.debug(f"Could not load Prophet for {cloud}-{service}: {e}")
                    
                try:
                    lgbm.load(config.MODEL_REGISTRY_PATH)
                    if hasattr(lgbm, 'metadata') and "test_mape" in lgbm.metadata:
                        l_mape = lgbm.metadata["test_mape"]
                except Exception as e:
                    logger.debug(f"Could not load LightGBM for {cloud}-{service}: {e}")

            if self.force_retrain or not prophet.model:
                try:
                    if n_rows >= config.MIN_ROWS_FOR_PROPHET:
                        p_meta = prophet.fit(group_df)
                        prophet.save(config.MODEL_REGISTRY_PATH)
                        p_mape = p_meta.get("test_mape", -1.0)
                except Exception as e:
                    logger.error(f"Prophet failed for {cloud}-{service}: {e}")

            if self.force_retrain or not lgbm.models:
                try:
                    l_meta = lgbm.fit(group_df)
                    lgbm.save(config.MODEL_REGISTRY_PATH)
                    l_mape = l_meta.get("test_mape", -1.0)
                except Exception as e:
                    logger.error(f"LightGBM failed for {cloud}-{service}: {e}")

            # Step 4: PREDICT ALL HORIZONS
            p_outputs, l_outputs = [], []
            try:
                if prophet.model:
                    p_outputs = prophet.predict(horizon_days=max_horizon)
            except Exception as e:
                logger.error(f"Prophet prediction failed for {cloud}-{service}: {e}")
                
            try:
                if lgbm.models:
                    l_outputs = lgbm.predict(horizon_days=max_horizon)
            except Exception as e:
                logger.error(f"LightGBM prediction failed for {cloud}-{service}: {e}")

            # Step 5: ENSEMBLE BLEND
            if not p_outputs and not l_outputs:
                continue
                
            forecasts, meta = self.ensemble.blend(
                prophet_outputs=p_outputs,
                lgbm_outputs=l_outputs,
                prophet_mape=max(p_mape, 0),
                lgbm_mape=max(l_mape, 0)
            )

            if forecasts:
                all_forecasts.extend(forecasts)
                all_metadata.extend(meta)
                
                # Setup summary row
                p_mape_str = f"{p_mape*100:.1f}%" if p_mape >= 0 else "N/A"
                l_mape_str = f"{l_mape*100:.1f}%" if l_mape >= 0 else "N/A"
                
                sum_pw = meta[0]["prophet_weight"]
                sum_lw = meta[0]["lgbm_weight"]
                weight_str = f"{sum_pw*100:.0f}% / {sum_lw*100:.0f}%"
                
                summary_rows.append((cloud, service, str(n_rows), p_mape_str, l_mape_str, weight_str, str(len(forecasts))))

        # Step 6: WRITE TO DB
        written = 0
        if all_forecasts:
            try:
                written = self.storage_client.write_forecasts(all_forecasts, all_metadata)
            except Exception as e:
                logger.error(f"Failed to write forecasts to DB: {e}")
                print(f"Warning: DB write failed: {e}")

        # Step 7: PRINT SUMMARY
        table = Table(title="[bold green]Forecasting Summary[/bold green]")
        table.add_column("Cloud", justify="left", style="cyan")
        table.add_column("Service", justify="left", style="magenta")
        table.add_column("Train Rows", justify="right")
        table.add_column("Prophet MAPE", justify="right")
        table.add_column("LGBM MAPE", justify="right")
        table.add_column("Ensemble Weight P/L", justify="center")
        table.add_column("Forecasts Written", justify="right")

        for r in summary_rows:
            table.add_row(*r)

        print("\n" + "="*60)
        self.console.print(table)
        print(f"Total forecast rows written: {written}")
        print(f"Horizons covered: {', '.join([str(h)+'d' for h in config.FORECAST_HORIZONS])}")
        print(f"Groups forecasted: {len(summary_rows)}")
        print("="*60 + "\n")

        return all_forecasts
