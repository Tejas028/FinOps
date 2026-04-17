import uuid
from typing import List, Tuple, Dict
from datetime import datetime, date

from forecasting import config
from forecasting.models.base_model import ForecastOutput
from shared.schemas.forecast import ForecastResult

class EnsembleForecaster:
    def to_date(self, val):
        if val is None: return None
        if hasattr(val, "date") and callable(val.date):
            return val.date()
        return val

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

        # Map predictions by (forecast_date) - UNIFIED TO date objects
        prophet_map: Dict[date, ForecastOutput] = {
            self.to_date(po.forecast_date): po for po in prophet_outputs
        }
        lgbm_map: Dict[date, ForecastOutput] = {
            self.to_date(lo.forecast_date): lo for lo in lgbm_outputs
        }

        results: List[ForecastResult] = []
        metadata: List[dict] = []
        now = datetime.now()
        
        # Determine the "origin" date to calculate target dates
        origin_date = None
        if lgbm_outputs:
            lo = lgbm_outputs[0]
            from datetime import timedelta
            origin_date = self.to_date(lo.forecast_date) - timedelta(days=lo.horizon_days)
        elif prophet_outputs:
            p_dates = sorted([self.to_date(po.forecast_date) for po in prophet_outputs])
            from datetime import timedelta
            origin_date = p_dates[0] - timedelta(days=1)
            
        if not origin_date:
            return [], []

        # Sorting to ensure chronological order
        all_dates = sorted(list(set(prophet_map.keys()).union(set(lgbm_map.keys()))))

        for d_date in all_dates:
            po = prophet_map.get(d_date)
            lo = lgbm_map.get(d_date)

            if not po and not lo:
                continue

            # Calculate horizon offset
            h_days = (d_date - origin_date).days
            if h_days <= 0:
                continue

            cur_p_weight = p_weight
            cur_l_weight = l_weight

            p_pred = po.predicted_cost if po else 0.0
            l_pred = lo.predicted_cost if lo else 0.0

            if po and lo:
                # Milestone date: Blend
                pred = (p_pred * cur_p_weight) + (l_pred * cur_l_weight)
                lb = min(po.lower_bound, lo.lower_bound)
                ub = max(po.upper_bound, lo.upper_bound)
            elif po:
                # Continuous daily line from Prophet
                pred = p_pred
                lb = po.lower_bound
                ub = po.upper_bound
                cur_p_weight = 1.0
                cur_l_weight = 0.0
            else:
                # LGBM only
                pred = l_pred
                lb = lo.lower_bound
                ub = lo.upper_bound
                cur_p_weight = 0.0
                cur_l_weight = 1.0

            base = po if po else lo

            try:
                fr = ForecastResult(
                    forecast_id=str(uuid.uuid4()),
                    cloud_provider=base.cloud_provider,
                    service=base.service,
                    region=None,
                    horizon_days=h_days,
                    forecast_date=base.forecast_date,
                    predicted_cost=max(0.0, pred),
                    lower_bound=max(0.0, lb),
                    upper_bound=max(0.0, ub),
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
            except Exception:
                pass

        return results, metadata
