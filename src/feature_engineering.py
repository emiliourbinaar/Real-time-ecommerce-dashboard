"""
Adds customer-level and product-level features used by both KPIs and ML models.
"""
import pandas as pd
import numpy as np
from src.config import DATA_PROCESSED, CHURN_INACTIVE_DAYS


def add_customer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Append RFM-style features per customer, joined back to the order level."""
    snapshot_date = df["order_date"].max()

    completed = df[df["is_completed"]]

    rfm = (
        completed.groupby("customer_id")
        .agg(
            last_purchase_date=("order_date", "max"),
            purchase_frequency=("order_id",   "count"),
            total_revenue=     ("revenue",     "sum"),
            avg_order_value=   ("revenue",     "mean"),
            total_units=       ("quantity",    "sum"),
        )
        .reset_index()
    )
    rfm["days_since_last_purchase"] = (
        snapshot_date - rfm["last_purchase_date"]
    ).dt.days
    rfm["is_repeat_customer"] = rfm["purchase_frequency"] >= 2
    rfm["is_churned"] = rfm["days_since_last_purchase"] >= CHURN_INACTIVE_DAYS

    df = df.merge(rfm[["customer_id", "days_since_last_purchase",
                        "purchase_frequency", "total_revenue",
                        "avg_order_value", "is_repeat_customer",
                        "is_churned"]],
                  on="customer_id", how="left")
    return df


def add_product_features(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling 4-week revenue and unit trend per product."""
    weekly = (
        df[df["is_completed"]]
        .groupby(["product_id", "week_start"])
        .agg(weekly_units=("quantity", "sum"),
             weekly_revenue=("revenue", "sum"))
        .reset_index()
        .sort_values(["product_id", "week_start"])
    )
    weekly["rolling_4w_units"] = (
        weekly.groupby("product_id")["weekly_units"]
        .transform(lambda x: x.rolling(4, min_periods=1).mean())
    )
    df = df.merge(weekly[["product_id", "week_start",
                           "weekly_units", "rolling_4w_units"]],
                  on=["product_id", "week_start"], how="left")
    return df


def add_funnel_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derived conversion and abandonment metrics at order level."""
    df["conversion_rate"]      = df["completed_orders"] / df["visits"].replace(0, np.nan)
    df["cart_abandonment_rate"]= 1 - (df["completed_orders"] /
                                       df["cart_additions"].replace(0, np.nan))
    df["conversion_rate"]       = df["conversion_rate"].clip(0, 1)
    df["cart_abandonment_rate"] = df["cart_abandonment_rate"].clip(0, 1)
    return df


def run() -> pd.DataFrame:
    path = DATA_PROCESSED / "orders_clean.parquet"
    df = pd.read_parquet(path)

    df = add_customer_features(df)
    df = add_product_features(df)
    df = add_funnel_features(df)

    df.to_parquet(DATA_PROCESSED / "orders_features.parquet", index=False)
    print("  Saved: data/processed/orders_features.parquet")
    return df


if __name__ == "__main__":
    run()
