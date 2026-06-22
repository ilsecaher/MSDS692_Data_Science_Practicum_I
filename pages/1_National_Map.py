import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from app_utils import (
    NAVY, GOLD, GREEN, RED, GRAY, LIGHT, LAYOUT_BASE, NAVY_SCALE,
    load_merged, page_header, section_title, kpi_row,
)

st.set_page_config(page_title="National Map", page_icon="🗺️", layout="wide")
page_header(
    "National Market Map",
    "Average predicted gross rental yield by state · 2025 & 2026",
)

df = load_merged()

# ── Controls ──────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1, 1, 2])
year_col   = c1.radio("Forecast Year", [2025, 2026], horizontal=True)
yield_col  = "yield_2025_pct" if year_col == 2025 else "yield_2026_pct"
conf_sel   = c2.selectbox("Confidence", ["All", "high", "medium", "low"])
state_sel  = c3.selectbox(
    "Drill into a state",
    ["All States"] + sorted(df["state"].unique().tolist()),
)

view = df.copy()
if conf_sel != "All":
    view = view[view["confidence"] == conf_sel]

# ── State choropleth ──────────────────────────────────────────────────────────
state_agg = (
    view.groupby("state")
    .agg(
        avg_yield=(yield_col, "mean"),
        n_counties=("county", "count"),
        best_county=("county", lambda x: view.loc[x.index, "county"].iloc[
            view.loc[x.index, yield_col].argmax()
        ]),
        best_yield=(yield_col, "max"),
    )
    .reset_index()
)

state_agg["hover"] = (
    "<b>" + state_agg["state"] + "</b><br>"
    + "Avg Yield: " + state_agg["avg_yield"].map(lambda v: f"{v:.2f}%") + "<br>"
    + "Counties: " + state_agg["n_counties"].astype(str) + "<br>"
    + "Best county: " + state_agg["best_county"]
    + " (" + state_agg["best_yield"].map(lambda v: f"{v:.2f}%") + ")"
)

fig_map = go.Figure(go.Choropleth(
    locations=state_agg["state"],
    z=state_agg["avg_yield"],
    locationmode="USA-states",
    colorscale=NAVY_SCALE,
    colorbar=dict(title="Avg Yield (%)", ticksuffix="%"),
    text=state_agg["hover"],
    hoverinfo="text",
))
fig_map.update_layout(
    **LAYOUT_BASE,
    geo=dict(scope="usa", showlakes=False, bgcolor="white"),
    title=f"<b>Predicted Rental Yield by State — {year_col}</b>",
    height=460,
    margin=dict(l=0, r=0, t=45, b=0),
)
st.plotly_chart(fig_map, use_container_width=True)

# ── County detail ─────────────────────────────────────────────────────────────
section_title(
    f"County Detail — {'All States' if state_sel == 'All States' else state_sel}"
)

county_view = view if state_sel == "All States" else view[view["state"] == state_sel]
county_view = county_view.sort_values(yield_col, ascending=False).head(30).copy()
county_view["label"] = county_view["county"] + ", " + county_view["state"]

col_map, col_info = st.columns([3, 2])

with col_map:
    t = county_view.sort_values(yield_col)
    fig_bar = go.Figure(go.Bar(
        x=t[yield_col], y=t["label"], orientation="h",
        marker_color=NAVY,
        text=[f"{v:.2f}%" for v in t[yield_col]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Yield: %{x:.2f}%<extra></extra>",
    ))
    fig_bar.update_layout(
        **LAYOUT_BASE,
        title=f"Top Counties — {year_col} Predicted Yield",
        xaxis=dict(title="Predicted Yield (%)", ticksuffix="%",
                   showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=False),
        height=max(380, len(county_view) * 22),
        margin=dict(l=10, r=80, t=45, b=30),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_info:
    st.markdown(
        f'<p style="color:{GRAY};font-size:13px;margin-bottom:10px">'
        "Click a row to see county details.</p>",
        unsafe_allow_html=True,
    )
    disp_cols = {
        "county": "County",
        "state": "State",
        yield_col: f"{year_col} Yield",
        "yield_change_pct": "Δ vs 2024",
        "median_home_value": "Home Value",
        "median_gross_rent": "Rent/mo",
        "total_enrollment": "Enrollment",
        "housing_deficit": "Housing Deficit",
        "enrollment_intensity": "Enrollment Intensity",
    }
    show = county_view[[c for c in disp_cols if c in county_view.columns]].copy()
    show = show.rename(columns=disp_cols)
    if f"{year_col} Yield" in show.columns:
        show[f"{year_col} Yield"] = show[f"{year_col} Yield"].map(lambda v: f"{v:.2f}%")
    if "Δ vs 2024" in show.columns:
        show["Δ vs 2024"] = show["Δ vs 2024"].map(lambda v: f"{v:+.2f}%")
    if "Home Value" in show.columns:
        show["Home Value"] = show["Home Value"].map(lambda v: f"${v:,.0f}" if v == v else "—")
    if "Rent/mo" in show.columns:
        show["Rent/mo"] = show["Rent/mo"].map(lambda v: f"${v:,.0f}" if v == v else "—")
    if "Enrollment" in show.columns:
        show["Enrollment"] = show["Enrollment"].map(lambda v: f"{v:,.0f}" if v == v else "—")
    if "Housing Deficit" in show.columns:
        show["Housing Deficit"] = show["Housing Deficit"].map(
            lambda v: f"{v:,.0f}" if v == v else "—"
        )
    if "Enrollment Intensity" in show.columns:
        show["Enrollment Intensity"] = show["Enrollment Intensity"].map(
            lambda v: f"{v:.3f}" if v == v else "—"
        )
    st.dataframe(show.reset_index(drop=True), use_container_width=True, height=560)
