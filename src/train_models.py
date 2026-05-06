"""
Trains three ML models:
  A) Weekly Sales Forecast (regression)
  B) Customer Churn Risk   (classification)
  C) Product Demand        (regression per category)

All fitted models are persisted so generate_predictions.py can load them.
"""
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                              accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from src.config import DATA_PROCESSED, TEST_WEEKS, RANDOM_SEED

warnings.filterwarnings("ignore")

MODELS_DIR = DATA_PROCESSED / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ── A: Weekly Sales Forecast ─────────────────────────────────────────────────

def _prepare_weekly_features(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["is_completed"]]
    wk = (
        completed.groupby("week_start")
        .agg(revenue=   ("revenue",   "sum"),
             orders=    ("order_id",  "count"),
             units=     ("quantity",  "sum"),
             avg_disc=  ("discount",  "mean"),
             n_customers=("customer_id", "nunique"))
        .reset_index()
        .sort_values("week_start")
    )
    wk["week_start"] = pd.to_datetime(wk["week_start"])
    wk["week_num"]   = wk["week_start"].dt.isocalendar().week.astype(int)
    wk["month"]      = wk["week_start"].dt.month
    wk["quarter"]    = wk["week_start"].dt.quarter
    wk["t"]          = range(len(wk))       # linear time index for trend

    # Lag features
    for lag in [1, 2, 4]:
        wk[f"revenue_lag{lag}"] = wk["revenue"].shift(lag)
        wk[f"orders_lag{lag}"]  = wk["orders"].shift(lag)

    # Rolling mean
    wk["revenue_roll4"] = wk["revenue"].shift(1).rolling(4).mean()
    return wk.dropna()


def train_sales_forecast(df: pd.DataFrame) -> dict:
    wk = _prepare_weekly_features(df)

    feature_cols = ["week_num", "month", "quarter", "t",
                    "revenue_lag1", "revenue_lag2", "revenue_lag4",
                    "orders_lag1", "orders_lag2", "orders_lag4",
                    "revenue_roll4", "avg_disc", "n_customers"]
    X = wk[feature_cols]
    y = wk["revenue"]

    # Temporal split — last TEST_WEEKS rows as test
    X_train, X_test = X.iloc[:-TEST_WEEKS], X.iloc[-TEST_WEEKS:]
    y_train, y_test = y.iloc[:-TEST_WEEKS], y.iloc[-TEST_WEEKS:]

    models = {
        "RandomForest": RandomForestRegressor(n_estimators=200, random_state=RANDOM_SEED,
                                              max_depth=8, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=200,
                                                      learning_rate=0.05,
                                                      max_depth=4,
                                                      random_state=RANDOM_SEED),
    }

    results = {}
    best_model, best_mae = None, np.inf

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae  = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mape = np.mean(np.abs((y_test.values - preds) / y_test.values.clip(1))) * 100
        results[name] = {"MAE": round(mae, 2), "RMSE": round(rmse, 2),
                         "MAPE": round(mape, 2)}
        print(f"    [Forecast] {name}: MAE={mae:.0f}  RMSE={rmse:.0f}  MAPE={mape:.1f}%")
        if mae < best_mae:
            best_mae, best_model = mae, (name, model)

    # Save best model + metadata
    with open(MODELS_DIR / "sales_forecast.pkl", "wb") as f:
        pickle.dump({"model": best_model[1], "features": feature_cols,
                     "name": best_model[0], "weekly_df": wk}, f)

    return {"metrics": results, "best": best_model[0], "weekly_df": wk,
            "feature_cols": feature_cols}


# ── B: Customer Churn Risk ────────────────────────────────────────────────────

def _prepare_churn_features(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["is_completed"]]
    cust = (
        completed.groupby("customer_id")
        .agg(
            customer_segment=  ("customer_segment",       "first"),
            days_since_last_purchase=("days_since_last_purchase", "first"),
            purchase_frequency=("purchase_frequency",     "first"),
            total_revenue=     ("total_revenue",          "first"),
            avg_order_value=   ("avg_order_value",        "first"),
            is_churned=        ("is_churned",             "first"),
        )
        .reset_index()
        .dropna(subset=["is_churned"])
    )
    le = LabelEncoder()
    cust["segment_enc"] = le.fit_transform(cust["customer_segment"])
    return cust, le


