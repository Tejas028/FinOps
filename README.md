# Cloud FinOps Intelligence Platform

A comprehensive mono-repo orchestrating AI-Powered Multi-Cloud Cost Anomaly Detection, Spend Forecasting, and Alerting across AWS, Azure, and GCP. The platform uses memory-chunked generation, TimescaleDB temporal indexing, isolated ML workers handling Time-Series Analysis models, and a modern React Vite frontend dashboard for visualizing insights at a massive scale.

## Module Map

| Module | Purpose | Status |
| :--- | :--- | :--- |
| **0. `synthetic_data/`** | Generates highly realistic labeled billing logs | ✅ Complete |
| **1. `shared/`** | Canonical schemas and utility contracts | ✅ Complete |
| **2. `ingestion/`** | Normalizes external Cloud Parquet into database format | 🚧 Scaffolded |
| **3. `normalization/`** | Enforces structured conversions utilizing mapping logics | 🚧 Scaffolded |
| **4. `storage/`** | Postgres + Timescale instance wiring and SQL connections| 🚧 Scaffolded |
| **5. `feature_engineering/`** | Dimensional grouping for anomaly triggers | 🚧 Scaffolded |
| **6. `detection/`** | IsolationForest & LSTM engine execution | 🚧 Scaffolded |
| **7. `forecasting/`** | Prophet and LightGBM model executions | 🚧 Scaffolded |
| **8. `attribution/`** | SHAP explanations mapped to identified cost aberrations | 🚧 Scaffolded |
| **9. `api/`** | FastAPI endpoints and routers interfacing the engines | 🚧 Scaffolded |
| **10. `frontend/`** | React+Vite Web Dashboard | 🚧 Scaffolded |
| **11. `alerting/`** | Event notification framework | 🚧 Scaffolded |
| **12. `tests/`** | Global pytest integration suites | 🚧 Scaffolded |

## Quick Start
```bash
cp .env.example .env
make dev
```

> [!WARNING]
> The target data dump rests relatively rooted at `synthetic_data/output/`. Never manually override or rename schema schemas outside of **`shared/schemas/`**. Any deviations strictly outside the core domain will break normalization ingestion.

**Please Note**: NEVER redefine `BillingRecord`, `AnomalyResult`, or `ForecastResult` outside the dedicated definitions.
