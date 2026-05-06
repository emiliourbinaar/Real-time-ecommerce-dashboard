"""
Final export step: ensures all Power BI CSVs are complete and consistent.
Adds a sales_channel_performance table not covered elsewhere.
"""
import pandas as pd
from src.config import DATA_PROCESSED, DATA_POWERBI


def build_sales_channel_performance(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["is_completed"]]
    ch = (
        completed.groupby("sales_channel")
        .agg(
            total_revenue=   ("revenue",     "sum"),
            total_orders=    ("order_id",    "count"),
            unique_customers=("customer_id", "nunique"),
            avg_order_value= ("revenue",     "mean"),
            total_margin=    ("margin",      "sum"),
            avg_discount=    ("discount",    "mean"),
        )
        .reset_index()
    )
    ch["gross_margin_pct"] = (ch["total_margin"] / ch["total_revenue"]).round(4)
    ch["revenue_share"]    = (ch["total_revenue"] /
                               ch["total_revenue"].sum()).round(4)
    ch["avg_order_value"]  = ch["avg_order_value"].round(2)
    return ch.sort_values("total_revenue", ascending=False)


def build_segment_performance(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["is_completed"]]
    seg = (
        completed.groupby("customer_segment")
        .agg(
            total_revenue=   ("revenue",     "sum"),
            total_orders=    ("order_id",    "count"),
            unique_customers=("customer_id", "nunique"),
            avg_order_value= ("revenue",     "mean"),
            total_margin=    ("margin",      "sum"),
            repeat_customers=("is_repeat_customer", "sum"),
        )
        .reset_index()
    )
    seg["gross_margin_pct"]   = (seg["total_margin"] / seg["total_revenue"]).round(4)
    seg["repeat_rate"]        = (seg["repeat_customers"] /
                                  seg["unique_customers"]).round(4)
    seg["avg_order_value"]    = seg["avg_order_value"].round(2)
    return seg.sort_values("total_revenue", ascending=False)


def run() -> None:
    DATA_POWERBI.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(DATA_PROCESSED / "orders_features.parquet")

    extras = {
        "sales_channel_performance": build_sales_channel_performance(df),
        "segment_performance":       build_segment_performance(df),
    }
    for name, tbl in extras.items():
        tbl.to_csv(DATA_POWERBI / f"{name}.csv", index=False)
        print(f"  Saved: data/powerbi/{name}.csv  ({len(tbl):,} rows)")

    # Verify all expected files exist
    expected = [
        "fact_orders", "dim_customers", "dim_products", "weekly_kpis",
        "campaign_performance", "sales_channel_performance", "segment_performance",
        "sales_forecast", "customer_churn_risk", "product_demand_predictions",
        "model_performance",
    ]
    print("\n  Power BI export manifest:")
    for name in expected:
        path = DATA_POWERBI / f"{name}.csv"
        status = f"{path.stat().st_size / 1024:.1f} KB" if path.exists() else "MISSING"
        print(f"    {'OK' if path.exists() else 'XX'}  {name}.csv  ({status})")


if __name__ == "__main__":
    run()
