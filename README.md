# Digital Commerce Performance Dashboard

A production-style Python + Power BI portfolio project demonstrating end-to-end ecommerce analytics: data engineering, business KPI calculation, and machine learning — built for a Digital Commerce context.

---

## Objective

Design and implement an analytics pipeline that ingests a continuously evolving B2B ecommerce dataset, calculates actionable business KPIs, trains interpretable ML models, and exports Power BI-ready files — all in a single reproducible command.

---

## Business Context

Modern digital commerce teams need more than static reports. They need:

- **Real-time KPI visibility** across revenue, orders, customers, and conversion.
- **Predictive signals** — which customers are about to churn, which products are gaining traction, what revenue looks like next month.
- **Self-service analytics** — dashboards that non-technical stakeholders can slice by segment, channel, or campaign without engineering support.

This project simulates that environment using synthetic B2B data across 14 months, five product categories, four customer segments, and four sales channels.

---

## Tools & Stack

| Layer | Technology |
|-------|------------|
| Data generation | Python · NumPy · pandas |
| Data cleaning | Python · pandas |
| Feature engineering | Python · pandas · NumPy |
| KPI calculation | Python · pandas |
| Machine learning | scikit-learn (RandomForest, GradientBoosting, LogisticRegression) |
| Data storage | CSV (Power BI) · Parquet (internal) |
| Visualization | Power BI Desktop |

---

## Project Structure

```
ecommerce-digital-commerce-dashboard/
│
├── data/
│   ├── raw/                    # Original generated dataset
│   ├── processed/              # Cleaned + feature-enriched Parquet files
│   │   └── models/             # Serialized ML models (.pkl)
│   └── powerbi/                # Final CSV exports for Power BI
│
├── notebooks/                  # Exploratory notebooks (optional)
│
├── src/
│   ├── config.py               # Central configuration (paths, constants)
│   ├── data_generator.py       # Synthetic B2B dataset generator
│   ├── data_cleaning.py        # Data quality & type casting
│   ├── feature_engineering.py  # RFM features, funnel metrics, lag features
│   ├── kpi_calculations.py     # Business KPI aggregations
│   ├── train_models.py         # ML model training (forecast + churn + demand)
│   ├── generate_predictions.py # Inference & prediction export
│   └── export_powerbi_tables.py# Final table validation & export
│
├── reports/
│   └── powerbi_page_plan.md    # Power BI data model + DAX + page layouts
│
├── main.py                     # Full pipeline runner
├── requirements.txt
└── README.md
```

---

## Main KPIs

| KPI | Description |
|-----|-------------|
| Total Revenue | Sum of completed order revenue |
| Total Orders | Count of completed orders |
| Average Order Value (AOV) | Revenue ÷ Orders |
| Units Sold | Total quantity of completed orders |
| Gross Margin % | Margin ÷ Revenue |
| Active Customers | Distinct customers with ≥1 completed order |
| New Customers | Customers who signed up in the selected period |
| Repeat Customer Rate | Customers with ≥2 orders ÷ active customers |
| Conversion Rate | Completed orders ÷ total visits |
| Cart Abandonment Rate | 1 − (completed ÷ cart additions) |
| WoW Revenue Growth | Week-over-week revenue % change |
| WoW Orders Growth | Week-over-week order count % change |

---

## Machine Learning Models

### A — Weekly Sales Forecast
- **Goal:** Predict next 4 weeks of revenue
- **Algorithm:** RandomForest or GradientBoosting (best selected by MAE)
- **Features:** Lag revenue, rolling mean, time index, seasonality signals
- **Metrics:** MAE, RMSE, MAPE
- **Output table:** `sales_forecast.csv`

### B — Customer Churn Risk
- **Goal:** Score each customer's probability of inactivity (no purchase in 60+ days)
- **Algorithm:** RandomForest or Logistic Regression (best selected by ROC-AUC)
- **Features:** Days since last purchase, purchase frequency, AOV, total revenue, segment
- **Metrics:** Accuracy, Precision, Recall, F1, ROC-AUC
- **Output table:** `customer_churn_risk.csv`

