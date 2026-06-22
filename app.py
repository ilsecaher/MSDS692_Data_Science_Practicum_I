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

@st.cache_data
def load_data():
    df = pd.read_csv("predictions_2025_2026.csv")
    for col in ["predicted_yield", "yield_2024", "yield_change"]:
        df[col + "_pct"] = df[col] * 100
    return df

df = load_data()

# ── Feature importance (static) ───────────────────────────────────────────────
CAT_COLORS = {
    "Demographic (ACS)": "#2ca02c",
    "College (IPEDS)":   "#ff7f0e",
    "Market (Zillow)":   "#1f77b4",
    "Macro (FRED)":      "#d62728",
    "Engineered":        "#9467bd",
    "Other":             "#7f7f7f",
}
fi_data = pd.DataFrame({
    "feature":    ["median_home_value", "median_household_income", "median_gross_rent",
                   "zori_is_real", "vacancy_rate"],
    "importance": [0.3203, 0.0685, 0.0623, 0.0574, 0.0485],
    "category":   ["Demographic (ACS)", "Demographic (ACS)", "Demographic (ACS)",
                   "Other", "Demographic (ACS)"],
})

MODEL_LBL = "Random Forest"

# ── Header ────────────────────────────────────────────────────────────────────
st.title("College Town Rental Yield Dashboard")
st.markdown(
    "Predicted gross rental yields (**Random Forest**) | 2025–2026  \n"
    "MSDS 692 — Data Science Practicum I | Ilse Severance"
)

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    state_opts = ["All States"] + sorted(df["state"].unique().tolist())
    state_sel = st.selectbox("State", state_opts)

    if state_sel == "All States":
        county_opts = ["All Counties"]
    else:
        county_opts = ["All Counties"] + sorted(
            df[df["state"] == state_sel]["county"].unique().tolist()
        )
    county_sel = st.selectbox("County", county_opts)

    year_sel = st.radio("Year", [2025, 2026])

    conf_opts = ["All"] + sorted(df["confidence"].dropna().unique().tolist())
    conf_sel = st.selectbox("Confidence", conf_opts)

    top_n = st.slider("Top N Counties", min_value=10, max_value=50, value=20, step=5)

# ── Filter data ───────────────────────────────────────────────────────────────
filtered = df[df["year"] == year_sel].copy()
if state_sel != "All States":
    filtered = filtered[filtered["state"] == state_sel]
if county_sel != "All Counties":
    filtered = filtered[filtered["county"] == county_sel]
if conf_sel != "All":
    filtered = filtered[filtered["confidence"] == conf_sel]

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

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg Predicted Yield", f"{avg_yield:.2f}%")
k2.metric("Avg Change vs 2024",  f"{avg_change:+.2f}%", delta_color="normal")
k3.metric("States",              n_states)
k4.metric("Counties",            f"{n_counties:,}")
k5.metric("Counties Improving",  f"{pct_improving:.0f}%")

st.divider()

# ── Feature importance ────────────────────────────────────────────────────────
fi_sorted  = fi_data.sort_values("importance")
cat_totals = fi_data.groupby("category")["importance"].sum().reset_index()

fi_fig = make_subplots(
    rows=1, cols=2, column_widths=[0.58, 0.42],
    specs=[[{"type": "xy"}, {"type": "domain"}]],
    subplot_titles=["Top 5 Feature Importances", "Importance by Data Source"],
)
fi_fig.add_trace(go.Bar(
    x=fi_sorted["importance"], y=fi_sorted["feature"], orientation="h",
    marker_color=fi_sorted["category"].map(CAT_COLORS).fillna("gray").tolist(),
    text=[f"{v:.4f}" for v in fi_sorted["importance"]],
    textposition="outside", showlegend=False,
    hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
), row=1, col=1)
fi_fig.add_trace(go.Pie(
    labels=cat_totals["category"], values=cat_totals["importance"],
    hole=0.45,
    marker_colors=cat_totals["category"].map(CAT_COLORS).fillna("gray").tolist(),
    textinfo="percent", textfont_size=12, pull=[0.05] * len(cat_totals),
    hovertemplate="<b>%{label}</b><br>Share: %{percent}<extra></extra>",
), row=1, col=2)
fi_fig.update_layout(
    height=310, margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.75, font=dict(size=11)),
)
st.plotly_chart(fi_fig, use_container_width=True)

