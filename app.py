import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="College Town Rental Yield Dashboard",
    page_icon="🏘️",
    layout="wide",
)

# ── Brand colors ──────────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
GOLD   = "#F2B705"
RED    = "#C00000"
LIGHT  = "#EAF0FB"   # light blue-gray for backgrounds
GRAY   = "#6B7280"

FONT = dict(family="Arial, sans-serif")

LAYOUT_BASE = dict(
    font=FONT,
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font=dict(size=16, color=NAVY, family="Arial, sans-serif"),
    xaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False),
    margin=dict(l=10, r=70, t=50, b=40),
)

CAT_COLORS = {
    "Demographic (ACS)": NAVY,
    "College (IPEDS)":   GOLD,
    "Market (Zillow)":   "#4472C4",
    "Macro (FRED)":      RED,
    "Engineered":        "#7B4EA0",
    "Other":             GRAY,
}

MODEL_LBL = "Random Forest"

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_predictions():
    df = pd.read_csv("predictions_2025_2026.csv")
    for col in ["predicted_yield", "yield_2024", "yield_change"]:
        df[col + "_pct"] = df[col] * 100
    return df

@st.cache_data
def load_historical():
    df = pd.read_csv("MasterCollegeTowns.csv")
    df = df[df["year"].between(2012, 2024)]
    hist = (
        df.groupby("year")["gross_rental_yield"]
        .agg(median="median", q25=lambda x: x.quantile(0.25), q75=lambda x: x.quantile(0.75))
        .reset_index()
    )
    hist["median_pct"] = hist["median"] * 100
    hist["q25_pct"]    = hist["q25"] * 100
    hist["q75_pct"]    = hist["q75"] * 100
    # Raw county-level values for 2024 box plot
    raw_2024 = df[df["year"] == 2024]["gross_rental_yield"].dropna() * 100
    return hist, raw_2024

df        = load_predictions()
hist, raw_2024 = load_historical()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:{NAVY};padding:20px 28px 14px;border-radius:10px;margin-bottom:18px">
      <h1 style="color:white;margin:0;font-size:26px;font-family:Arial,sans-serif">
        College Town Rental Yield Dashboard
      </h1>
      <p style="color:{GOLD};margin:4px 0 0;font-size:14px;font-family:Arial,sans-serif">
        Predicted gross rental yields · Random Forest · 2025–2026 &nbsp;|&nbsp;
        MSDS 692 — Data Science Practicum I · Ilse Severance
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<h2 style="color:{NAVY};font-family:Arial,sans-serif;margin-top:0">Filters</h2>',
        unsafe_allow_html=True,
    )

    state_opts = ["All States"] + sorted(df["state"].unique().tolist())
    state_sel  = st.selectbox("State", state_opts)

    county_opts = (
        ["All Counties"] if state_sel == "All States"
        else ["All Counties"] + sorted(df[df["state"] == state_sel]["county"].unique().tolist())
    )
    county_sel = st.selectbox("County", county_opts)

    year_sel = st.radio("Prediction Year", [2025, 2026])

    conf_opts = ["All"] + sorted(df["confidence"].dropna().unique().tolist())
    conf_sel  = st.selectbox("Confidence", conf_opts)

    top_n = st.slider("Top N Counties", min_value=10, max_value=50, value=20, step=5)

# ── Filter predictions ────────────────────────────────────────────────────────
filtered = df[df["year"] == year_sel].copy()
if state_sel  != "All States":   filtered = filtered[filtered["state"]  == state_sel]
if county_sel != "All Counties": filtered = filtered[filtered["county"] == county_sel]
if conf_sel   != "All":          filtered = filtered[filtered["confidence"] == conf_sel]

if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

filtered["label"] = filtered["county"] + ", " + filtered["state"]
top = filtered.nlargest(top_n, "predicted_yield").copy()
top["label"] = top["county"] + ", " + top["state"]

# ── KPI row ───────────────────────────────────────────────────────────────────
avg_yield     = filtered["predicted_yield_pct"].mean()
avg_change    = filtered["yield_change_pct"].mean()
n_counties    = len(filtered)
n_states      = filtered["state"].nunique()
pct_improving = (filtered["yield_change_pct"] > 0).mean() * 100
chg_sign      = "+" if avg_change >= 0 else ""

