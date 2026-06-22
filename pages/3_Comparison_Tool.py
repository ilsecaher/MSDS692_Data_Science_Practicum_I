import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app_utils import NAVY, GOLD, GREEN, GRAY, LIGHT, LAYOUT_BASE, load_merged, page_header, section_title

st.set_page_config(page_title="Comparison Tool", page_icon="⚖️", layout="wide")
page_header(
    "College Town Comparison Tool",
    "Select 2–5 counties to compare side-by-side across key investment metrics",
)

df = load_merged()
df["label"] = df["county"] + ", " + df["state"]

all_labels = sorted(df["label"].dropna().unique().tolist())
defaults = [d for d in ["Weld, CO", "Larimer, CO", "Brazos, TX", "Cache, UT"] if d in all_labels][:4]

selected = st.multiselect("Select counties to compare (2–5)", all_labels, default=defaults, max_selections=5)

if len(selected) < 2:
    st.info("Select at least 2 counties to compare.")
    st.stop()

view = df[df["label"].isin(selected)].copy()

# ── Metrics table ─────────────────────────────────────────────────────────────
section_title("Metrics Comparison")

METRICS = [
    ("2025 Predicted Yield",    "yield_2025_pct",          lambda v: f"{v:.2f}%"),
    ("Change vs 2024",          "yield_change_pct",        lambda v: f"{v:+.2f}%"),
    ("2024 Actual Yield",       "yield_2024_pct",          lambda v: f"{v:.2f}%"),
    ("Median Home Value",       "median_home_value",       lambda v: f"${v:,.0f}"),
    ("Median Monthly Rent",     "median_gross_rent",       lambda v: f"${v:,.0f}"),
    ("Median HH Income",        "median_household_income", lambda v: f"${v:,.0f}"),
    ("Vacancy Rate",            "vacancy_rate",            lambda v: f"{v:.1%}"),
    ("Total Enrollment",        "total_enrollment",        lambda v: f"{v:,.0f}"),
    ("Housing Capacity",        "total_housing_cap",       lambda v: f"{v:,.0f}"),
    ("Housing Deficit",         "housing_deficit",         lambda v: f"{v:,.0f}"),
    ("Enrollment Intensity",    "enrollment_intensity",    lambda v: f"{v:.3f}"),
    ("% Bachelor+",             "pct_bachelor_plus",       lambda v: f"{v:.1%}"),
    ("Confidence",              "confidence",              lambda v: str(v)),
]

table_rows = {}
for label, col, fmt in METRICS:
    if col in view.columns:
        table_rows[label] = {
            row["label"]: fmt(row[col]) if pd.notna(row[col]) else "—"
            for _, row in view.iterrows()
        }

tbl = pd.DataFrame(table_rows).T
tbl.columns.name = None
tbl.index.name = "Metric"
st.dataframe(tbl, use_container_width=True)

# ── 4 bar charts ──────────────────────────────────────────────────────────────
section_title("Visual Comparison")

CHART_METRICS = [
    ("2025 Predicted Yield (%)",  "yield_2025_pct",    GOLD,      1),
    ("Yield Change vs 2024 (%)",  "yield_change_pct",  GREEN,     1),
    ("Median Home Value ($000s)", "median_home_value", "#4472C4", 1000),
    ("Housing Deficit (students)","housing_deficit",   "#7B4EA0", 1),
]

cols = st.columns(2)
for i, (title, col, color, scale) in enumerate(CHART_METRICS):
    if col not in view.columns:
        continue
    sub = view[["label", col]].dropna(subset=[col]).copy()
    if len(sub) == 0:
        continue
    values = sub[col] / scale
    fig = go.Figure(go.Bar(
        x=sub["label"], y=values,
        marker_color=[color] * len(sub),
        text=[f"{v:,.1f}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=f"<b>{title}</b>",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#E5E7EB"),
        height=300, margin=dict(l=10, r=10, t=45, b=60),
        showlegend=False,
    )
    with cols[i % 2]:
        st.plotly_chart(fig, use_container_width=True)

