import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (
    NAVY, GOLD, RED, GREEN, LIGHT, GRAY, FONT, LAYOUT_BASE,
    load_predictions, load_master, page_header, kpi_row, section_title,
)

st.set_page_config(
    page_title="College Town Rental Investment Dashboard",
    page_icon="🏘️",
    layout="wide",
)

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:{NAVY};padding:32px 36px 24px;border-radius:12px;margin-bottom:24px">
      <p style="color:{GOLD};font-size:13px;font-family:Arial,sans-serif;
                margin:0 0 8px;letter-spacing:1px;text-transform:uppercase">
        MSDS 692 · Data Science Practicum I · Ilse Severance
      </p>
      <h1 style="color:white;margin:0;font-size:30px;font-family:Arial,sans-serif;line-height:1.25">
        Machine Learning Framework for Rental<br>Investment Analysis in College Towns
      </h1>
      <p style="color:#B0C4E8;margin:14px 0 0;font-size:15px;font-family:Arial,sans-serif;
                max-width:720px;line-height:1.6">
        <em style="color:{GOLD};font-style:normal;font-weight:600">Research question:</em>
        Which U.S. college-town counties appear to have the strongest rental investment
        potential, and why?
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Top-line stats ────────────────────────────────────────────────────────────
kpi_row([
    ("College-Town Counties", "428", NAVY),
    ("States Covered", "49", GOLD),
    ("Years of Historical Data", "2012–2024", NAVY),
    ("Forecast Horizon", "2025–2026", GOLD),
    ("Best Model", "Random Forest", GREEN),
])

st.markdown("<br>", unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    section_title("Project Overview")
    st.markdown(
        f"""
        This project builds a machine learning pipeline to identify which U.S. college-town
        counties offer the strongest gross rental yield potential for real estate investors.
        Using a **Random Forest** model trained on 13 years of county-level data, we generate
        forward-looking yield predictions for **2025 and 2026** across 428 counties spanning
        49 states.

        The analysis integrates three primary data sources — rental market data (Zillow),
        demographic and housing characteristics (U.S. Census ACS), and college enrollment
        figures (IPEDS) — to capture the unique demand dynamics that distinguish college
        towns from the broader housing market.

        The core insight is that college towns create persistent, inelastic rental demand:
        students need housing regardless of economic cycles, yet housing supply in many
        markets has failed to keep pace with enrollment growth. Counties where this
        imbalance is most acute tend to sustain higher gross rental yields over time.
        """,
    )

    section_title("Data Sources")
    for src, desc in [
        ("Zillow (ZORI / ZHVI)", "Monthly rent index (ZORI) and home value index (ZHVI) at county level, 2012–2024. Primary source for yield computation."),
        ("U.S. Census ACS", "5-year estimates for income, rent, home value, vacancy rate, and educational attainment. Interpolated across census waves."),
        ("IPEDS (Postsecondary Education)", "Annual enrollment, housing capacity, graduation rates, room & board costs, and admissions data for colleges within each county."),
    ]:
        st.markdown(
            f"""<div style="background:{LIGHT};border-left:4px solid {GOLD};
                border-radius:6px;padding:10px 14px;margin-bottom:8px">
              <strong style="color:{NAVY}">{src}</strong><br>
              <span style="font-size:13px;color:{GRAY}">{desc}</span>
            </div>""",
            unsafe_allow_html=True,
        )

with col_right:
    section_title("Final Model Performance")
    st.markdown(
        f"""<div style="background:{NAVY};border-radius:10px;padding:20px 24px;margin-bottom:16px">
          <p style="color:{GOLD};font-size:12px;margin:0 0 4px;letter-spacing:0.5px">BEST MODEL · RANDOM FOREST</p>
          <p style="color:#B0C4E8;font-size:12px;margin:0 0 16px">Test set: 2024 (510 counties)</p>
          <div style="display:flex;gap:16px;flex-wrap:wrap">
            <div style="flex:1;background:rgba(255,255,255,0.08);border-radius:8px;padding:14px;text-align:center">
              <div style="color:{GOLD};font-size:24px;font-weight:700">0.57%</div>
              <div style="color:#B0C4E8;font-size:11px;margin-top:4px">MAE</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,0.08);border-radius:8px;padding:14px;text-align:center">
              <div style="color:{GOLD};font-size:24px;font-weight:700">0.79%</div>
              <div style="color:#B0C4E8;font-size:11px;margin-top:4px">RMSE</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,0.08);border-radius:8px;padding:14px;text-align:center">
              <div style="color:{GOLD};font-size:24px;font-weight:700">0.66</div>
              <div style="color:#B0C4E8;font-size:11px;margin-top:4px">R²</div>
            </div>
          </div>
          <p style="color:#8AA6C8;font-size:11px;margin:12px 0 0;line-height:1.5">
            Tuned RF outperformed LightGBM, XGBoost, and Ridge baselines on the held-out
            2024 test set. Errors are in percentage-point yield — a 0.57% MAE on yields
            averaging ~6% represents roughly 9% relative error.
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

    section_title("Model Comparison")
    models = ["Random Forest", "LightGBM", "XGBoost", "Ridge (baseline)"]
    maes   = [0.567, 0.627, 0.605, 0.747]
    colors = [GOLD if m == "Random Forest" else "#4472C4" for m in models]

    fig = go.Figure(go.Bar(
        x=maes, y=models, orientation="h",
        marker_color=colors,
        text=[f"{v:.3f}%" for v in maes],
        textposition="outside",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        xaxis=dict(title="MAE (%, lower is better)", showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=False),
        height=220, margin=dict(l=10, r=60, t=10, b=30),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    section_title("How to Use This Dashboard")
    steps = [
        ("🗺️ National Map", "Bird's-eye view of predicted yields by state"),
        ("🔍 County Explorer", "Filter and search all 428 counties"),
        ("💰 Investment Opportunities", "AI-curated high-potential markets"),
        ("⚖️ Comparison Tool", "Compare up to 5 counties side-by-side"),
        ("📈 Historical Trends", "13-year trajectory for any county"),
        ("🧠 What Drives Yield?", "Feature importance and key drivers"),
        ("🎮 Prediction Simulator", "What-if yield estimator"),
    ]
    for icon_name, desc in steps:
        st.markdown(
            f'<div style="padding:4px 0;font-size:13px">'
            f'<strong style="color:{NAVY}">{icon_name}</strong>'
            f'<span style="color:{GRAY}"> — {desc}</span></div>',
            unsafe_allow_html=True,
        )
