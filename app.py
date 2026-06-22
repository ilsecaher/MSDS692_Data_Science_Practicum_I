import streamlit as st
from app_utils import (
    NAVY, GOLD, GREEN, LIGHT, GRAY, FONT,
    load_predictions, page_header, kpi_row, section_title,
)

st.set_page_config(
    page_title="College Town Rental Investment Dashboard",
    page_icon="🏘️",
    layout="wide",
)

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
      <p style="color:#8AA6C8;margin:12px 0 0;font-size:13px;font-family:Arial,sans-serif">
        Use the sidebar to explore all pages →
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

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
        """
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
        ("Zillow (ZORI / ZHVI)", "Monthly rent index and home value index at county level, 2012–2024. Primary source for yield computation."),
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
          <p style="color:#B0C4E8;font-size:12px;margin:0 0 16px">Test set: 2024 · 510 counties · trained on 2012–2023</p>
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
            2024 test set. A 0.57% MAE on yields averaging ~6% represents ~9% relative error.
            See <strong style="color:{GOLD}">The Model</strong> page for full details.
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

    section_title("Dataset at a Glance")
    rows = [
        ("Training rows", "6,113"),
        ("Test rows (2024)", "510"),
        ("Features used", "20+"),
        ("CV strategy", "Walk-forward (yearly folds)"),
        ("Prediction years", "2025 & 2026"),
        ("Models compared", "RF, LightGBM, XGBoost, Ridge"),
    ]
    for label, val in rows:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:5px 0;'
            f'border-bottom:1px solid #E5E7EB;font-size:13px">'
            f'<span style="color:{GRAY}">{label}</span>'
            f'<span style="color:{NAVY};font-weight:600">{val}</span></div>',
            unsafe_allow_html=True,
        )
