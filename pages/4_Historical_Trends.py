import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app_utils import NAVY, GOLD, GRAY, LIGHT, LAYOUT_BASE, load_master, load_predictions, page_header, section_title

st.set_page_config(page_title="Historical Trends", page_icon="📈", layout="wide")
page_header(
    "Historical Trends",
    "County-level time series 2012–2024 extended with 2025–2026 model predictions",
)

master = load_master()
pred   = load_predictions()

c1, c2 = st.columns(2)
state_opts = ["All States"] + sorted(master["state"].unique().tolist())
state_sel  = c1.selectbox("State", state_opts)

county_opts = (
    ["All Counties (national median)"] if state_sel == "All States"
    else sorted(master[master["state"] == state_sel]["county"].unique().tolist())
)
county_sel = c2.selectbox("County", county_opts)

# ── Aggregate historical ──────────────────────────────────────────────────────
hist = master[master["year"] <= 2024].copy()
if state_sel != "All States":
    hist = hist[hist["state"] == state_sel]
if county_sel not in ("All Counties (national median)", ""):
    hist = hist[hist["county"] == county_sel]

hist_agg = (
    hist.groupby("year")
    .agg(
        gross_rental_yield=("gross_rental_yield", "median"),
        avg_zori=("avg_zori", "median"),
        avg_zhvi=("avg_zhvi", "median"),
    )
    .reset_index()
)

# ── Prediction extension ──────────────────────────────────────────────────────
pred_view = pred.copy()
if state_sel != "All States":
    pred_view = pred_view[pred_view["state"] == state_sel]
if county_sel not in ("All Counties (national median)", ""):
    pred_view = pred_view[pred_view["county"] == county_sel]

pred_agg = (
    pred_view.groupby("year")["predicted_yield"].median().reset_index()
    .rename(columns={"predicted_yield": "gross_rental_yield"})
)
bridge = hist_agg.loc[hist_agg["year"] == 2024, "gross_rental_yield"]
if len(bridge) > 0:
    bridge_row = pd.DataFrame({"year": [2024], "gross_rental_yield": [bridge.values[0]]})
    pred_ext = pd.concat([bridge_row, pred_agg[pred_agg["year"] > 2024]], ignore_index=True)
else:
    pred_ext = pred_agg[pred_agg["year"] > 2024]

# ── PRIMARY CHART: Yield trend ────────────────────────────────────────────────
section_title("Gross Rental Yield — Actual 2012–2024 + Predicted 2025–2026")

fig_yield = go.Figure()
fig_yield.add_trace(go.Scatter(
    x=hist_agg["year"], y=hist_agg["gross_rental_yield"] * 100,
    mode="lines+markers",
    line=dict(color=NAVY, width=2.5),
    marker=dict(size=7, color=NAVY),
    name="Actual (Median)",
))
if len(pred_ext) > 1:
    fig_yield.add_trace(go.Scatter(
        x=pred_ext["year"], y=pred_ext["gross_rental_yield"] * 100,
        mode="lines+markers",
        line=dict(color=GOLD, width=2.5, dash="dash"),
        marker=dict(size=9, symbol="square", color=GOLD),
        name="Predicted",
    ))
fig_yield.add_vline(x=2024.5, line_dash="dot", line_color=GRAY, line_width=1.5)
fig_yield.update_layout(
    **LAYOUT_BASE,
    xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
    yaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="%"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    height=380, margin=dict(l=10, r=20, t=40, b=40),
)
st.plotly_chart(fig_yield, use_container_width=True)

# ── SUPPORTING INDICATORS (collapsible) ───────────────────────────────────────
with st.expander("Show supporting indicators — Rent & Home Value"):
    col_a, col_b = st.columns(2)

    with col_a:
        fig_rent = go.Figure(go.Scatter(
            x=hist_agg["year"], y=hist_agg["avg_zori"],
            mode="lines+markers",
            line=dict(color=NAVY, width=2.5),
            marker=dict(size=7, color=NAVY),
        ))
        fig_rent.update_layout(
            **LAYOUT_BASE,
            title="<b>Median Monthly Rent — ZORI ($)</b>",
            xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
            yaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickprefix="$"),
            height=300, margin=dict(l=10, r=20, t=45, b=40),
        )
        st.plotly_chart(fig_rent, use_container_width=True)

    with col_b:
        fig_hv = go.Figure(go.Scatter(
            x=hist_agg["year"], y=hist_agg["avg_zhvi"] / 1000,
            mode="lines+markers",
            line=dict(color="#4472C4", width=2.5),
            marker=dict(size=7, color="#4472C4"),
        ))
        fig_hv.update_layout(
            **LAYOUT_BASE,
            title="<b>Median Home Value — ZHVI ($000s)</b>",
            xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
            yaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="k"),
            height=300, margin=dict(l=10, r=20, t=45, b=40),
        )
        st.plotly_chart(fig_hv, use_container_width=True)

with st.expander("Show supporting indicator — Student Enrollment"):
    st.markdown(
        f'<p style="color:{GRAY};font-size:13px">IPEDS enrollment data is available through '
        f'<strong>2021</strong> in this dataset — figures for 2022–2024 are zero due to a '
        f'reporting lag in the source data and are excluded from the chart.</p>',
        unsafe_allow_html=True,
    )
    enr_data = (
        hist[hist["total_enrollment"] > 0]
        .groupby("year")["total_enrollment"]
        .median()
        .reset_index()
    )
    if len(enr_data) > 0:
        fig_enr = go.Figure(go.Scatter(
            x=enr_data["year"], y=enr_data["total_enrollment"] / 1000,
            mode="lines+markers",
            line=dict(color="#7B4EA0", width=2.5),
            marker=dict(size=7, color="#7B4EA0"),
        ))
        fig_enr.update_layout(
            **LAYOUT_BASE,
            title="<b>Median Student Enrollment (000s) — Available Through 2021</b>",
            xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
            yaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="k"),
            height=300, margin=dict(l=10, r=20, t=45, b=40),
        )
        st.plotly_chart(fig_enr, use_container_width=True)
    else:
        st.info("No enrollment data available for this selection.")
