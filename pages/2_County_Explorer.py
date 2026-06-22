import streamlit as st
import pandas as pd
from app_utils import NAVY, GOLD, GRAY, LIGHT, load_merged, page_header, section_title

st.set_page_config(page_title="County Explorer", page_icon="🔍", layout="wide")
page_header(
    "County Explorer",
    "Filter and search all 428 college-town counties · adjust sliders to narrow results",
)

df = load_merged()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<h2 style="color:{NAVY};font-family:Arial;margin-top:0">Filters</h2>',
        unsafe_allow_html=True,
    )

    state_opts = ["All States"] + sorted(df["state"].dropna().unique().tolist())
    state_sel  = st.selectbox("State", state_opts)

    year_sel  = st.radio("Forecast Year", [2025, 2026])
    yield_col = "yield_2025_pct" if year_sel == 2025 else "yield_2026_pct"

    conf_sel = st.multiselect("Confidence", ["high", "medium", "low"],
                              default=["high", "medium", "low"])

    ymin, ymax = float(df[yield_col].min()), float(df[yield_col].max())
    yield_range = st.slider("Predicted Yield (%)", ymin, ymax,
                             (ymin, ymax), step=0.1, format="%.1f")

    hv_min = float(df["median_home_value"].dropna().min())
    hv_max = float(df["median_home_value"].dropna().max())
    hv_range = st.slider("Home Value ($)", hv_min, hv_max,
                          (hv_min, hv_max), step=10000, format="$%.0f")

    enr = df["total_enrollment"].dropna()
    if len(enr) > 0:
        enr_range = st.slider(
            "Enrollment (students)", 0.0, float(enr.max()),
            (0.0, float(enr.max())), step=1000, format="%.0f",
        )
    else:
        enr_range = (0.0, 1e9)

    deficit_only = st.checkbox("Housing deficit only (enrollment > capacity)")

# ── Apply filters ─────────────────────────────────────────────────────────────
view = df.copy()
if state_sel != "All States":
    view = view[view["state"] == state_sel]
if conf_sel:
    view = view[view["confidence"].isin(conf_sel)]

view = view[
    view[yield_col].between(yield_range[0], yield_range[1])
    & view["median_home_value"].between(hv_range[0], hv_range[1])
]

if "total_enrollment" in view.columns:
    enr_mask = view["total_enrollment"].isna() | view["total_enrollment"].between(
        enr_range[0], enr_range[1]
    )
    view = view[enr_mask]

if deficit_only and "housing_deficit" in view.columns:
    view = view[view["housing_deficit"] > 0]

view = view.sort_values(yield_col, ascending=False).reset_index(drop=True)

# ── Stats row ─────────────────────────────────────────────────────────────────
n    = len(view)
avg  = view[yield_col].mean() if n > 0 else 0
best = view.iloc[0]["county"] + ", " + view.iloc[0]["state"] if n > 0 else "—"

c1, c2, c3 = st.columns(3)
for col, lbl, val in [(c1, "Counties Shown", str(n)),
                       (c2, "Avg Predicted Yield", f"{avg:.2f}%"),
                       (c3, "Top County", best)]:
    col.markdown(
        f'<div style="background:{LIGHT};border-left:4px solid {NAVY};border-radius:8px;'
        f'padding:10px 14px"><div style="font-size:20px;font-weight:700;color:{NAVY}">{val}</div>'
        f'<div style="font-size:11px;color:{GRAY}">{lbl}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Results table ─────────────────────────────────────────────────────────────
section_title(f"Results — {n} counties")

if n == 0:
    st.warning("No counties match the current filters.")
    st.stop()

DISPLAY = {
    "county":              "County",
    "state":               "State",
    yield_col:             f"{year_sel} Yield",
    "yield_change_pct":    "Δ vs 2024",
    "confidence":          "Confidence",
    "median_home_value":   "Home Value",
    "median_gross_rent":   "Rent/mo",
    "median_household_income": "Median Income",
    "total_enrollment":    "Enrollment",
    "total_housing_cap":   "Housing Cap",
    "housing_deficit":     "Housing Deficit",
    "enrollment_intensity":"Enroll. Intensity",
    "vacancy_rate":        "Vacancy Rate",
}

out = view[[c for c in DISPLAY if c in view.columns]].rename(columns=DISPLAY).copy()

def fmt(col, fn):
    if col in out.columns:
        out[col] = out[col].map(lambda v: fn(v) if pd.notna(v) else "—")

fmt(f"{year_sel} Yield",    lambda v: f"{v:.2f}%")
fmt("Δ vs 2024",            lambda v: f"{v:+.2f}%")
fmt("Home Value",           lambda v: f"${v:,.0f}")
fmt("Rent/mo",              lambda v: f"${v:,.0f}")
fmt("Median Income",        lambda v: f"${v:,.0f}")
fmt("Enrollment",           lambda v: f"{v:,.0f}")
fmt("Housing Cap",          lambda v: f"{v:,.0f}")
fmt("Housing Deficit",      lambda v: f"{v:,.0f}")
fmt("Enroll. Intensity",    lambda v: f"{v:.3f}")
fmt("Vacancy Rate",         lambda v: f"{v:.1%}")

st.dataframe(out, use_container_width=True, height=520)

st.download_button(
    "Download CSV",
    view[[c for c in DISPLAY if c in view.columns]].to_csv(index=False),
    file_name=f"college_towns_{year_sel}.csv",
    mime="text/csv",
)
