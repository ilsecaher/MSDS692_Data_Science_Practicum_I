import pandas as pd
import streamlit as st

# ── Brand palette ─────────────────────────────────────────────────────────────
TEAL   = "#0D3349"   # deep teal — page headers / hero banners
NAVY   = "#1B3A6B"   # navy blue — chart bars, borders, text
MID    = "#4472C4"   # mid blue — secondary chart elements
GOLD   = "#F2B705"   # gold — predicted lines, accents
RED    = "#C00000"   # red — negatives / alerts
GREEN  = "#1A7238"   # green — positive gains
LIGHT  = "#D4E6F1"   # light blue — card backgrounds (matches slide cards)
GRAY   = "#6B7280"   # gray — body text, captions
FONT   = dict(family="Arial, sans-serif")

LAYOUT_BASE = dict(
    font=FONT,
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font=dict(size=16, color=NAVY, family="Arial, sans-serif"),
)

NAVY_SCALE = [[0, "#EAF2F8"], [0.5, MID], [1, TEAL]]

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
        <div style="background:linear-gradient(135deg,{TEAL} 0%,#0F4060 100%);
                    padding:20px 28px 14px;border-radius:10px;margin-bottom:16px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.18)">
          <h1 style="color:white;margin:0;font-size:24px;font-family:Arial,sans-serif;
                     font-weight:700;letter-spacing:0.3px">{title}</h1>
          <p style="color:{GOLD};margin:5px 0 0;font-size:13px;font-family:Arial,sans-serif;
                    letter-spacing:0.2px">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_row(metrics: list[tuple]):
    """metrics = list of (label, value, accent_color)"""
    cols = st.columns(len(metrics))
    for col, (label, value, color) in zip(cols, metrics):
        col.markdown(
            f"""<div style="background:{LIGHT};border-left:5px solid {color};
                border-radius:8px;padding:12px 16px;
                box-shadow:0 1px 4px rgba(13,51,73,0.08)">
              <div style="font-size:22px;font-weight:700;color:{TEAL}">{value}</div>
              <div style="font-size:11px;color:{GRAY};margin-top:3px;letter-spacing:0.2px">{label}</div>
            </div>""",
            unsafe_allow_html=True,
        )

def section_title(text: str):
    st.markdown(
        f'<h3 style="color:{TEAL};font-family:Arial,sans-serif;font-weight:700;'
        f'border-bottom:2px solid {GOLD};padding-bottom:5px;margin:20px 0 12px">{text}</h3>',
        unsafe_allow_html=True,
    )