st.markdown(
    f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px">
      <div style="flex:1;min-width:140px;background:{LIGHT};border-left:4px solid {NAVY};
                  border-radius:8px;padding:14px 16px">
        <div style="font-size:24px;font-weight:700;color:{NAVY}">{avg_yield:.2f}%</div>
        <div style="font-size:12px;color:{GRAY};margin-top:2px">Avg Predicted Yield</div>
      </div>
      <div style="flex:1;min-width:140px;background:{LIGHT};border-left:4px solid {'#1A7238' if avg_change>=0 else RED};
                  border-radius:8px;padding:14px 16px">
        <div style="font-size:24px;font-weight:700;color:{'#1A7238' if avg_change>=0 else RED}">{chg_sign}{avg_change:.2f}%</div>
        <div style="font-size:12px;color:{GRAY};margin-top:2px">Avg Change vs 2024</div>
      </div>
      <div style="flex:1;min-width:140px;background:{LIGHT};border-left:4px solid {GOLD};
                  border-radius:8px;padding:14px 16px">
        <div style="font-size:24px;font-weight:700;color:{NAVY}">{n_states}</div>
        <div style="font-size:12px;color:{GRAY};margin-top:2px">States</div>
      </div>
      <div style="flex:1;min-width:140px;background:{LIGHT};border-left:4px solid {GOLD};
                  border-radius:8px;padding:14px 16px">
        <div style="font-size:24px;font-weight:700;color:{NAVY}">{n_counties:,}</div>
        <div style="font-size:12px;color:{GRAY};margin-top:2px">Counties</div>
      </div>
      <div style="flex:1;min-width:140px;background:{LIGHT};border-left:4px solid {'#1A7238' if pct_improving>=50 else RED};
                  border-radius:8px;padding:14px 16px">
        <div style="font-size:24px;font-weight:700;color:{NAVY}">{pct_improving:.0f}%</div>
        <div style="font-size:12px;color:{GRAY};margin-top:2px">Counties Improving</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Section: Historical Overview ──────────────────────────────────────────────
st.markdown(
    f'<h2 style="color:{NAVY};font-family:Arial,sans-serif;border-bottom:2px solid {GOLD};'
    f'padding-bottom:6px;margin-top:8px">Historical Overview</h2>',
    unsafe_allow_html=True,
)

col_a, col_b = st.columns(2)

# Chart A: Median Yield Trend (Actual + Predicted)
pred_medians = (
    df.groupby("year")["predicted_yield_pct"].median().reset_index()
)
bridge_year  = 2024
bridge_value = hist.loc[hist["year"] == bridge_year, "median_pct"].values[0]
trend_pred_x = [bridge_year] + pred_medians["year"].tolist()
trend_pred_y = [bridge_value] + pred_medians["predicted_yield_pct"].tolist()

trend_fig = go.Figure()

# IQR band
trend_fig.add_trace(go.Scatter(
    x=hist["year"].tolist() + hist["year"].tolist()[::-1],
    y=hist["q75_pct"].tolist() + hist["q25_pct"].tolist()[::-1],
    fill="toself", fillcolor=f"rgba(27,58,107,0.10)",
    line=dict(width=0), showlegend=True, name="IQR (25–75%)",
    hoverinfo="skip",
))

# Actual line
trend_fig.add_trace(go.Scatter(
    x=hist["year"], y=hist["median_pct"],
    mode="lines+markers",
    line=dict(color=NAVY, width=2.5),
    marker=dict(size=7, color=NAVY),
    name="Actual",
))

# Predicted line
trend_fig.add_trace(go.Scatter(
    x=trend_pred_x, y=trend_pred_y,
    mode="lines+markers",
    line=dict(color=GOLD, width=2.5, dash="dash"),
    marker=dict(size=9, symbol="square", color=GOLD),
    name="Predicted",
))

trend_fig.add_vline(
    x=2024.5, line_dash="dot", line_color=GRAY, line_width=1.5,
)
trend_fig.update_layout(
    **LAYOUT_BASE,
    title="<b>Median Yield Trend: Actual + Predicted</b>",
    xaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False,
               tickmode="linear", dtick=2),
    yaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False,
               tickformat=".1%", tickvals=[v/100 for v in [4.5,5.0,5.5,6.0,6.5]],
               ticktext=["4.5%","5.0%","5.5%","6.0%","6.5%"]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    height=380, margin=dict(l=10, r=20, t=60, b=40),
)
trend_fig.update_yaxes(tickformat=".1f", ticksuffix="%")