# ── Chart 1: Top N counties ───────────────────────────────────────────────────
t1 = top.sort_values("predicted_yield")
fig1 = px.bar(
    t1, x="predicted_yield_pct", y="label", orientation="h",
    title=f"Top {top_n} Counties — Predicted Rental Yield ({year_sel}) [{MODEL_LBL}]",
    labels={"predicted_yield_pct": "Predicted Yield (%)", "label": ""},
    color="predicted_yield_pct", color_continuous_scale="Blues",
    text=t1["predicted_yield_pct"].map(lambda v: f"{v:.2f}%"),
)
fig1.update_traces(textposition="outside")
fig1.update_layout(height=max(400, top_n * 22), coloraxis_showscale=False,
                   margin=dict(l=10, r=70, t=45, b=30))
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Yield change ─────────────────────────────────────────────────────
t2 = top.sort_values("yield_change")
fig2 = go.Figure(go.Bar(
    x=t2["yield_change_pct"], y=t2["label"], orientation="h",
    marker_color=["#dc3545" if v < 0 else "#28a745" for v in t2["yield_change_pct"]],
    text=[f"{v:+.2f}%" for v in t2["yield_change_pct"]], textposition="outside",
))
fig2.update_layout(
    title=f"Yield Change vs 2024 — Top {top_n} Counties ({year_sel}) [{MODEL_LBL}]",
    xaxis_title="Change in Yield (%)", yaxis_title="",
    height=max(400, top_n * 22), margin=dict(l=10, r=70, t=45, b=30),
)
fig2.add_vline(x=0, line_dash="dash", line_color="gray", line_width=1)
st.plotly_chart(fig2, use_container_width=True)

# ── Chart 3: State avg ────────────────────────────────────────────────────────
state_avg = (
    filtered.groupby("state")
    .agg(avg_yield=("predicted_yield_pct", "mean"),
         avg_change=("yield_change_pct", "mean"),
         n_counties=("county", "count"))
    .reset_index()
    .sort_values("avg_yield", ascending=False)
)
fig3 = px.bar(
    state_avg, x="state", y="avg_yield",
    color="avg_yield", color_continuous_scale="Blues",
    title=f"Average Predicted Yield by State ({year_sel}) [{MODEL_LBL}]",
    labels={"avg_yield": "Avg Yield (%)", "state": "State", "avg_change": "Avg Δ (%)"},
    text=state_avg["avg_yield"].map(lambda v: f"{v:.2f}%"),
    hover_data={"n_counties": True, "avg_change": ":.2f"},
)
fig3.update_traces(textposition="outside")
fig3.update_layout(height=450, margin=dict(l=10, r=10, t=45, b=40))
st.plotly_chart(fig3, use_container_width=True)

# ── Chart 4: Scatter ──────────────────────────────────────────────────────────
fig4 = px.scatter(
    filtered, x="yield_2024_pct", y="predicted_yield_pct",
    color="predicted_yield_pct", color_continuous_scale="Blues",
    hover_data={"state": True, "county": True, "confidence": True},
    title=f"2024 Actual vs {year_sel} Predicted Yield [{MODEL_LBL}]",
    labels={"yield_2024_pct": "2024 Actual Yield (%)",
            "predicted_yield_pct": f"{year_sel} Predicted Yield (%)"},
    opacity=0.65,
)
mn = min(filtered["yield_2024_pct"].min(), filtered["predicted_yield_pct"].min())
mx = max(filtered["yield_2024_pct"].max(), filtered["predicted_yield_pct"].max())
fig4.add_shape(type="line", x0=mn, x1=mx, y0=mn, y1=mx,
               line=dict(dash="dash", color="gray", width=1))
fig4.update_layout(height=460, margin=dict(l=10, r=10, t=45, b=40))
st.plotly_chart(fig4, use_container_width=True)
