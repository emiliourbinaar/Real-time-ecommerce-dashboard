# Power BI Data Model & Dashboard Plan
### Digital Commerce Performance Dashboard

---

## 1. Tables to Load into Power BI

| File | Type | Description |
|------|------|-------------|
| `fact_orders.csv` | Fact | One row per order transaction |
| `dim_customers.csv` | Dimension | One row per customer with RFM features |
| `dim_products.csv` | Dimension | One row per product |
| `weekly_kpis.csv` | Aggregate | Pre-calculated weekly KPIs |
| `campaign_performance.csv` | Aggregate | Revenue & orders by campaign |
| `sales_channel_performance.csv` | Aggregate | Revenue & orders by sales channel |
| `segment_performance.csv` | Aggregate | Revenue & orders by customer segment |
| `sales_forecast.csv` | ML Output | Actual vs predicted weekly revenue |
| `customer_churn_risk.csv` | ML Output | Churn probability per customer |
| `product_demand_predictions.csv` | ML Output | Demand trend by category |
| `model_performance.csv` | ML Metadata | Model metrics summary |

---

## 2. Recommended Relationships

```
fact_orders[customer_id]   → dim_customers[customer_id]   (Many-to-One)
fact_orders[product_id]    → dim_products[product_id]     (Many-to-One)
fact_orders[week_start]    → weekly_kpis[week_start]      (Many-to-One)
customer_churn_risk[customer_id] → dim_customers[customer_id] (One-to-One)
```

> **Note:** `weekly_kpis`, `campaign_performance`, `sales_channel_performance`,
> `segment_performance`, `sales_forecast`, and `product_demand_predictions`
> are standalone aggregate tables — connect them via shared key columns only
> where needed. Avoid circular dependencies.

---

## 3. Primary Keys & Foreign Keys

| Table | Primary Key | Foreign Key(s) |
|-------|-------------|----------------|
| `fact_orders` | `order_id` | `customer_id`, `product_id` |
| `dim_customers` | `customer_id` | — |
| `dim_products` | `product_id` | — |
| `weekly_kpis` | `week_start` | — |
| `campaign_performance` | `campaign_name` | — |
| `sales_channel_performance` | `sales_channel` | — |
| `segment_performance` | `customer_segment` | — |
| `sales_forecast` | `week_start` | — |
| `customer_churn_risk` | `customer_id` | `customer_id → dim_customers` |
| `product_demand_predictions` | (`product_category`, `week`) | — |
| `model_performance` | `model` | — |

---

## 4. DAX Measures (copy-paste ready)

### Core KPIs

```dax
Total Revenue =
CALCULATE(SUM(fact_orders[revenue]), fact_orders[is_completed] = TRUE())

Total Orders =
CALCULATE(COUNTROWS(fact_orders), fact_orders[is_completed] = TRUE())

Average Order Value =
DIVIDE([Total Revenue], [Total Orders], 0)

Gross Margin =
CALCULATE(SUM(fact_orders[margin]), fact_orders[is_completed] = TRUE())

Gross Margin % =
DIVIDE([Gross Margin], [Total Revenue], 0)

Units Sold =
CALCULATE(SUM(fact_orders[quantity]), fact_orders[is_completed] = TRUE())
```

### Customer Metrics

```dax
Active Customers =
CALCULATE(DISTINCTCOUNT(fact_orders[customer_id]),
          fact_orders[is_completed] = TRUE())

New Customers =
SUM(weekly_kpis[new_customers])

Repeat Customers =
CALCULATE(
    DISTINCTCOUNT(fact_orders[customer_id]),
    fact_orders[is_completed] = TRUE(),
    RELATED(dim_customers[is_repeat_customer]) = TRUE()
)

Repeat Customer Rate =
DIVIDE([Repeat Customers], [Active Customers], 0)
```

### Funnel Metrics

```dax
Conversion Rate =
DIVIDE(
    CALCULATE(SUM(fact_orders[completed_orders])),
    CALCULATE(SUM(fact_orders[visits])),
    0
)

Cart Abandonment Rate =
1 - DIVIDE(
    CALCULATE(SUM(fact_orders[completed_orders])),
    CALCULATE(SUM(fact_orders[cart_additions])),
    0
)
```

### Week-over-Week Growth

```dax
WoW Revenue Growth =
VAR CurrentWeek = MAX(weekly_kpis[week_start])
VAR PrevWeek    = CurrentWeek - 7
VAR ThisRev = CALCULATE(SUM(weekly_kpis[total_revenue]),
                        weekly_kpis[week_start] = CurrentWeek)
VAR PrevRev = CALCULATE(SUM(weekly_kpis[total_revenue]),
                        weekly_kpis[week_start] = PrevWeek)
RETURN DIVIDE(ThisRev - PrevRev, PrevRev, 0)

WoW Orders Growth =
VAR CurrentWeek = MAX(weekly_kpis[week_start])
VAR PrevWeek    = CurrentWeek - 7
VAR ThisOrd = CALCULATE(SUM(weekly_kpis[total_orders]),
                        weekly_kpis[week_start] = CurrentWeek)
VAR PrevOrd = CALCULATE(SUM(weekly_kpis[total_orders]),
                        weekly_kpis[week_start] = PrevWeek)
RETURN DIVIDE(ThisOrd - PrevOrd, PrevOrd, 0)
```

