export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface BillingSummary {
  usage_date: string;
  cloud_provider: string;
  service: string;
  total_cost_usd: number;
  record_count: number;
  anomaly_count: number;
}

export interface SpendByDimension {
  dimension: string;
  total_cost_usd: number;
  pct_of_total: number;
  record_count: number;
}

export interface TrendPoint {
  period: string;
  total_cost_usd: number;
  record_count: number;
}

export interface AnomalyListItem {
  anomaly_id: string;
  detection_method: string;
  severity: string;
  z_score: number | null;
  expected_cost: number;
  actual_cost: number;
  deviation_pct: number;
  detected_at: string;
  cloud_provider: string;
  service: string;
  usage_date: string;
}

export interface AnomalySummary {
  total_anomalies: number;
  by_severity: Record<string, number>;
  by_cloud: Record<string, number>;
  by_type: Record<string, number>;
}

export interface ForecastItem {
  forecast_id: string;
  cloud_provider: string;
  service: string;
  horizon_days: number;
  forecast_date: string;
  predicted_cost: number;
  lower_bound: number;
  upper_bound: number;
  model_used: string;
}

export interface BudgetRisk {
  breach_risk: "none" | "possible" | "likely" | "certain";
  breach_date: string | null;
  days_to_breach: number | null;
  projected_monthly_cost: number;
  monthly_budget_usd: number;
  confidence_pct: number;
}

export interface TopDriver {
  driver: string;
  avg_shap_value: number;
  appearance_count: number;
}

export interface AttributionItem {
  attribution_date: string;
  cloud_provider: string;
  service_category: string;
  total_cost_usd: number;
  shap_values: Record<string, number>;
  top_driver_1: string;
  top_driver_1_value: number;
  top_driver_2: string | null;
  top_driver_2_value: number | null;
  top_driver_3: string | null;
  top_driver_3_value: number | null;
}

export interface AlertListItem {
  alert_id: string;
  alert_type: string;
  severity: string;
  cloud_provider: string;
  service_category: string | null;
  alert_date: string;
  title: string;
  message: string;
  is_resolved: boolean;
  created_at: string;
}

export interface AlertSummary {
  total: number;
  unresolved: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  by_cloud: Record<string, number>;
}
