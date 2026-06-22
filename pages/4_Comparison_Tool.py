import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import NAVY, GOLD, GREEN, RED, GRAY, LIGHT, LAYOUT_BASE, load_merged, page_header, section_title

st.set_page_config(page_title="Comparison Tool", page_icon="⚖️", layout="wide")
page_header(
    "College Town Comparison Tool",
    "Select 2–5 counties to compare side-by-side across key investment metrics",
)

df = load_merged()
df["label"] = df["county"] + ", " + df["state"]

# ── County selector ───────────────────────────────────────────────────────────
all_labels = sorted(df["label"].dropna().unique().tolist())
defaults = ["Weld, CO", "Larimer, CO", "Brazos, TX", "Cache, UT"]
defaults = [d for d in defaults if d in all_labels][:4]

selected = st.multiselect(
    "Select counties to compare (2–5)",
    all_labels,
    default=defaults,
    max_selections=5,
)

if len(selected) < 2:
    st.info("Select at least 2 counties to compare.")
    st.stop()

view = df[df["label"].isin(selected)].copy()

# ── Metrics table ─────────────────────────────────────────────────────────────
section_title("Metrics Comparison")

METRICS = [
    ("2025 Predicted Yield",    "yield_2025_pct",        lambda v: f"{v:.2f}%"),
    ("2026 Predicted Yield",    "yield_2026_pct",        lambda v: f"{v:.2f}%"),
    ("Change vs 2024",          "yield_change_pct",      lambda v: f"{v:+.2f}%"),
    ("2024 Actual Yield",       "yield_2024_pct",        lambda v: f"{v:.2f}%"),
    ("Median Home Value",       "median_home_value",     lambda v: f"${v:,.0f}"),
    ("Median Monthly Rent",     "median_gross_rent",     lambda v: f"${v:,.0f}"),
    ("Median HH Income",        "median_household_income",lambda v: f"${v:,.0f}"),
    ("Vacancy Rate",            "vacancy_rate",          lambda v: f"{v:.1%}"),
    ("Total Enrollment",        "total_enrollment",      lambda v: f"{v:,.0f}"),
    ("Housing Capacity",        "total_housing_cap",     lambda v: f"{v:,.0f}"),
    ("Housing Deficit",         "housing_deficit",       lambda v: f"{v:,.0f}"),
    ("Enrollment Intensity",    "enrollment_intensity",  lambda v: f"{v:.3f}"),
    ("% Bachelor+",             "pct_bachelor_plus",     lambda v: f"{v:.1%}"),
    ("Confidence",              "confidence",            lambda v: str(v)),
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

# ── Bar charts ────────────────────────────────────────────────────────────────
section_title("Visual Comparison")

CHART_METRICS = [
    ("2025 Predicted Yield (%)",    "yield_2025_pct",        GOLD),
    ("2026 Predicted Yield (%)",    "yield_2026_pct",        NAVY),
    ("Change vs 2024 (%)",          "yield_change_pct",      GREEN),
    ("Median Home Value ($000s)",   "median_home_value",     "#4472C4"),
    ("Enrollment",                  "total_enrollment",      "#7B4EA0"),
    ("Housing Deficit",             "housing_deficit",       "#CC6000"),
]

cols = st.columns(2)
for i, (title, col, color) in enumerate(CHART_METRICS):
    if col not in view.columns:
        continue
    sub = view[["label", col]].dropna(subset=[col]).copy()
    if len(sub) == 0:
        continue

    scale = 1000 if "home_value" in col else 1
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

# ── Radar chart ───────────────────────────────────────────────────────────────
section_title("Radar — Normalized Profile")
st.markdown(
    f'<p style="color:{GRAY};font-size:13px">All metrics normalized 0–1 within the full 428-county dataset '
    f'(1 = best in class for that metric).</p>',
    unsafe_allow_html=True,
)

RADAR_METRICS = [
    ("Yield",       "yield_2025_pct",       True),
    ("Affordability","median_home_value",   False),   # lower home value = better
    ("Rent Growth", "yield_change_pct",     True),
    ("Enrollment",  "total_enrollment",     True),
    ("Housing Deficit","housing_deficit",   True),
    ("Edu. Attain.","pct_bachelor_plus",    True),
]

def normalize(series, higher_is_better):
    mn, mx = df[series.name].min(), df[series.name].max()
    n = (series - mn) / (mx - mn) if mx > mn else series * 0
    return n if higher_is_better else (1 - n)

radar_fig = go.Figure()
palette = [NAVY, GOLD, GREEN, RED, "#4472C4", "#CC6000"]

for idx, county_label in enumerate(selected):
    row = view[view["label"] == county_label]
    if row.empty:
        continue
    vals = []
    categories = []
    for cat, col, higher in RADAR_METRICS:
        if col in df.columns and pd.notna(row[col].values[0]):
            full_col = df[col].rename(col)
            n = normalize(full_col, higher)
            v = n.loc[df["label"] == county_label]
            vals.append(float(v.values[0]) if len(v) > 0 else 0.0)
        else:
            vals.append(0.0)
        categories.append(cat)

    vals += [vals[0]]
    cats  = categories + [categories[0]]

    radar_fig.add_trace(go.Scatterpolar(
        r=vals, theta=cats,
        fill="toself", name=county_label,
        line_color=palette[idx % len(palette)],
        fillcolor=palette[idx % len(palette)].replace("#", "rgba(") + ",0.12)" if False else palette[idx % len(palette)],
        opacity=0.7,
    ))

radar_fig.update_layout(
    **LAYOUT_BASE,
    polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=9))),
    showlegend=True,
    height=420, margin=dict(l=40, r=40, t=20, b=20),
)
st.plotly_chart(radar_fig, use_container_width=True)
