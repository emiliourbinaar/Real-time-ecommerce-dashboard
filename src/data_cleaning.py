"""
Loads raw orders and applies data quality rules:
- type casting
- duplicate removal
- null handling
- business-rule validation (e.g. revenue > 0)
- date enrichment (year, month, week_number)
"""
import pandas as pd
from src.config import DATA_RAW, DATA_PROCESSED


def load_raw() -> pd.DataFrame:
    path = DATA_RAW / "orders_raw.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {path}. Run data_generator first."
        )
    df = pd.read_csv(path, parse_dates=["order_date", "customer_signup_date",
                                         "last_purchase_date"])
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    original_len = len(df)

    # ── Drop exact duplicates ────────────────────────────────────────────────
    df = df.drop_duplicates(subset=["order_id"])

    # ── Type safety ─────────────────────────────────────────────────────────
    df["quantity"]   = pd.to_numeric(df["quantity"],   errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["discount"]   = pd.to_numeric(df["discount"],   errors="coerce").fillna(0)
    df["revenue"]    = pd.to_numeric(df["revenue"],    errors="coerce")
    df["margin"]     = pd.to_numeric(df["margin"],     errors="coerce")

    # ── Business-rule validation ─────────────────────────────────────────────
    df = df[df["revenue"] > 0]
    df = df[df["quantity"] > 0]
    df = df[df["unit_price"] > 0]
    df = df[df["discount"].between(0, 1)]

    # ── Drop rows missing critical keys ──────────────────────────────────────
    df = df.dropna(subset=["order_id", "customer_id", "product_id", "order_date"])

    # ── Date features ────────────────────────────────────────────────────────
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["year"]       = df["order_date"].dt.year
    df["month"]      = df["order_date"].dt.month
    df["week_number"]= df["order_date"].dt.isocalendar().week.astype(int)
    df["quarter"]    = df["order_date"].dt.quarter
    df["week_start"] = df["order_date"].dt.to_period("W").apply(
                           lambda p: p.start_time)

    # ── Cancelled / refunded orders: keep but flag ───────────────────────────
    df["is_completed"] = df["order_status"] == "Completed"

    cleaned_len = len(df)
    print(f"  Cleaning: {original_len:,} -> {cleaned_len:,} rows "
          f"({original_len - cleaned_len:,} removed).")
    return df.reset_index(drop=True)


def run() -> pd.DataFrame:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df = load_raw()
    df = clean(df)
    df.to_parquet(DATA_PROCESSED / "orders_clean.parquet", index=False)
    print("  Saved: data/processed/orders_clean.parquet")
    return df


if __name__ == "__main__":
    run()