### C — Product Demand Prediction
- **Goal:** Forecast weekly units sold by product category
- **Algorithm:** RandomForest Regressor
- **Features:** Category encoding, week/month, time index, unit lags, rolling mean
- **Metrics:** MAE, RMSE
- **Output table:** `product_demand_predictions.csv`

All models are interpretable — RandomForest feature importances and Logistic Regression coefficients can be inspected directly.

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline

```bash
python main.py
```

This generates ~11,700 synthetic orders across 14 months, cleans them, engineers features, calculates KPIs, trains 3 ML models, and exports 12 CSV files to `data/powerbi/`.

### 3. Re-run without regenerating data

```bash
python main.py --skip-gen
```

Useful for re-running KPI and ML steps after parameter changes.

---

## How to Connect to Power BI

1. Open **Power BI Desktop**.
2. Click **Get Data → Text/CSV**.
3. Navigate to `data/powerbi/` and import all 12 CSV files.
4. In the **Model view**, create the relationships described in `reports/powerbi_page_plan.md`.
5. Create the DAX measures from the same file (copy-paste ready).
6. Build the 5 dashboard pages as described in the page plan.

> All date columns are already formatted as YYYY-MM-DD for seamless Power BI parsing.

See `reports/powerbi_page_plan.md` for the full setup guide including relationships, DAX measures, and page-by-page visual instructions.

---

## Dashboard Report

A completed export of the Power BI report is available as `ecommerce_dashboard.pdf` in the root of this repository. It includes all 5 dashboard pages and can be viewed without Power BI Desktop installed.

---

## How to Interpret the Dashboard

| Page | Audience | Key Question Answered |
|------|----------|-----------------------|
| Executive Overview | C-level, management | Are we growing? What is our baseline health? |
| Weekly KPI Tracking | Ops, trading team | Where did performance change this week? |
| Product & Category | Merchandising | Which products drive revenue and margin? |
| Customer & Segment | CRM, marketing | Who are our most valuable customers? |
| Predictive Insights | Commercial team | What will revenue look like next month? Who might churn? |

---

## Power BI Files Generated

| File | Rows (approx.) | Purpose |
|------|---------------|---------|
| `fact_orders.csv` | ~11,700 | Main transaction fact table |
| `dim_customers.csv` | ~490 | Customer master with RFM attributes |
| `dim_products.csv` | 80 | Product master |
| `dim_date.csv` | ~466 | Date dimension (day-level, with week/month/quarter) |
| `weekly_kpis.csv` | ~61 | Pre-aggregated weekly KPIs |
| `campaign_performance.csv` | 9 | Revenue by marketing campaign |
| `sales_channel_performance.csv` | 4 | Revenue by channel |
| `segment_performance.csv` | 4 | Revenue by customer segment |
| `sales_forecast.csv` | ~61 | Actual + predicted revenue + 4-week forecast (`is_future` flag) |
| `customer_churn_risk.csv` | ~482 | Churn probability per customer (Low / Medium / High) |
| `product_demand_predictions.csv` | ~285 | Category-level demand with trend labels |
| `model_performance.csv` | 8 | ML model metrics in long format (one row per model × metric) |

---

## Possible Future Improvements

- **Real data integration:** Replace the synthetic generator with a connector to Shopify, WooCommerce, or a BigQuery/Snowflake warehouse.
- **Automated refresh:** Schedule `main.py` with a cron job or Azure Data Factory to refresh Power BI files on a daily/weekly cadence.
- **Advanced forecasting:** Replace RandomForest with Prophet or LSTM for better seasonality capture.
- **A/B test analysis:** Add a module to evaluate campaign or pricing experiments using statistical significance tests.
- **Power BI Dataflow:** Publish the CSVs to a SharePoint/OneDrive folder and connect Power BI via a live dataflow for automatic refresh.
- **Customer LTV:** Add a Customer Lifetime Value model using a BG/NBD or Pareto/NBD approach.
- **Alerting:** Add a threshold-check step that flags KPI anomalies before exporting.

---

## Author

Built as a portfolio project.
Stack: Python · pandas · scikit-learn · Power BI
