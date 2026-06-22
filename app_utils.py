import pandas as pd
import streamlit as st

# ── Brand palette ─────────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
GOLD   = "#F2B705"
RED    = "#C00000"
GREEN  = "#1A7238"
LIGHT  = "#EAF0FB"
GRAY   = "#6B7280"
FONT   = dict(family="Arial, sans-serif")

LAYOUT_BASE = dict(
    font=FONT,
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font=dict(size=16, color=NAVY, family="Arial, sans-serif"),
)

NAVY_SCALE = [[0, LIGHT], [0.5, "#4472C4"], [1, NAVY]]

# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data
def load_predictions():
    df = pd.read_csv("predictions_2025_2026.csv")
    for col in ["predicted_yield", "yield_2024", "yield_change"]:
        df[col + "_pct"] = df[col] * 100
    return df

@st.cache_data
def load_master():
    return pd.read_csv("MasterCollegeTowns.csv")

@st.cache_data
def load_merged():
    master = load_master()
    pred   = load_predictions()

    fin = master[master["year"] == 2024][[
        "state", "county", "median_home_value", "median_gross_rent",
        "median_household_income", "vacancy_rate", "pct_bachelor_plus",
        "avg_zhvi", "avg_zori",
    ]].copy()

    enr = master[(master["year"] == 2021) & (master["total_enrollment"] > 0)][[
        "state", "county", "total_enrollment", "total_housing_cap",
        "enrollment_intensity", "student_per_housing_unit",
    ]].copy()
    enr["housing_deficit"] = (enr["total_enrollment"] - enr["total_housing_cap"]).clip(lower=0)

    p25 = pred[pred["year"] == 2025][[
        "state", "county", "predicted_yield_pct", "yield_2024_pct",
        "yield_change_pct", "confidence",
    ]].rename(columns={"predicted_yield_pct": "yield_2025_pct"})
    p26 = pred[pred["year"] == 2026][["state", "county", "predicted_yield_pct"]
    ].rename(columns={"predicted_yield_pct": "yield_2026_pct"})

    df = (p25
          .merge(p26,  on=["state", "county"], how="left")
          .merge(fin,  on=["state", "county"], how="left")
          .merge(enr,  on=["state", "county"], how="left"))
    return df

# ── Shared UI helpers ─────────────────────────────────────────────────────────
def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="background:{NAVY};padding:18px 24px 12px;border-radius:10px;margin-bottom:16px">
          <h1 style="color:white;margin:0;font-size:22px;font-family:Arial,sans-serif">{title}</h1>
          <p style="color:{GOLD};margin:4px 0 0;font-size:13px;font-family:Arial,sans-serif">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_row(metrics: list[tuple]):
    """metrics = list of (label, value, accent_color)"""
    cols = st.columns(len(metrics))
    for col, (label, value, color) in zip(cols, metrics):
        col.markdown(
            f"""<div style="background:{LIGHT};border-left:4px solid {color};
                border-radius:8px;padding:12px 14px">
              <div style="font-size:22px;font-weight:700;color:{NAVY}">{value}</div>
              <div style="font-size:11px;color:{GRAY};margin-top:2px">{label}</div>
            </div>""",
            unsafe_allow_html=True,
        )

def section_title(text: str):
    st.markdown(
        f'<h3 style="color:{NAVY};font-family:Arial,sans-serif;'
        f'border-bottom:2px solid {GOLD};padding-bottom:4px;margin:18px 0 10px">{text}</h3>',
        unsafe_allow_html=True,
    )
