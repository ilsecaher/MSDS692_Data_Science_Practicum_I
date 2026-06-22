import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
from utils import (
    NAVY, GOLD, GREEN, RED, GRAY, LIGHT, LAYOUT_BASE,
    load_master, page_header, section_title,
)

st.set_page_config(page_title="What Drives Yield?", page_icon="🧠", layout="wide")
page_header(
    "What Drives Rental Yield?",
    "Feature importance, correlations, and plain-language explanations from the Random Forest model",
)

master = load_master()
df_ml  = master[master["year"].between(2012, 2024)].copy()

# ── Feature importance (from trained RF model) ────────────────────────────────
section_title("Feature Importance — Random Forest")

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
    "direction": [-1, -1, 1, 1, -1, 1, 1, -1, 1, -1],   # +1 = higher → higher yield
})

CAT_COLORS = {
    "Demographic (ACS)": NAVY,
    "Market (Zillow)":   "#4472C4",
    "College (IPEDS)":   GOLD,
}

fi_sorted = FI.sort_values("importance")

col_fi1, col_fi2 = st.columns([3, 2])
with col_fi1:
    fig_fi = go.Figure(go.Bar(
        x=fi_sorted["importance"],
        y=fi_sorted["feature"],
        orientation="h",
        marker_color=fi_sorted["category"].map(CAT_COLORS).fillna(GRAY).tolist(),
        text=[f"{v:.4f}" for v in fi_sorted["importance"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
    ))
    for cat, color in CAT_COLORS.items():
        fig_fi.add_trace(go.Bar(x=[None], y=[None], name=cat,
                                marker_color=color, showlegend=True))
    fig_fi.update_layout(
        **LAYOUT_BASE,
        title="<b>Top 10 Feature Importances</b>",
        xaxis=dict(title="Relative Importance", showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=-0.15, x=0),
        height=400, margin=dict(l=10, r=80, t=45, b=60),
        barmode="overlay",
    )
    st.plotly_chart(fig_fi, use_container_width=True)

with col_fi2:
    cat_totals = FI.groupby("category")["importance"].sum().reset_index()
    fig_pie = go.Figure(go.Pie(
        labels=cat_totals["category"],
        values=cat_totals["importance"],
        hole=0.45,
        marker_colors=cat_totals["category"].map(CAT_COLORS).fillna(GRAY).tolist(),
        textinfo="label+percent",
        pull=[0.05] * len(cat_totals),
    ))
    fig_pie.update_layout(
        **LAYOUT_BASE,
        title="<b>Importance by Data Source</b>",
        height=400, margin=dict(l=10, r=10, t=45, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Plain-language interpretation ──────────────────────────────────────────────
section_title("Plain-Language Interpretation")

explanations = [
    (NAVY,  "Median Home Value (most important — 32%)",
     "The single strongest predictor of rental yield. "
     "Lower home values relative to rents produce higher gross yields — the "
     "fundamental yield formula (annual rent ÷ home value) means cheaper markets "
     "with stable rents consistently outperform expensive ones."),
    (NAVY,  "Median Household Income (7%)",
     "Higher-income areas attract renters who can afford more, supporting stronger "
     "rents. However, higher incomes also correlate with higher home values, so the "
     "net effect on yield is moderated."),
    (NAVY,  "Median Gross Rent (6%)",
     "Directly drives the numerator of the yield formula. Markets with higher rents "
     "relative to home prices produce higher yields. ACS rent is used as a fallback "
     "where Zillow ZORI data is unavailable."),
    ("#4472C4", "ZORI Availability Flag (6%)",
     "Counties with actual Zillow rent index data (vs ACS-imputed estimates) have "
     "more accurate yield estimates. The flag itself captures a data quality dimension "
     "that correlates with market size and liquidity."),
    (NAVY,  "Vacancy Rate (5%)",
     "High vacancy drags yields downward: excess supply weakens landlord pricing power. "
     "College towns with chronic housing shortages (low vacancy) sustain stronger rent "
     "growth and higher yields over time."),
    (GOLD,  "Enrollment Intensity & Housing Capacity (College IPEDS)",
     "Counties where student enrollment substantially exceeds on-campus housing capacity "
     "create persistent off-campus rental demand. This structural imbalance is one of "
     "the key differentiating factors unique to college-town markets."),
]

for color, title, text in explanations:
    st.markdown(
        f"""<div style="background:{LIGHT};border-left:4px solid {color};
            border-radius:6px;padding:12px 16px;margin-bottom:10px">
          <strong style="color:{NAVY}">{title}</strong>
          <p style="margin:6px 0 0;font-size:13px;color:{GRAY};line-height:1.6">{text}</p>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Correlation scatter plots ─────────────────────────────────────────────────
section_title("Yield vs Top Features — 2012–2024 Data")

SCATTER_FEATURES = [
    ("median_home_value",      "Median Home Value ($)",    True),
    ("median_gross_rent",      "Median Gross Rent ($/mo)", False),
    ("vacancy_rate",           "Vacancy Rate",             True),
    ("enrollment_intensity",   "Enrollment Intensity",     False),
]

scatter_df = df_ml[
    ["gross_rental_yield"] + [f for f, _, _ in SCATTER_FEATURES]
].dropna().sample(min(3000, len(df_ml)), random_state=42)

cols = st.columns(2)
for i, (feat, label, flip) in enumerate(SCATTER_FEATURES):
    if feat not in scatter_df.columns:
        continue
    corr = scatter_df["gross_rental_yield"].corr(scatter_df[feat])
    fig_s = px.scatter(
        scatter_df.sample(min(1500, len(scatter_df)), random_state=i),
        x=feat, y="gross_rental_yield",
        opacity=0.35,
        color_discrete_sequence=[NAVY],
        trendline="ols",
        trendline_color_override=GOLD,
        labels={feat: label, "gross_rental_yield": "Gross Rental Yield"},
    )
    fig_s.update_traces(marker_size=4)
    fig_s.update_layout(
        **LAYOUT_BASE,
        title=f"<b>Yield vs {label}</b><br>"
              f"<sup style='color:{GRAY}'>Pearson r = {corr:.3f}</sup>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickformat=".1%"),
        height=300, margin=dict(l=10, r=10, t=60, b=40),
    )
    with cols[i % 2]:
        st.plotly_chart(fig_s, use_container_width=True)

# ── Key takeaway ──────────────────────────────────────────────────────────────
st.markdown(
    f"""<div style="background:{NAVY};border-radius:10px;padding:20px 24px;margin-top:8px">
      <p style="color:{GOLD};font-size:13px;font-weight:600;margin:0 0 6px">KEY FINDING</p>
      <p style="color:white;font-size:14px;line-height:1.7;margin:0">
        Counties with <strong style="color:{GOLD}">stronger rent growth</strong>,
        <strong style="color:{GOLD}">persistent housing shortages</strong>,
        and <strong style="color:{GOLD}">large student populations</strong> relative to
        on-campus capacity tend to produce higher and more stable gross rental yields.
        The interaction between affordable home prices and inelastic student rental demand
        is the most reliable signal the model found across 13 years of data.
      </p>
    </div>""",
    unsafe_allow_html=True,
)