with col_a:
    st.plotly_chart(trend_fig, use_container_width=True)

# Chart B: Box Plot Comparison
raw_2025 = df[df["year"] == 2025]["predicted_yield_pct"].dropna()
raw_2026 = df[df["year"] == 2026]["predicted_yield_pct"].dropna()

box_fig = go.Figure()
box_fig.add_trace(go.Box(
    y=raw_2024, name="2024 Actual",
    marker_color=NAVY, line_color=NAVY,
    fillcolor=f"rgba(27,58,107,0.18)",
    medianline=dict(color=GOLD, width=3),
    boxpoints=False,
))
box_fig.add_trace(go.Box(
    y=raw_2025, name="2025 Predicted",
    marker_color=NAVY, line_color=NAVY,
    fillcolor=f"rgba(27,58,107,0.18)",
    medianline=dict(color=GOLD, width=3),
    boxpoints=False,
))
box_fig.add_trace(go.Box(
    y=raw_2026, name="2026 Predicted",
    marker_color=NAVY, line_color=NAVY,
    fillcolor=f"rgba(27,58,107,0.18)",
    medianline=dict(color=GOLD, width=3),
    boxpoints=False,
))
box_fig.update_layout(
    **LAYOUT_BASE,
    title="<b>Yield Box Plot Comparison</b>",
    yaxis_title="Gross Rental Yield (%)",
    yaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False, ticksuffix="%"),
    showlegend=False,
    height=380, margin=dict(l=10, r=20, t=60, b=40),
)

with col_b:
    st.plotly_chart(box_fig, use_container_width=True)

# ── Section: Interactive Dashboard ───────────────────────────────────────────
st.markdown(
    f'<h2 style="color:{NAVY};font-family:Arial,sans-serif;border-bottom:2px solid {GOLD};'
    f'padding-bottom:6px;margin-top:8px">Interactive Dashboard — {year_sel}</h2>',
    unsafe_allow_html=True,
)

# Feature importance
fi_data = pd.DataFrame({
    "feature":    ["median_home_value", "median_household_income", "median_gross_rent",
                   "zori_is_real", "vacancy_rate"],
    "importance": [0.3203, 0.0685, 0.0623, 0.0574, 0.0485],
    "category":   ["Demographic (ACS)", "Demographic (ACS)", "Demographic (ACS)",
                   "Other", "Demographic (ACS)"],
})
fi_sorted  = fi_data.sort_values("importance")
cat_totals = fi_data.groupby("category")["importance"].sum().reset_index()

fi_fig = make_subplots(
    rows=1, cols=2, column_widths=[0.58, 0.42],
    specs=[[{"type": "xy"}, {"type": "domain"}]],
    subplot_titles=["Top 5 Feature Importances (Random Forest)",
                    "Importance by Data Source"],
)
fi_fig.add_trace(go.Bar(
    x=fi_sorted["importance"], y=fi_sorted["feature"], orientation="h",
    marker_color=fi_sorted["category"].map(CAT_COLORS).fillna(GRAY).tolist(),
    text=[f"{v:.4f}" for v in fi_sorted["importance"]],
    textposition="outside", showlegend=False,
    hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
), row=1, col=1)
fi_fig.add_trace(go.Pie(
    labels=cat_totals["category"], values=cat_totals["importance"],
    hole=0.45,
    marker_colors=cat_totals["category"].map(CAT_COLORS).fillna(GRAY).tolist(),
    textinfo="percent", textfont_size=12, pull=[0.05] * len(cat_totals),
    hovertemplate="<b>%{label}</b><br>Share: %{percent}<extra></extra>",
), row=1, col=2)
fi_fig.update_layout(
    font=FONT,
    plot_bgcolor="white", paper_bgcolor="white",
    height=310, margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="top", y=-0.1,
                xanchor="center", x=0.75, font=dict(size=11)),
)
fi_fig.update_xaxes(showgrid=True, gridcolor="#E5E7EB", row=1, col=1)
fi_fig.update_yaxes(showgrid=False, row=1, col=1)
st.plotly_chart(fi_fig, use_container_width=True)

