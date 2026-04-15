# Multi-Cloud FinOps Synthetic Dataset Generator

A production-grade synthetic dataset generator for generating labeled billing data for AWS, Azure, and GCP. The generator simulates real-world seasonal patterns, controlled anomalies, and billing edge cases, making it perfect for training and evaluating FinOps intelligence and anomaly detection ML models.

## Usage

```bash
pip install -r requirements.txt
python generate.py --help
```

### Output

Data is generated relative to the script invoking it in the `output/` directory, broken down by cloud, retaining both raw labeled `csv`s and `parquet` records, and producing a unified ground-truth `anomaly_manifest.json` marking anomaly events.
