"""
Calculates all business KPIs and produces the dimension/fact tables
that Power BI will consume.
"""
import pandas as pd
import numpy as np
from src.config import DATA_PROCESSED, DATA_POWERBI


# ── Helpers ──────────────────────────────────────────────────────────────────

def _pct_change(series: pd.Series) -> pd.Series:
    return series.pct_change().replace([np.inf, -np.inf], np.nan).round(4)


def build_fact_orders(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "order_id", "order_date", "week_start", "year", "month",
        "week_number", "quarter", "customer_id", "customer_segment",
        "product_id", "product_category", "product_name",
        "quantity", "unit_price", "discount", "revenue", "margin",
        "city", "sales_channel", "campaign_name",
        "visits", "cart_additions", "completed_orders",
        "payment_method", "order_status", "is_completed",
        "conversion_rate", "cart_abandonment_rate",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def build_dim_customers(df: pd.DataFrame) -> pd.DataFrame:
    cust = (
        df.groupby("customer_id")
        .agg(
            customer_segment=  ("customer_segment",        "first"),
            city=              ("city",                    "first"),
            customer_signup_date=("customer_signup_date",  "first"),
            days_since_last_purchase=("days_since_last_purchase", "first"),
            purchase_frequency=("purchase_frequency",      "first"),
            total_revenue=     ("total_revenue",           "first"),
            avg_order_value=   ("avg_order_value",         "first"),
            is_repeat_customer=("is_repeat_customer",      "first"),
            is_churned=        ("is_churned",              "first"),
        )
        .reset_index()
    )
    return cust


def build_dim_products(df: pd.DataFrame) -> pd.DataFrame:
    prod = (
        df.groupby("product_id")
        .agg(
            product_name=    ("product_name",     "first"),
            product_category=("product_category", "first"),
            unit_price=      ("unit_price",        "mean"),
        )
        .reset_index()
    )
    prod["unit_price"] = prod["unit_price"].round(2)
    return prod


def build_weekly_kpis(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["is_completed"]]

    wk = (
        completed.groupby("week_start")
        .agg(
            total_revenue=   ("revenue",          "sum"),
            total_orders=    ("order_id",          "count"),
            total_units=     ("quantity",          "sum"),
            total_margin=    ("margin",            "sum"),
            avg_order_value= ("revenue",           "mean"),
            unique_customers=("customer_id",       "nunique"),
            avg_discount=    ("discount",          "mean"),
            visits=          ("visits",            "sum"),
            cart_additions=  ("cart_additions",    "sum"),
            completed_orders=("completed_orders",  "sum"),
        )
        .reset_index()
        .sort_values("week_start")
    )

    wk["gross_margin_pct"]      = (wk["total_margin"] / wk["total_revenue"]).round(4)
    wk["conversion_rate"]       = (wk["completed_orders"] /
                                    wk["visits"].replace(0, np.nan)).clip(0, 1).round(4)
    wk["cart_abandonment_rate"] = (1 - wk["completed_orders"] /
                                    wk["cart_additions"].replace(0, np.nan)).clip(0, 1).round(4)

    # Week-over-week growth
    wk["revenue_wow_growth"] = _pct_change(wk["total_revenue"])
    wk["orders_wow_growth"]  = _pct_change(wk["total_orders"])

    # New customers: signed up in this week
    new_cust = (
        df.groupby(df["customer_signup_date"].dt.to_period("W")
                     .apply(lambda p: p.start_time))
        ["customer_id"]
        .nunique()
        .reset_index()
    )
    new_cust.columns = ["week_start", "new_customers"]
    new_cust["week_start"] = pd.to_datetime(new_cust["week_start"])
    wk = wk.merge(new_cust, on="week_start", how="left")
    wk["new_customers"] = wk["new_customers"].fillna(0).astype(int)

    # Repeat customers in the week
    repeat = (
        completed[completed["is_repeat_customer"]]
        .groupby("week_start")["customer_id"]
        .nunique()
        .reset_index()
        .rename(columns={"customer_id": "repeat_customers"})
    )
    wk = wk.merge(repeat, on="week_start", how="left")
    wk["repeat_customers"] = wk["repeat_customers"].fillna(0).astype(int)

    wk["avg_order_value"] = wk["avg_order_value"].round(2)
    wk["total_revenue"]   = wk["total_revenue"].round(2)
    wk["total_margin"]    = wk["total_margin"].round(2)

    return wk


def build_campaign_performance(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["is_completed"]]
    camp = (
        completed.groupby("campaign_name")
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
    camp["gross_margin_pct"] = (camp["total_margin"] / camp["total_revenue"]).round(4)
    camp["avg_order_value"]  = camp["avg_order_value"].round(2)
    camp["revenue_share"]    = (camp["total_revenue"] /
                                 camp["total_revenue"].sum()).round(4)
    return camp.sort_values("total_revenue", ascending=False)


def run() -> dict:
    DATA_POWERBI.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(DATA_PROCESSED / "orders_features.parquet")

    tables = {
        "fact_orders":          build_fact_orders(df),
        "dim_customers":        build_dim_customers(df),
        "dim_products":         build_dim_products(df),
        "weekly_kpis":          build_weekly_kpis(df),
        "campaign_performance": build_campaign_performance(df),
    }

    for name, tbl in tables.items():
        tbl.to_csv(DATA_POWERBI / f"{name}.csv", index=False)
        print(f"  Saved: data/powerbi/{name}.csv  ({len(tbl):,} rows)")

    return tables


if __name__ == "__main__":
    run()
