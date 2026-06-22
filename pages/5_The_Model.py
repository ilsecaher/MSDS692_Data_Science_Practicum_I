import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
from app_utils import (
    NAVY, GOLD, GREEN, RED, GRAY, LIGHT, LAYOUT_BASE,
    load_master, load_merged, page_header, section_title,
)

st.set_page_config(page_title="The Model", page_icon="🧠", layout="wide")
page_header(
    "The Model",
    "How it was built · what it learned · and a yield simulator to test it",
)

master = load_master()
df_ml  = master[master["year"].between(2012, 2024)].copy()
merged = load_merged()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — MODEL PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
section_title("Model Performance — Test Set 2024")

perf_col, chart_col = st.columns([2, 3])

with perf_col:
    st.markdown(
        f"""<div style="background:{NAVY};border-radius:10px;padding:20px 24px">
          <p style="color:{GOLD};font-size:12px;margin:0 0 4px;letter-spacing:0.5px">
            BEST MODEL · RANDOM FOREST
          </p>
          <p style="color:#B0C4E8;font-size:12px;margin:0 0 16px">
            Train 2012–2023 (6,113 rows) · Test 2024 (510 rows)
          </p>
          <div style="display:flex;gap:12px">
            <div style="flex:1;background:rgba(255,255,255,0.08);border-radius:8px;
                        padding:14px;text-align:center">
              <div style="color:{GOLD};font-size:24px;font-weight:700">0.57%</div>
              <div style="color:#B0C4E8;font-size:11px;margin-top:4px">MAE</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,0.08);border-radius:8px;
                        padding:14px;text-align:center">
              <div style="color:{GOLD};font-size:24px;font-weight:700">0.79%</div>
              <div style="color:#B0C4E8;font-size:11px;margin-top:4px">RMSE</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,0.08);border-radius:8px;
                        padding:14px;text-align:center">
              <div style="color:{GOLD};font-size:24px;font-weight:700">66%</div>
              <div style="color:#B0C4E8;font-size:11px;margin-top:4px">R² (variance explained)</div>
            </div>
          </div>
          <p style="color:#8AA6C8;font-size:11px;margin:12px 0 0;line-height:1.5">
            Walk-forward cross-validation (4 folds). Errors are in percentage-point
            yield — 0.57% MAE on a ~6% average yield is ~9% relative error.
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

with chart_col:
    models = ["Random Forest", "XGBoost", "LightGBM", "Ridge (baseline)"]
    maes   = [0.567, 0.605, 0.627, 0.747]
    colors = [GOLD if m == "Random Forest" else NAVY for m in models]

    fig_cmp = go.Figure(go.Bar(
        x=maes, y=models, orientation="h",
        marker_color=colors,
        text=[f"{v:.3f}%" for v in maes],
        textposition="outside",
    ))
    fig_cmp.update_layout(
        **LAYOUT_BASE,
        title="<b>Model Comparison — MAE on 2024 Test Set (lower is better)</b>",
        xaxis=dict(title="MAE (%)", showgrid=True, gridcolor="#E5E7EB", ticksuffix="%"),
        yaxis=dict(showgrid=False),
        height=240, margin=dict(l=10, r=80, t=45, b=30),
        showlegend=False,
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — WHAT THE MODEL LEARNED
# ══════════════════════════════════════════════════════════════════════════════
section_title("What the Model Learned — Feature Importance")

FI = pd.DataFrame({
    "feature": [
        "median_home_value", "median_household_income", "median_gross_rent",
        "zori_is_real", "vacancy_rate", "zhvi_yoy_pct", "pct_bachelor_plus",
        "unemployment_rate", "enrollment_intensity", "avg_room_board",
    ],
    "importance": [0.3203, 0.0685, 0.0623, 0.0574, 0.0485,
                   0.0412, 0.0388, 0.0321, 0.0298, 0.0254],
    "category": [
        "Demographic (ACS)", "Demographic (ACS)", "Demographic (ACS)",
        "Market (Zillow)", "Demographic (ACS)", "Market (Zillow)",
        "Demographic (ACS)", "Demographic (ACS)", "College (IPEDS)", "College (IPEDS)",
    ],
})
CAT_COLORS = {"Demographic (ACS)": NAVY, "Market (Zillow)": "#4472C4", "College (IPEDS)": GOLD}

fi_col, corr_col = st.columns([3, 2])
fi_sorted = FI.sort_values("importance")

with fi_col:
    fig_fi = go.Figure()
    for cat, color in CAT_COLORS.items():
        sub = fi_sorted[fi_sorted["category"] == cat]
        fig_fi.add_trace(go.Bar(
            x=sub["importance"], y=sub["feature"], orientation="h",
            marker_color=color, name=cat,
            text=[f"{v:.4f}" for v in sub["importance"]],
            textposition="outside",
        ))
    fig_fi.update_layout(
        **LAYOUT_BASE,
        title="<b>Top 10 Feature Importances</b>",
        barmode="overlay",
        xaxis=dict(title="Relative Importance", showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=-0.2, x=0),
        height=380, margin=dict(l=10, r=80, t=45, b=60),
    )
    st.plotly_chart(fig_fi, use_container_width=True)

with corr_col:
    # Compute zhvi_yoy_pct if not present
    corr_df = df_ml.copy()
    if "zhvi_yoy_pct" not in corr_df.columns and "avg_zhvi" in corr_df.columns:
        corr_df = corr_df.sort_values(["state", "county", "year"])
        corr_df["zhvi_yoy_pct"] = (
            corr_df.groupby(["state", "county"])["avg_zhvi"]
            .pct_change() * 100
        )

    CORR_FEATURES = [
        ("median_home_value",  "median_home_value → Yield"),
        ("zhvi_yoy_pct",       "zhvi_yoy_pct → Yield"),
        ("enrollment_intensity","enrollment_intensity → Yield"),
        ("unemployment_rate",  "unemployment_rate → Yield"),
        ("vacancy_rate",       "vacancy_rate → Yield"),
    ]

    corr_rows = []
    for col, label in CORR_FEATURES:
        if col in corr_df.columns and "gross_rental_yield" in corr_df.columns:
            sub = corr_df[[col, "gross_rental_yield"]].dropna()
            r = sub[col].corr(sub["gross_rental_yield"])
            corr_rows.append({"label": label, "corr": round(r, 3)})

    corr_data = pd.DataFrame(corr_rows).sort_values("corr")
    bar_colors = [RED if v < 0 else NAVY for v in corr_data["corr"]]

    fig_corr = go.Figure(go.Bar(
        x=corr_data["corr"],
        y=corr_data["label"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:+.3f}" for v in corr_data["corr"]],
        textposition="outside",
    ))
    fig_corr.update_layout(
        **LAYOUT_BASE,
        title="<b>Correlation by Channel</b>",
        xaxis=dict(
            title="Pearson correlation with Yield",
            showgrid=True, gridcolor="#E5E7EB",
            zeroline=True, zerolinecolor=GRAY, zerolinewidth=1.5,
        ),
        yaxis=dict(showgrid=False),
        height=380, margin=dict(l=10, r=60, t=45, b=30),
        showlegend=False,
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# Key drivers plain language
for color, title, text in [
    (NAVY,     "Median Home Value (32%) — the dominant driver",
     "Lower home values relative to rent produce higher gross yields. The fundamental yield formula "
     "(annual rent ÷ home value) means affordable markets with stable rents consistently outperform expensive ones."),
    (NAVY,     "Vacancy Rate (5%) — the demand signal",
     "High vacancy drags yields down. College towns with chronic housing shortages (low vacancy) sustain "
     "stronger rent growth and higher yields over time."),
    (GOLD,     "Enrollment Intensity & Housing Capacity — the college-town differentiator",
     "Counties where enrollment substantially exceeds on-campus housing capacity create persistent "
     "off-campus rental demand. This structural imbalance is the key factor unique to college-town markets."),
]:
    st.markdown(
        f"""<div style="background:{LIGHT};border-left:4px solid {color};
            border-radius:6px;padding:10px 14px;margin-bottom:8px">
          <strong style="color:{NAVY}">{title}</strong>
          <p style="margin:4px 0 0;font-size:13px;color:{GRAY};line-height:1.6">{text}</p>
        </div>""",
        unsafe_allow_html=True,
    )

# Scatter plots (3 most important relationships)
section_title("Yield vs Key Features — 2012–2024 Data")

scatter_df = df_ml[
    ["gross_rental_yield", "median_home_value", "median_gross_rent", "vacancy_rate"]
].dropna().sample(min(2000, len(df_ml)), random_state=42)

SCATTER_FEATS = [
    ("median_home_value", "Median Home Value ($)"),
    ("median_gross_rent", "Median Gross Rent ($/mo)"),
    ("vacancy_rate",      "Vacancy Rate"),
]
s_cols = st.columns(3)
for i, (feat, label) in enumerate(SCATTER_FEATS):
    corr = scatter_df["gross_rental_yield"].corr(scatter_df[feat])
    fig_s = px.scatter(
        scatter_df.sample(min(1200, len(scatter_df)), random_state=i),
        x=feat, y="gross_rental_yield",
        opacity=0.35,
        color_discrete_sequence=[NAVY],
        trendline="ols",
        trendline_color_override=GOLD,
        labels={feat: label, "gross_rental_yield": "Yield"},
    )
    fig_s.update_traces(marker_size=4)
    fig_s.update_layout(
        **LAYOUT_BASE,
        title=f"<b>Yield vs {label}</b><br><sup>r = {corr:.3f}</sup>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickformat=".1%"),
        height=280, margin=dict(l=10, r=10, t=60, b=40),
    )
    with s_cols[i]:
        st.plotly_chart(fig_s, use_container_width=True)

st.markdown(
    f"""<div style="background:{NAVY};border-radius:10px;padding:18px 22px;margin:8px 0 24px">
      <p style="color:{GOLD};font-size:12px;font-weight:600;margin:0 0 4px">KEY FINDING</p>
      <p style="color:white;font-size:14px;line-height:1.7;margin:0">
        Counties with <strong style="color:{GOLD}">lower home values</strong>,
        <strong style="color:{GOLD}">persistent housing shortages</strong>, and
        <strong style="color:{GOLD}">large student populations</strong> relative to
        on-campus capacity produce the highest and most stable gross rental yields.
        The interaction between affordable entry prices and inelastic student demand
        is the most reliable signal across 13 years of data.
      </p>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — PREDICTION SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════
section_title("Prediction Simulator — Try the Model Logic")

st.markdown(
    f"""<div style="background:{LIGHT};border-left:4px solid {GOLD};border-radius:6px;
        padding:12px 16px;margin-bottom:16px;font-size:13px;color:{GRAY}">
      <strong>Note:</strong> This simulator uses a <strong>formula approximation</strong>
      based on the model's top three drivers (home value, rent, enrollment pressure, vacancy).
      It is <em>not</em> the actual Random Forest — the full model uses 20+ features with
      learned non-linear interactions. Use this to build intuition, not as a precise forecast.
    </div>""",
    unsafe_allow_html=True,
)

nat_med_hv    = merged["median_home_value"].median()
nat_med_rent  = merged["median_gross_rent"].median()
nat_med_enr   = merged["total_enrollment"].dropna().median()
nat_med_cap   = merged["total_housing_cap"].dropna().median()
nat_med_vac   = merged["vacancy_rate"].dropna().median()
nat_med_yield = merged["yield_2025_pct"].median()

col_l, col_r = st.columns([2, 3], gap="large")

with col_l:
    home_value   = st.slider("Median Home Value ($)", 100_000, 1_500_000,
                              int(nat_med_hv), step=10_000, format="%d")
    monthly_rent = st.slider("Median Monthly Rent ($)", 400, 3_000,
                              int(nat_med_rent), step=50, format="%d")
    enrollment   = st.slider("Total Student Enrollment", 500, 80_000,
                              int(nat_med_enr), step=500)
    housing_cap  = st.slider("On-Campus Housing Capacity", 0, 30_000,
                              int(nat_med_cap), step=250)
    vacancy_rate = st.slider("Vacancy Rate (%)", 2.0, 25.0,
                              float(nat_med_vac * 100), step=0.5, format="%.1f")

def estimate_yield(hv, rent, enr, cap, vac):
    base          = (rent * 12) / hv * 100
    deficit_ratio = max(0, enr - cap) / max(enr, 1)
    enr_boost     = 1 + 0.12 * deficit_ratio
    vac_penalty   = max(0.75, 1 - max(0, (vac / 100 - 0.05) * 2.5))
    return round(max(1.0, min(16.0, base * enr_boost * vac_penalty)), 2)

est    = estimate_yield(home_value, monthly_rent, enrollment, housing_cap, vacancy_rate)
base   = round((monthly_rent * 12) / home_value * 100, 2)
deficit = max(0, enrollment - housing_cap)
delta  = est - nat_med_yield
color  = GREEN if delta >= 0 else RED

with col_r:
    st.markdown(
        f"""<div style="background:{NAVY};border-radius:12px;padding:24px 28px;
            text-align:center;margin-bottom:14px">
          <div style="color:{GOLD};font-size:12px;letter-spacing:1px;margin-bottom:4px">
            ESTIMATED GROSS RENTAL YIELD
          </div>
          <div style="color:white;font-size:54px;font-weight:700;line-height:1">
            {est:.2f}%
          </div>
          <div style="color:{color};font-size:15px;margin-top:8px">
            {'+' if delta >= 0 else ''}{delta:.2f}% vs national median ({nat_med_yield:.2f}%)
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)
    for col, lbl, val, accent in [
        (s1, "Base Yield\n(rent/price)", f"{base:.2f}%", NAVY),
        (s2, "Housing\nDeficit", f"{deficit:,.0f}", GOLD),
        (s3, "Vacancy\nRate", f"{vacancy_rate:.1f}%", RED if vacancy_rate > 8 else GREEN),
    ]:
        col.markdown(
            f'<div style="background:{LIGHT};border-left:3px solid {accent};border-radius:6px;'
            f'padding:10px;text-align:center"><div style="font-size:18px;font-weight:700;color:{NAVY}">'
            f'{val}</div><div style="font-size:11px;color:{GRAY};white-space:pre-line">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Comparator
    comparators = {
        "Your estimate":         est,
        "Top quartile (75th)":   merged["yield_2025_pct"].quantile(0.75),
        "National median":       nat_med_yield,
        "Bottom quartile (25th)":merged["yield_2025_pct"].quantile(0.25),
    }
    fig_cmp2 = go.Figure(go.Bar(
        x=list(comparators.values()), y=list(comparators.keys()), orientation="h",
        marker_color=[GOLD if k == "Your estimate" else NAVY for k in comparators],
        text=[f"{v:.2f}%" for v in comparators.values()],
        textposition="outside",
    ))
    fig_cmp2.update_layout(
        **LAYOUT_BASE,
        title="<b>How Does Your Estimate Compare? (RF model quartiles)</b>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="%"),
        yaxis=dict(showgrid=False),
        height=220, margin=dict(l=10, r=80, t=45, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig_cmp2, use_container_width=True)

    # Sensitivity curve
    hv_range    = np.linspace(100_000, 1_500_000, 60)
    sens_yields = [estimate_yield(hv, monthly_rent, enrollment, housing_cap, vacancy_rate)
                   for hv in hv_range]
    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(
        x=hv_range / 1000, y=sens_yields,
        mode="lines", line=dict(color=NAVY, width=2.5),
    ))
    fig_sens.add_vline(x=home_value / 1000, line_dash="dot", line_color=GOLD, line_width=2,
                       annotation_text=f"${home_value/1000:.0f}k",
                       annotation_font_color=GOLD)
    fig_sens.update_layout(
        **LAYOUT_BASE,
        title="<b>Sensitivity — Yield vs Home Value (all other inputs fixed)</b>",
        xaxis=dict(title="Home Value ($000s)", ticksuffix="k",
                   showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(title="Estimated Yield (%)", ticksuffix="%",
                   showgrid=True, gridcolor="#E5E7EB"),
        height=260, margin=dict(l=10, r=20, t=45, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_sens, use_container_width=True)
