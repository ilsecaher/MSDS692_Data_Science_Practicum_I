# Machine Learning Framework for Rental Investment Analysis in College Towns

**Course:** MSDS 692 — Data Science Practicum I · Regis University · June 2026
**Author:** Ilse Severance

---

## Research Question

> *Which U.S. college-town counties appear to have the strongest rental investment potential, and why?*

---

## Project Overview

This project builds an end-to-end machine learning pipeline to identify which U.S. college-town counties offer the strongest **gross rental yield** potential for real estate investors. A **Random Forest** model trained on 13 years of county-level data generates forward-looking yield predictions for **2025 and 2026** across **428 counties spanning 49 states**.

The analysis integrates three primary data sources — rental market data (Zillow), demographic and housing characteristics (U.S. Census ACS), and college enrollment figures (IPEDS) — to capture the unique demand dynamics that distinguish college towns from the broader housing market.

---

## Key Results

| Metric | Value |
|---|---|
| Best Model | Random Forest |
| MAE (2024 test set) | 0.57 percentage points |
| RMSE | 0.79 percentage points |
| R² | 66% |
| Counties covered | 428 |
| States covered | 49 |
| Historical data range | 2012–2024 |
| Forecast horizon | 2025–2026 |
| Models compared | RF, LightGBM, XGBoost, Ridge |

---

## Data Sources

| Source | Description |
|---|---|
| **Zillow ZORI / ZHVI** | Monthly rent index and home value index at county level, 2012–2024 |
| **U.S. Census ACS** | 5-year estimates for income, rent, home value, vacancy rate, and educational attainment |
| **IPEDS** | Annual enrollment, housing capacity, graduation rates, and room & board costs |
| **FRED** | 30-year mortgage rate and federal funds rate |

---

## Project Structure

```
.
├── Overview.py                          # Streamlit entry point (Streamlit Cloud)
├── app.py                               # Alternate local entry point
├── app_utils.py                         # Shared utilities, color palette, data loaders
├── pages/
│   ├── 1_Explore_the_Market.py
│   ├── 2_Investment_Opportunities.py
│   ├── 3_Comparison_Tool.py
│   ├── 4_Historical_Trends.py
│   └── 5_The_Model.py
├── MSDS692_Data_Science_Practicum_I - Ilse Severance.ipynb
├── MasterCollegeTowns.csv
├── predictions_2025_2026.csv
├── requirements.txt
└── .env                                 # CENSUS_API_KEY (not committed)
```

---

## Dashboard Pages

| Page | Description |
|---|---|
| **Overview** | Project summary, KPIs, model performance, data sources |
| **Explore the Market** | Choropleth map, filterable county table, CSV download |
| **Investment Opportunities** | Top yield-gain counties; hidden gems |
| **Comparison Tool** | Side-by-side comparison of up to 5 counties |
| **Historical Trends** | Time series 2012–2024 + 2025–2026 forecasts |
| **The Model** | Feature importance, scatter plots, yield simulator |

---

## Methodology Summary

**Target variable:** Gross Rental Yield = (Annual Rent ÷ Home Value) × 100

**College-town filter:** Counties with peak enrollment ≥ 3,000 students at any point 2012–2024

**Walk-forward cross-validation (4 folds — no data leakage):**

| Fold | Train | Validate |
|---|---|---|
| 1 | 2012–2019 | 2020 |
| 2 | 2012–2020 | 2021 |
| 3 | 2012–2021 | 2022 |
| 4 | 2012–2022 | 2023 |
| Final | 2012–2023 | **2024 (held-out)** |

**Final model:** Retrained on full 2012–2024 dataset to generate 2025–2026 predictions.

---

## Top Feature Importances

| Feature | Importance | Source |
|---|---|---|
| median_home_value | 32.0% | ACS |
| median_household_income | 6.9% | ACS |
| median_gross_rent | 6.2% | ACS |
| vacancy_rate | 4.9% | ACS |
| enrollment_intensity | 3.0% | IPEDS |

**Key finding:** Counties with lower home values, persistent housing shortages, and large student populations relative to on-campus capacity produce the highest and most stable gross rental yields.

---

## Limitations

- Gross yield is a **pre-expense** metric (excludes taxes, maintenance, insurance).
- IPEDS enrollment data available through **2021 only**.
- Map shows **state-level averages** only.
- Predictions are for **screening purposes only**, not investment advice.
