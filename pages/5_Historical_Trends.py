import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app_utils import NAVY, GOLD, GREEN, RED, GRAY, LIGHT, LAYOUT_BASE, load_master, load_predictions, page_header, section_title

st.set_page_config(page_title="Historical Trends", page_icon="📈", layout="wide")
page_header(
    "Historical Trends",
    "County-level time series 2012–2024 with 2025–2026 predictions",
)

master = load_master()
pred   = load_predictions()

# ── Selectors ─────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
state_opts = ["All States"] + sorted(master["state"].unique().tolist())
state_sel  = c1.selectbox("State", state_opts)

if state_sel == "All States":
    county_opts = ["All Counties (national median)"]
else:
    county_opts = sorted(master[master["state"] == state_sel]["county"].unique().tolist())
county_sel = c2.selectbox("County", county_opts)

# ── Filter historical ─────────────────────────────────────────────────────────
hist = master[master["year"] <= 2024].copy()
if state_sel != "All States":
    hist = hist[hist["state"] == state_sel]
if county_sel != "All Counties (national median)" and county_sel in hist["county"].values:
    hist = hist[hist["county"] == county_sel]

hist_agg = (
    hist.groupby("year")
    .agg(
        gross_rental_yield=("gross_rental_yield", "median"),
        avg_zori=("avg_zori", "median"),
        avg_zhvi=("avg_zhvi", "median"),
        total_enrollment=("total_enrollment", "median"),
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
    pred_view.groupby("year")["predicted_yield"]
    .median()
    .reset_index()
    .rename(columns={"predicted_yield": "gross_rental_yield"})
)

# Bridge point: repeat 2024 actual as start of predicted line
bridge_yield = hist_agg.loc[hist_agg["year"] == 2024, "gross_rental_yield"]
if len(bridge_yield) > 0:
    bridge_row = pd.DataFrame({"year": [2024], "gross_rental_yield": [bridge_yield.values[0]]})
    pred_ext = pd.concat([bridge_row, pred_agg[pred_agg["year"] > 2024]], ignore_index=True)
else:
    pred_ext = pred_agg

section_title("Gross Rental Yield — Actual + Predicted")

def make_trend(hist_col, pred_col=None, title="", y_fmt=".2f", y_suffix="%",
               hist_label="Actual (Median)", pred_label="Predicted"):
    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(
        x=hist_agg["year"], y=hist_agg[hist_col] * (100 if "yield" in hist_col else 1),
        mode="lines+markers",
        line=dict(color=NAVY, width=2.5),
        marker=dict(size=7, color=NAVY),
        name=hist_label,
    ))

    # Predicted extension
    if pred_col is not None and len(pred_ext) > 1:
        fig.add_trace(go.Scatter(
            x=pred_ext["year"],
            y=pred_ext[pred_col] * (100 if "yield" in pred_col else 1),
            mode="lines+markers",
            line=dict(color=GOLD, width=2.5, dash="dash"),
            marker=dict(size=9, symbol="square", color=GOLD),
            name=pred_label,
        ))

    fig.add_vline(x=2024.5, line_dash="dot", line_color=GRAY, line_width=1.5)
    fig.update_layout(
        **LAYOUT_BASE,
        title=f"<b>{title}</b>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix=y_suffix),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        height=320, margin=dict(l=10, r=20, t=55, b=40),
    )
    return fig

col_top1, col_top2 = st.columns(2)
with col_top1:
    st.plotly_chart(
        make_trend("gross_rental_yield", "gross_rental_yield",
                   "Gross Rental Yield (%)"),
        use_container_width=True,
    )
with col_top2:
    # Rent trend
    fig_rent = go.Figure()
    fig_rent.add_trace(go.Scatter(
        x=hist_agg["year"], y=hist_agg["avg_zori"],
        mode="lines+markers",
        line=dict(color=NAVY, width=2.5),
        marker=dict(size=7, color=NAVY),
        name="Median Rent (ZORI)",
    ))
    fig_rent.update_layout(
        **LAYOUT_BASE,
        title="<b>Median Monthly Rent — ZORI ($)</b>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickprefix="$"),
        height=320, margin=dict(l=10, r=20, t=55, b=40),
    )
    st.plotly_chart(fig_rent, use_container_width=True)

col_bot1, col_bot2 = st.columns(2)
with col_bot1:
    fig_hv = go.Figure()
    fig_hv.add_trace(go.Scatter(
        x=hist_agg["year"], y=hist_agg["avg_zhvi"] / 1000,
        mode="lines+markers",
        line=dict(color="#4472C4", width=2.5),
        marker=dict(size=7, color="#4472C4"),
        name="Median Home Value (ZHVI, $000s)",
    ))
    fig_hv.update_layout(
        **LAYOUT_BASE,
        title="<b>Median Home Value — ZHVI ($000s)</b>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="k"),
        height=320, margin=dict(l=10, r=20, t=55, b=40),
    )
    st.plotly_chart(fig_hv, use_container_width=True)

with col_bot2:
    enr_data = hist[hist["total_enrollment"] > 0].groupby("year")["total_enrollment"].median().reset_index()
    if len(enr_data) > 0:
        fig_enr = go.Figure()
        fig_enr.add_trace(go.Scatter(
            x=enr_data["year"], y=enr_data["total_enrollment"] / 1000,
            mode="lines+markers",
            line=dict(color="#7B4EA0", width=2.5),
            marker=dict(size=7, color="#7B4EA0"),
            name="Median Enrollment (000s)",
        ))
        fig_enr.update_layout(
            **LAYOUT_BASE,
            title="<b>Median Student Enrollment (000s)</b>",
            xaxis=dict(showgrid=True, gridcolor="#E5E7EB", tickmode="linear", dtick=2),
            yaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="k"),
            height=320, margin=dict(l=10, r=20, t=55, b=40),
        )
        st.plotly_chart(fig_enr, use_container_width=True)
    else:
        st.info("Enrollment data not available for this selection.")
