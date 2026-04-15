import uuid
from typing import List, Tuple, Dict
from datetime import datetime

from forecasting import config
from forecasting.models.base_model import ForecastOutput
from shared.schemas.forecast import ForecastResult

class EnsembleForecaster:
    def blend(
        self,
        prophet_outputs: List[ForecastOutput],
        lgbm_outputs: List[ForecastOutput],
        prophet_mape: float,
        lgbm_mape: float
    ) -> Tuple[List[ForecastResult], List[dict]]:
        
        # Determine weighting logic
        has_prophet = len(prophet_outputs) > 0 and prophet_mape > 0
        has_lgbm = len(lgbm_outputs) > 0 and lgbm_mape > 0

        p_weight = config.ENSEMBLE_PROPHET_WEIGHT_DEFAULT
        l_weight = config.ENSEMBLE_LGBM_WEIGHT_DEFAULT

        if has_prophet and has_lgbm:
            total_mape = prophet_mape + lgbm_mape
            if total_mape > 0:
                p_weight = lgbm_mape / total_mape
                l_weight = prophet_mape / total_mape
        elif has_prophet and not has_lgbm:
            p_weight = 1.0
            l_weight = 0.0
        elif has_lgbm and not has_prophet:
            p_weight = 0.0
            l_weight = 1.0

        # Map predictions by (forecast_date)
        prophet_map: Dict[str, ForecastOutput] = {
            str(po.forecast_date): po for po in prophet_outputs
        }
        lgbm_map: Dict[str, ForecastOutput] = {
            str(lo.forecast_date): lo for lo in lgbm_outputs
        }

        # The prediction dates overlap should be identical or union
        all_dates = set(prophet_map.keys()).union(set(lgbm_map.keys()))
        
        results: List[ForecastResult] = []
        metadata: List[dict] = []
        now = datetime.now()

        for d_str in sorted(list(all_dates)):
            po = prophet_map.get(d_str)
            lo = lgbm_map.get(d_str)

            # Need at least one valid prediction
            if not po and not lo:
                continue

            # Fallback handling for mismatched dates
            # (e.g. Prophet generated 30 days, LightGBM only generated 4 horizons 7, 14, 30, 90)
            # wait, LightGBM predict() only generates outputs for specifically H days! 
            # Prophet generates all days up to H.
            # Thus, we only blend if both exist OR just use what we have. 
            # In forecasts, we want to store specifically for the 4 horizons basically, but Prophet has all.
            # Wait, do we want to write all Prophet days? The prompt says "Forecasts are generated for 4 horizons: 7, 14, 30, 90 days."
            # So I should only care about horizons matching `config.FORECAST_HORIZONS`. Let's filter dates to only those matching target horizons.
            # Mappings for LightGBM are exact. So let's only loop through LightGBM mapped dates if LGBM ran, OR we filter Prophet outputs explicitly.
            
            # Since LightGBM emits specifically H horizons, let's just pick the Horizon from the object
            horizon_days = po.horizon_days if po else lo.horizon_days
            valid_horizons = config.FORECAST_HORIZONS
            
            # We must be exact. Since LightGBM specifically outputs horizon_days, Prophet outputs horizon_days for the max horizon in loop.
            # Actually, Prophet Outputs don't natively tag with `H` properly because it outputs a continuous range. 
            # In ProphetModel I did `horizon_days=horizon_days` for all rows. I must compute true horizon!
            
            # Recompute true horizon if we only want exact match.
            # But the requirement from Prompt: "Predict all horizons: prophet = prophet.predict(max(HORIZONS)). Blends outputs".
            # The prompt says: "Both return outputs for dates covering all 4 horizons. Filter by horizon_days in ensemble step".
            # This means I need to only yield if it corresponds to an exact horizon!
            pass

        # Let's fix the logic based on dates.
        # Actually, LGBM explicitly returns List[ForecastOutput] with correct `horizon_days`.
        # Prophet outputs a list where `horizon_days` is just the `max(horizon)` passed in. 
        # But we know the target date for a horizon `H` = last_date + H days.
        # LGBM dates are exactly the target dates.
        # So we can just use the LGBM dates, or if LGBM failed, we can derive target dates from the Prophet results start_date.
        # Let's cleanly filter the Prophet outputs to ONLY the target horizons.
        
        # Determine the "origin" date to calculate target dates
        # The first date in Prophet outputs is usually origin + 1 day.
        # Or from LightGBM.
        
        origin_date = None
        if lgbm_outputs:
            # We can back-calculate origin from horizon
            lo = lgbm_outputs[0]
            from datetime import timedelta
            origin_date = lo.forecast_date - timedelta(days=lo.horizon_days)
        elif prophet_outputs:
            p_dates = sorted([po.forecast_date for po in prophet_outputs])
            from datetime import timedelta
            origin_date = p_dates[0] - timedelta(days=1)
            
        if not origin_date:
            return [], []
            
        target_dates = {}
        from datetime import timedelta
        for h in config.FORECAST_HORIZONS:
            target_dates[str(origin_date + timedelta(days=h))] = h
            
        for d_str, h_days in target_dates.items():
            po = prophet_map.get(d_str)
            lo = lgbm_map.get(d_str)

            if not po and not lo:
                continue
                
            cur_p_weight = p_weight
            cur_l_weight = l_weight
            
            p_pred = po.predicted_cost if po else 0.0
            l_pred = lo.predicted_cost if lo else 0.0
            
            if po and lo:
                pred = (p_pred * cur_p_weight) + (l_pred * cur_l_weight)
                lb = min(po.lower_bound, lo.lower_bound)
                ub = max(po.upper_bound, lo.upper_bound)
            elif po:
                pred = p_pred
                lb = po.lower_bound
                ub = po.upper_bound
                cur_p_weight = 1.0
                cur_l_weight = 0.0
            elif lo:
                pred = l_pred
                lb = lo.lower_bound
                ub = lo.upper_bound
                cur_p_weight = 0.0
                cur_l_weight = 1.0

            base = po if po else lo
            
            fr = ForecastResult(
                forecast_id=str(uuid.uuid4()),
                cloud_provider=base.cloud_provider,
                service=base.service,
                region=None,
                horizon_days=h_days,
                forecast_date=base.forecast_date,
                predicted_cost=pred,
                lower_bound=lb,
                upper_bound=ub,
                model_used="ensemble",
                generated_at=now
            )
            
            meta = {
                "prophet_prediction": float(p_pred) if po else None,
                "lgbm_prediction": float(l_pred) if lo else None,
                "prophet_weight": float(cur_p_weight),
                "lgbm_weight": float(cur_l_weight)
            }
            
            results.append(fr)
            metadata.append(meta)

        return results, metadata
