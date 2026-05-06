"""
Full pipeline runner.

Usage:
    python main.py              # generate data + run full pipeline
    python main.py --skip-gen   # skip data generation (use existing raw data)
"""
import argparse
import time
from pathlib import Path


def banner(step: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {step}")
    print(f"{'='*60}")


def main(skip_gen: bool = False) -> None:
    t0 = time.time()

    # ── Step 1: Data generation ──────────────────────────────────────────────
    raw_path = Path("data/raw/orders_raw.csv")
    if not skip_gen or not raw_path.exists():
        banner("Step 1/6 — Generating synthetic dataset")
        from src.data_generator import run as gen_run
        gen_run()
    else:
        banner("Step 1/6 — Skipping data generation (raw file found)")

    # ── Step 2: Data cleaning ────────────────────────────────────────────────
    banner("Step 2/6 — Cleaning data")
    from src.data_cleaning import run as clean_run
    clean_run()

    # ── Step 3: Feature engineering ──────────────────────────────────────────
    banner("Step 3/6 — Engineering features")
    from src.feature_engineering import run as feat_run
    feat_run()

    # ── Step 4: KPI calculations ─────────────────────────────────────────────
    banner("Step 4/6 — Calculating KPIs")
    from src.kpi_calculations import run as kpi_run
    kpi_run()

    # ── Step 5: Train ML models ──────────────────────────────────────────────
    banner("Step 5/6 — Training ML models")
    from src.train_models import run as train_run
    train_run()

    # ── Step 6: Generate predictions + export ────────────────────────────────
    banner("Step 6/6 — Generating predictions & exporting Power BI tables")
    from src.generate_predictions import run as pred_run
    pred_run()
    from src.export_powerbi_tables import run as export_run
    export_run()

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  Pipeline complete in {elapsed:.1f}s")
    print(f"  Power BI files are ready in: data/powerbi/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ecommerce Dashboard Pipeline")
    parser.add_argument("--skip-gen", action="store_true",
                        help="Skip dataset generation if raw file already exists")
    args = parser.parse_args()
    main(skip_gen=args.skip_gen)