def train_churn_model(df: pd.DataFrame) -> dict:
    cust, le = _prepare_churn_features(df)

    feature_cols = ["days_since_last_purchase", "purchase_frequency",
                    "total_revenue", "avg_order_value", "segment_enc"]
    X = cust[feature_cols]
    y = cust["is_churned"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )

    models = {
        "LogisticRegression": LogisticRegression(max_iter=500, random_state=RANDOM_SEED),
        "RandomForest":       RandomForestClassifier(n_estimators=150, max_depth=6,
                                                     random_state=RANDOM_SEED, n_jobs=-1),
    }

    results = {}
    best_model, best_auc = None, 0

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]
        acc   = accuracy_score(y_test, preds)
        prec  = precision_score(y_test, preds, zero_division=0)
        rec   = recall_score(y_test, preds, zero_division=0)
        f1    = f1_score(y_test, preds, zero_division=0)
        auc   = roc_auc_score(y_test, proba)
        results[name] = {"Accuracy": round(acc, 4), "Precision": round(prec, 4),
                         "Recall": round(rec, 4), "F1": round(f1, 4),
                         "ROC_AUC": round(auc, 4)}
        print(f"    [Churn] {name}: Acc={acc:.3f}  F1={f1:.3f}  AUC={auc:.3f}")
        if auc > best_auc:
            best_auc, best_model = auc, (name, model)

    with open(MODELS_DIR / "churn_model.pkl", "wb") as f:
        pickle.dump({"model": best_model[1], "features": feature_cols,
                     "name": best_model[0], "label_encoder": le,
                     "customer_df": cust}, f)

    return {"metrics": results, "best": best_model[0]}


# ── C: Product Demand Prediction ─────────────────────────────────────────────

def _prepare_demand_features(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["is_completed"]]
    cat_wk = (
        completed.groupby(["product_category", "week_start"])
        .agg(units=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
        .sort_values(["product_category", "week_start"])
    )
    cat_wk["week_start"] = pd.to_datetime(cat_wk["week_start"])
    cat_wk["week_num"]   = cat_wk["week_start"].dt.isocalendar().week.astype(int)
    cat_wk["month"]      = cat_wk["week_start"].dt.month
    cat_wk["t"]          = cat_wk.groupby("product_category").cumcount()

    for lag in [1, 2, 4]:
        cat_wk[f"units_lag{lag}"] = (
            cat_wk.groupby("product_category")["units"].shift(lag)
        )
    cat_wk["units_roll4"] = (
        cat_wk.groupby("product_category")["units"]
        .transform(lambda x: x.shift(1).rolling(4).mean())
    )

    le = LabelEncoder()
    cat_wk["cat_enc"] = le.fit_transform(cat_wk["product_category"])
    return cat_wk.dropna(), le


def train_demand_model(df: pd.DataFrame) -> dict:
    cat_wk, le = _prepare_demand_features(df)

    feature_cols = ["cat_enc", "week_num", "month", "t",
                    "units_lag1", "units_lag2", "units_lag4", "units_roll4"]
    X = cat_wk[feature_cols]
    y = cat_wk["units"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED
    )

    model = RandomForestRegressor(n_estimators=200, max_depth=8,
                                  random_state=RANDOM_SEED, n_jobs=-1)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae  = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    print(f"    [Demand] RandomForest: MAE={mae:.1f}  RMSE={rmse:.1f}")

    with open(MODELS_DIR / "demand_model.pkl", "wb") as f:
        pickle.dump({"model": model, "features": feature_cols,
                     "name": "RandomForest", "label_encoder": le,
                     "cat_wk_df": cat_wk}, f)

    return {"metrics": {"MAE": round(mae, 2), "RMSE": round(rmse, 2)},
            "best": "RandomForest"}


# ── Main ─────────────────────────────────────────────────────────────────────

def run() -> dict:
    df = pd.read_parquet(DATA_PROCESSED / "orders_features.parquet")
    print("  Training Sales Forecast model...")
    forecast_info = train_sales_forecast(df)
    print("  Training Customer Churn model...")
    churn_info    = train_churn_model(df)
    print("  Training Product Demand model...")
    demand_info   = train_demand_model(df)
    return {"forecast": forecast_info, "churn": churn_info, "demand": demand_info}


if __name__ == "__main__":
    run()