# Chart 1: Top N counties
t1 = top.sort_values("predicted_yield")
colors_n = [NAVY] * len(t1)
fig1 = go.Figure(go.Bar(
    x=t1["predicted_yield_pct"], y=t1["label"], orientation="h",
    marker_color=colors_n,
    text=[f"{v:.2f}%" for v in t1["predicted_yield_pct"]],
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>Predicted Yield: %{x:.2f}%<extra></extra>",
))
fig1.update_layout(
    **LAYOUT_BASE,
    title=f"<b>Top {top_n} Counties — Predicted Rental Yield ({year_sel})</b>",
    xaxis_title="Predicted Yield (%)", yaxis_title="",
    height=max(420, top_n * 22),
    xaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False, ticksuffix="%"),
    yaxis=dict(showgrid=False, zeroline=False),
)
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Yield change
t2 = top.sort_values("yield_change")
fig2 = go.Figure(go.Bar(
    x=t2["yield_change_pct"], y=t2["label"], orientation="h",
    marker_color=["#C00000" if v < 0 else "#1A7238" for v in t2["yield_change_pct"]],
    text=[f"{v:+.2f}%" for v in t2["yield_change_pct"]], textposition="outside",
    hovertemplate="<b>%{y}</b><br>Change: %{x:+.2f}%<extra></extra>",
))
fig2.update_layout(
    **LAYOUT_BASE,
    title=f"<b>Yield Change vs 2024 — Top {top_n} Counties ({year_sel})</b>",
    xaxis_title="Change in Yield (%)", yaxis_title="",
    height=max(420, top_n * 22),
    xaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False, ticksuffix="%"),
    yaxis=dict(showgrid=False, zeroline=False),
)
fig2.add_vline(x=0, line_dash="dash", line_color=GRAY, line_width=1)
st.plotly_chart(fig2, use_container_width=True)

# Chart 3: State avg
state_avg = (
    filtered.groupby("state")
    .agg(avg_yield=("predicted_yield_pct", "mean"),
         avg_change=("yield_change_pct", "mean"),
         n_counties=("county", "count"))
    .reset_index()
    .sort_values("avg_yield", ascending=False)
)
fig3 = go.Figure(go.Bar(
    x=state_avg["state"], y=state_avg["avg_yield"],
    marker_color=NAVY,
    text=[f"{v:.2f}%" for v in state_avg["avg_yield"]],
    textposition="outside",
    customdata=state_avg[["n_counties", "avg_change"]].values,
    hovertemplate="<b>%{x}</b><br>Avg Yield: %{y:.2f}%<br>Counties: %{customdata[0]}<br>Avg Δ: %{customdata[1]:.2f}%<extra></extra>",
))
fig3.update_layout(
    **LAYOUT_BASE,
    title=f"<b>Average Predicted Yield by State ({year_sel})</b>",
    xaxis_title="State", yaxis_title="Avg Yield (%)",
    height=450,
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False, ticksuffix="%"),
    margin=dict(l=10, r=10, t=50, b=40),
)
st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Scatter
fig4 = go.Figure(go.Scatter(
    x=filtered["yield_2024_pct"], y=filtered["predicted_yield_pct"],
    mode="markers",
    marker=dict(color=NAVY, size=7, opacity=0.65,
                line=dict(width=0.5, color="white")),
    customdata=filtered[["county", "state", "confidence"]].values,
    hovertemplate=(
        "<b>%{customdata[0]}, %{customdata[1]}</b><br>"
        "2024 Actual: %{x:.2f}%<br>"
        f"{year_sel} Predicted: %{{y:.2f}}%<br>"
        "Confidence: %{customdata[2]}<extra></extra>"
    ),
))
mn = min(filtered["yield_2024_pct"].min(), filtered["predicted_yield_pct"].min())
mx = max(filtered["yield_2024_pct"].max(), filtered["predicted_yield_pct"].max())
fig4.add_shape(type="line", x0=mn, x1=mx, y0=mn, y1=mx,
               line=dict(dash="dash", color=GRAY, width=1.5))
fig4.update_layout(
    **LAYOUT_BASE,
    title=f"<b>2024 Actual vs {year_sel} Predicted Yield</b>",
    xaxis_title="2024 Actual Yield (%)",
    yaxis_title=f"{year_sel} Predicted Yield (%)",
    height=480,
    xaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False, ticksuffix="%"),
    yaxis=dict(showgrid=True, gridcolor="#E5E7EB", zeroline=False, ticksuffix="%"),
    margin=dict(l=10, r=10, t=50, b=40),
)
st.plotly_chart(fig4, use_container_width=True)
