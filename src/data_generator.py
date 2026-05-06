"""
Generates a realistic synthetic B2B ecommerce dataset and saves it to data/raw/.
"""
import numpy as np
import pandas as pd
from pathlib import Path

from src.config import (
    RANDOM_SEED, N_CUSTOMERS, N_PRODUCTS, START_DATE, MONTHS_OF_DATA,
    CUSTOMER_SEGMENTS, SALES_CHANNELS, PAYMENT_METHODS, ORDER_STATUSES,
    PRODUCT_CATEGORIES, CAMPAIGNS, DATA_RAW,
)

rng = np.random.default_rng(RANDOM_SEED)


def _build_customers() -> pd.DataFrame:
    """Master customer dimension with signup dates spread over the period."""
    start = pd.Timestamp(START_DATE)
    signup_offsets = rng.integers(0, MONTHS_OF_DATA * 30, size=N_CUSTOMERS)
    signup_dates = [start + pd.Timedelta(days=int(d)) for d in signup_offsets]

    segments = rng.choice(CUSTOMER_SEGMENTS, size=N_CUSTOMERS,
                          p=[0.20, 0.45, 0.25, 0.10])
    cities = rng.choice(
        ["London", "Manchester", "Birmingham", "Leeds", "Glasgow",
         "Liverpool", "Bristol", "Edinburgh", "Cardiff", "Dublin"],
        size=N_CUSTOMERS,
    )
    return pd.DataFrame({
        "customer_id":      [f"C{str(i).zfill(4)}" for i in range(1, N_CUSTOMERS + 1)],
        "customer_segment": segments,
        "city":             cities,
        "customer_signup_date": signup_dates,
    })


def _build_products() -> pd.DataFrame:
    """Master product dimension."""
    records = []
    pid = 1
    for category, names in PRODUCT_CATEGORIES.items():
        for name in names:
            # price varies by category
            base = {"Electronics": 400, "Software": 900,
                    "Cloud Services": 600, "Networking": 300,
                    "Office Supply": 120}[category]
            price = round(float(rng.uniform(base * 0.6, base * 1.6)), 2)
            margin_pct = round(float(rng.uniform(0.18, 0.52)), 3)
            records.append({
                "product_id":       f"P{str(pid).zfill(3)}",
                "product_name":     name,
                "product_category": category,
                "unit_price":       price,
                "margin_pct":       margin_pct,
            })
            pid += 1
    # pad to N_PRODUCTS with variants
    while len(records) < N_PRODUCTS:
        base_rec = records[rng.integers(0, len(records))]
        new_rec = base_rec.copy()
        new_rec["product_id"] = f"P{str(pid).zfill(3)}"
        new_rec["product_name"] = base_rec["product_name"] + " Pro"
        new_rec["unit_price"] = round(base_rec["unit_price"] * rng.uniform(1.1, 1.5), 2)
        records.append(new_rec)
        pid += 1
    return pd.DataFrame(records[:N_PRODUCTS])


def _seasonal_multiplier(date: pd.Timestamp) -> float:
    """Simple seasonal curve: peak in Q4 and mid-year."""
    m = date.month
    curve = {1: 0.75, 2: 0.78, 3: 0.90, 4: 0.95, 5: 1.00, 6: 1.05,
             7: 0.88, 8: 0.85, 9: 1.00, 10: 1.10, 11: 1.35, 12: 1.25}
    return curve.get(m, 1.0)


def generate_orders(customers: pd.DataFrame,
                    products: pd.DataFrame) -> pd.DataFrame:
    """
    Generate order-level transactions.
    Volume increases over time to simulate business growth (~2 % per month).
    """
    start = pd.Timestamp(START_DATE)
    end   = start + pd.DateOffset(months=MONTHS_OF_DATA)
    date_range = pd.date_range(start, end, freq="D")

    products_arr = products.to_dict("records")

    orders = []
    order_id = 1

    for date in date_range:
        # Pre-filter eligible customers (signed up on or before this date)
        eligible = customers[
            pd.to_datetime(customers["customer_signup_date"]) <= date
        ]
        if eligible.empty:
            continue

        season = _seasonal_multiplier(date)
        growth = 1 + 0.02 * ((date - start).days / 30)
        n_orders = max(2, int(rng.poisson(lam=25 * season * growth)))

        # Sample with replacement from eligible customers
        cust_indices = rng.integers(0, len(eligible), size=n_orders)

        for idx in cust_indices:
            cust = eligible.iloc[idx]
            prod_idx = rng.integers(0, len(products_arr))
            prod = products_arr[prod_idx]
            qty = int(rng.choice([1, 2, 3, 4, 5, 10], p=[0.35, 0.25, 0.18, 0.10, 0.08, 0.04]))
            discount = float(rng.choice([0, 0.05, 0.10, 0.15, 0.20],
                                        p=[0.50, 0.20, 0.15, 0.10, 0.05]))
            unit_price = prod["unit_price"]
            revenue = round(unit_price * qty * (1 - discount), 2)
            margin  = round(revenue * prod["margin_pct"], 2)

            # funnel metrics: visits > cart_additions > completed_orders
            visits = int(rng.integers(5, 80))
            cart_adds = max(1, int(visits * rng.uniform(0.10, 0.45)))
            completed = 1 if rng.random() < 0.65 else 0

            status = rng.choice(ORDER_STATUSES, p=[0.82, 0.08, 0.06, 0.04])

            orders.append({
                "order_id":          f"ORD{str(order_id).zfill(6)}",
                "customer_id":       cust["customer_id"],
                "customer_segment":  cust["customer_segment"],
                "order_date":        date,
                "week":              date.to_period("W").start_time.date(),
                "product_id":        prod["product_id"],
                "product_category":  prod["product_category"],
                "product_name":      prod["product_name"],
                "quantity":          qty,
                "unit_price":        unit_price,
                "discount":          discount,
                "revenue":           revenue,
                "margin":            margin,
                "city":              cust["city"],
                "sales_channel":     rng.choice(SALES_CHANNELS, p=[0.30, 0.28, 0.22, 0.20]),
                "campaign_name":     rng.choice(CAMPAIGNS),
                "visits":            visits,
                "cart_additions":    cart_adds,
                "completed_orders":  completed,
                "customer_signup_date": cust["customer_signup_date"],
                "last_purchase_date":   date,
                "payment_method":    rng.choice(PAYMENT_METHODS, p=[0.40, 0.30, 0.20, 0.10]),
                "order_status":      status,
            })
            order_id += 1

    return pd.DataFrame(orders)


def run() -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    customers = _build_customers()
    products  = _build_products()
    orders    = generate_orders(customers, products)

    customers.to_csv(DATA_RAW / "customers_master.csv", index=False)
    products.to_csv(DATA_RAW / "products_master.csv",   index=False)
    orders.to_csv(DATA_RAW / "orders_raw.csv",          index=False)

    print(f"  Generated {len(orders):,} orders across "
          f"{orders['order_date'].nunique()} days.")


if __name__ == "__main__":
    run()