### Predictive Measures

```dax
Predicted Revenue =
CALCULATE(SUM(sales_forecast[predicted_revenue]),
          NOT(ISBLANK(sales_forecast[predicted_revenue])))

Forecast Error =
DIVIDE(
    ABS(SUM(sales_forecast[prediction_error])),
    SUM(sales_forecast[actual_revenue]),
    0
)

High Risk Customers =
CALCULATE(COUNTROWS(customer_churn_risk),
          customer_churn_risk[risk_level] = "High")

Churn Risk Rate =
DIVIDE([High Risk Customers], COUNTROWS(customer_churn_risk), 0)
```

---

## 5. Dashboard Pages

---

### Page 1 — Executive Overview

**Purpose:** Single-screen business summary for leadership.

**Visuals:**
- 6× KPI Cards: Total Revenue, Total Orders, AOV, Gross Margin %, Active Customers, Conversion Rate
- Line chart: Weekly Revenue trend (last 12 weeks)
- Clustered bar: Revenue by Customer Segment
- Donut: Revenue by Sales Channel
- KPI Card: WoW Revenue Growth, WoW Orders Growth
- Slicer: Date range, Customer Segment

**Key fields:**
- `weekly_kpis[total_revenue]`, `[total_orders]`, `[avg_order_value]`, `[gross_margin_pct]`, `[unique_customers]`, `[conversion_rate]`

---

### Page 2 — Weekly KPI Tracking

**Purpose:** Operational view of week-by-week performance.

**Visuals:**
- Line + Column combo: Weekly Revenue (bars) + WoW Growth (line)
- Line chart: Weekly Orders trend
- Area chart: New vs Repeat Customers per week
- Table: Weekly KPI summary (all `weekly_kpis` columns)
- Slicer: Year, Quarter

**Key fields:**
- `weekly_kpis` (all columns), `[revenue_wow_growth]`, `[orders_wow_growth]`

---

### Page 3 — Product & Category Performance

**Purpose:** Identify top-performing products and demand patterns.

**Visuals:**
- Bar chart (horizontal): Top 10 Products by Revenue
- Treemap: Revenue by Product Category
- Scatter plot: Units Sold vs Gross Margin % by Category
- Table: Category breakdown (revenue, units, margin, trend)
- Bar chart: Product Demand Trend (Increasing / Stable / Decreasing count)
- Slicer: Product Category

**Key fields:**
- `fact_orders[product_name]`, `[product_category]`, `[revenue]`, `[margin]`, `[quantity]`
- `product_demand_predictions[demand_trend]`

---

### Page 4 — Customer & Segment Analysis

**Purpose:** Understand the customer base, loyalty, and value distribution.

**Visuals:**
- Stacked bar: Revenue by Customer Segment
- KPI Cards: Active Customers, New Customers, Repeat Rate
- Scatter plot: Purchase Frequency vs AOV (coloured by Segment)
- Bar chart: Top 10 Customers by Revenue
- Histogram / Distribution: Days Since Last Purchase
- Table: Segment performance summary

**Key fields:**
- `dim_customers`, `segment_performance`, `fact_orders[customer_segment]`

---

### Page 5 — Predictive Insights

**Purpose:** Forward-looking view powered by ML models.

**Visuals:**
- Line chart: Actual Revenue vs Predicted Revenue (with future forecast dashed)
- Table: Customer Churn Risk — top 20 high-risk customers
- Bar chart: Customers by Risk Level (Low / Medium / High)
- Bar chart: Product categories with Increasing / Decreasing demand
- KPI Card: High Risk Customers count, Churn Risk Rate
- Slicer: Risk Level, Product Category

**Key fields:**
- `sales_forecast[actual_revenue]`, `[predicted_revenue]`
- `customer_churn_risk[churn_risk_probability]`, `[risk_level]`
- `product_demand_predictions[demand_trend]`, `[predicted_units_sold]`

---

### Page 6 — Model Performance

**Purpose:** Transparent view of ML model quality for technical stakeholders.

**Visuals:**
- Table: `model_performance` — algorithm, target, MAE, RMSE, MAPE, F1, AUC
- KPI Cards: Best Forecast MAPE %, Churn Model F1, Churn Model AUC
- Bar chart: Forecast Error by week (actual vs predicted comparison)
- Text card: Plain-language model explanation (add manually in Power BI)

**Key fields:**
- `model_performance` (all columns)
- `sales_forecast[prediction_error]`

---

## 6. Recommended Color Theme

| Metric | Color |
|--------|-------|
| Revenue / Positive | `#1E8449` (dark green) |
| Orders | `#2980B9` (blue) |
| Margin | `#8E44AD` (purple) |
| Churn / Risk High | `#C0392B` (red) |
| Risk Medium | `#E67E22` (orange) |
| Risk Low | `#27AE60` (green) |
| Forecast | `#F39C12` (amber, dashed line) |
| Neutral/Background | `#F2F3F4` |

---

## 7. Suggested Filter Panel (Global Slicers)

Add these slicers to every page via the **Sync Slicers** panel:
- `fact_orders[order_date]` — date range picker
- `fact_orders[customer_segment]` — multi-select
- `fact_orders[sales_channel]` — multi-select
- `fact_orders[product_category]` — multi-select
