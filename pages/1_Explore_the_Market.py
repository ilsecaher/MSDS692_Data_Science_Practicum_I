import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app_utils import (
    NAVY, GOLD, GRAY, LIGHT, LAYOUT_BASE, NAVY_SCALE,
    load_merged, page_header, section_title,
)

st.set_page_config(page_title="Explore the Market", page_icon="🗺️", layout="wide")
page_header(
    "Explore the Market",
    "National overview by state · drill into any county · filter and download",
)

df = load_merged()

tab_map, tab_explorer = st.tabs(["🗺️ Map View", "🔍 County Explorer"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MAP VIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab_map:
    c1, c2, c3 = st.columns([1, 1, 2])
    year_sel  = c1.radio("Forecast Year", [2025, 2026], horizontal=True, key="map_year")
    conf_sel  = c2.selectbox("Confidence", ["All", "high", "medium", "low"], key="map_conf")
    state_sel = c3.selectbox(
        "Drill into a state",
        ["All States"] + sorted(df["state"].unique().tolist()),
        key="map_state",
    )

    yield_col = "yield_2025_pct" if year_sel == 2025 else "yield_2026_pct"
    view = df.copy()
    if conf_sel != "All":
        view = view[view["confidence"] == conf_sel]

    # State choropleth
    state_agg = (
        view.groupby("state")
        .agg(
            avg_yield=(yield_col, "mean"),
            n_counties=("county", "count"),
            best_county=("county", lambda x: view.loc[x.index]
                         .nlargest(1, yield_col)["county"].values[0]),
            best_yield=(yield_col, "max"),
        )
        .reset_index()
    )
    state_agg["hover"] = (
        "<b>" + state_agg["state"] + "</b><br>"
        + "Avg Yield: " + state_agg["avg_yield"].map(lambda v: f"{v:.2f}%") + "<br>"
        + "Counties: " + state_agg["n_counties"].astype(str) + "<br>"
        + "Best: " + state_agg["best_county"]
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
        title=f"<b>Average Predicted Rental Yield by State — {year_sel}</b>",
        height=440,
        margin=dict(l=0, r=0, t=45, b=0),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.caption("Map shows state averages. Select a state above or switch to County Explorer for county-level filtering.")

    # County bar chart (top 20 nationally or all for selected state)
    county_view = (
        view if state_sel == "All States"
        else view[view["state"] == state_sel]
    )
    county_view = county_view.nlargest(25, yield_col).copy()
    county_view["label"] = county_view["county"] + ", " + county_view["state"]
    t = county_view.sort_values(yield_col)

    fig_bar = go.Figure(go.Bar(
        x=t[yield_col], y=t["label"], orientation="h",
        marker_color=NAVY,
        text=[f"{v:.2f}%" for v in t[yield_col]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Yield: %{x:.2f}%<extra></extra>",
    ))
    title_sfx = "All States" if state_sel == "All States" else state_sel
    fig_bar.update_layout(
        **LAYOUT_BASE,
        title=f"<b>Top Counties — {year_sel} Predicted Yield ({title_sfx})</b>",
        xaxis=dict(title="Predicted Yield (%)", ticksuffix="%",
                   showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=False),
        height=max(400, len(t) * 22),
        margin=dict(l=10, r=80, t=45, b=30),
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COUNTY EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    f1, f2, f3, f4 = st.columns(4)

    year_ex   = f1.radio("Forecast Year", [2025, 2026], horizontal=True, key="ex_year")
    yield_ex  = "yield_2025_pct" if year_ex == 2025 else "yield_2026_pct"

    state_ex  = f2.selectbox(
        "State", ["All States"] + sorted(df["state"].unique().tolist()), key="ex_state"
    )
    conf_ex   = f3.multiselect(
        "Confidence", ["high", "medium", "low"],
        default=["high", "medium", "low"], key="ex_conf"
    )
    deficit_only = f4.checkbox("Housing deficit only")

    f5, f6 = st.columns(2)
    ymin, ymax = float(df[yield_ex].min()), float(df[yield_ex].max())
    yield_range = f5.slider("Yield range (%)", ymin, ymax, (ymin, ymax),
                             step=0.1, format="%.1f", key="ex_yield")

    hv_min = float(df["median_home_value"].dropna().min())
    hv_max = float(df["median_home_value"].dropna().max())
    hv_range = f6.slider("Home Value ($)", hv_min, hv_max, (hv_min, hv_max),
                          step=10000.0, format="%.0f", key="ex_hv")

    # Apply filters
    ex = df.copy()
    if state_ex != "All States":
        ex = ex[ex["state"] == state_ex]
    if conf_ex:
        ex = ex[ex["confidence"].isin(conf_ex)]
    ex = ex[
        ex[yield_ex].between(yield_range[0], yield_range[1]) &
        ex["median_home_value"].between(hv_range[0], hv_range[1])
    ]
    if deficit_only and "housing_deficit" in ex.columns:
        ex = ex[ex["housing_deficit"] > 0]
    ex = ex.sort_values(yield_ex, ascending=False).reset_index(drop=True)

    n   = len(ex)
    avg = ex[yield_ex].mean() if n > 0 else 0
    top = ex.iloc[0]["county"] + ", " + ex.iloc[0]["state"] if n > 0 else "—"

    k1, k2, k3 = st.columns(3)
    for col, lbl, val in [(k1, "Counties Shown", str(n)),
                           (k2, "Avg Predicted Yield", f"{avg:.2f}%"),
                           (k3, "Top County", top)]:
        col.markdown(
            f'<div style="background:{LIGHT};border-left:4px solid {NAVY};border-radius:8px;'
            f'padding:10px 14px;margin:8px 0"><div style="font-size:20px;font-weight:700;color:{NAVY}">{val}</div>'
            f'<div style="font-size:11px;color:{GRAY}">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    if n == 0:
        st.warning("No counties match the current filters.")
        st.stop()

    DISPLAY = {
        "county": "County", "state": "State",
        yield_ex: f"{year_ex} Yield", "yield_change_pct": "Δ vs 2024",
        "confidence": "Confidence",
        "median_home_value": "Home Value", "median_gross_rent": "Rent/mo",
        "median_household_income": "Median Income",
        "total_enrollment": "Enrollment", "housing_deficit": "Housing Deficit",
        "enrollment_intensity": "Enroll. Intensity", "vacancy_rate": "Vacancy Rate",
    }
    out = ex[[c for c in DISPLAY if c in ex.columns]].rename(columns=DISPLAY).copy()

    def fmt(col, fn):
        if col in out.columns:
            out[col] = out[col].map(lambda v: fn(v) if pd.notna(v) else "—")

    fmt(f"{year_ex} Yield",    lambda v: f"{v:.2f}%")
    fmt("Δ vs 2024",           lambda v: f"{v:+.2f}%")
    fmt("Home Value",          lambda v: f"${v:,.0f}")
    fmt("Rent/mo",             lambda v: f"${v:,.0f}")
    fmt("Median Income",       lambda v: f"${v:,.0f}")
    fmt("Enrollment",          lambda v: f"{v:,.0f}")
    fmt("Housing Deficit",     lambda v: f"{v:,.0f}")
    fmt("Enroll. Intensity",   lambda v: f"{v:.3f}")
    fmt("Vacancy Rate",        lambda v: f"{v:.1%}")

    st.dataframe(out, use_container_width=True, height=500)
    st.download_button(
        "Download CSV",
        ex[[c for c in DISPLAY if c in ex.columns]].to_csv(index=False),
        file_name=f"college_towns_{year_ex}.csv",
        mime="text/csv",
    )
