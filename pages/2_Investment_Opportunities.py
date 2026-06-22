import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app_utils import (
    NAVY, GOLD, GREEN, GRAY, LIGHT, LAYOUT_BASE,
    load_merged, page_header, section_title,
)

st.set_page_config(page_title="Investment Opportunities", page_icon="💰", layout="wide")
page_header(
    "Investment Opportunity Finder",
    "AI-curated insights into the strongest college-town rental markets",
)

df = load_merged()
df["label"] = df["county"] + ", " + df["state"]

year_sel  = st.radio("Forecast Year", [2025, 2026], horizontal=True)
yield_col = "yield_2025_pct" if year_sel == 2025 else "yield_2026_pct"

nat_med_yield = df[yield_col].median()
nat_med_hv    = df["median_home_value"].median()

TOP_N = 15

def hbar(data, x_col, title, color=NAVY, suffix="%", fmt=".2f"):
    data = data.sort_values(x_col)
    fig = go.Figure(go.Bar(
        x=data[x_col], y=data["label"], orientation="h",
        marker_color=color,
        text=[f"{v:{fmt}}{suffix}" for v in data[x_col]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=f"<b>{title}</b>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix=suffix),
        yaxis=dict(showgrid=False),
        height=max(360, len(data) * 22),
        margin=dict(l=10, r=80, t=45, b=30),
    )
    return fig

# ── Section 1: Predicted to Gain ─────────────────────────────────────────────
section_title("Predicted to Gain — Highest Upward Momentum")
st.markdown(
    f"""<div style="background:{LIGHT};border-left:4px solid {GREEN};border-radius:6px;
        padding:10px 14px;margin-bottom:14px;font-size:13px;color:{GRAY}">
      Counties where the Random Forest model predicts the <strong>largest yield
      improvement vs 2024</strong>. This is model-driven, not historical — it reflects
      the model's forward-looking assessment of improving market conditions.
    </div>""",
    unsafe_allow_html=True,
)

s1 = df[df["yield_change_pct"] > 0].nlargest(TOP_N, "yield_change_pct").copy()

col1a, col1b = st.columns(2)
with col1a:
    st.plotly_chart(
        hbar(s1.copy(), "yield_change_pct", f"Predicted Yield Gain vs 2024", GREEN, "+%", "+.2f"),
        use_container_width=True,
    )
with col1b:
    st.plotly_chart(
        hbar(s1.copy(), yield_col, f"Absolute Predicted Yield ({year_sel})", NAVY),
        use_container_width=True,
    )

st.divider()

# ── Section 2: Hidden Gems ────────────────────────────────────────────────────
section_title("Hidden Gems — High Yield · Housing Deficit · Affordable Entry")
st.markdown(
    f"""<div style="background:{LIGHT};border-left:4px solid {NAVY};border-radius:6px;
        padding:10px 14px;margin-bottom:14px;font-size:13px;color:{GRAY}">
      Counties satisfying <em>all three</em> criteria: predicted yield
      <strong>above the national median ({nat_med_yield:.2f}%)</strong>, an active
      <strong>housing deficit</strong> (enrollment exceeds on-campus capacity, creating
      persistent off-campus rental demand), and home values
      <strong>below the national median (${nat_med_hv:,.0f})</strong>.
      These are the most structurally advantaged markets in the dataset.
    </div>""",
    unsafe_allow_html=True,
)

s2 = df[
    (df[yield_col] > nat_med_yield) &
    (df["housing_deficit"].notna()) & (df["housing_deficit"] > 0) &
    (df["median_home_value"].notna()) & (df["median_home_value"] < nat_med_hv)
].nlargest(TOP_N, yield_col).copy()

if len(s2) == 0:
    st.info("No counties match all three criteria with current data.")
else:
    col2a, col2b = st.columns(2)
    with col2a:
        st.plotly_chart(
            hbar(s2.copy(), yield_col, f"Hidden Gem Yield ({year_sel})", GOLD),
            use_container_width=True,
        )
    with col2b:
        s2d = s2.sort_values("housing_deficit")
        fig_d = go.Figure(go.Bar(
            x=s2d["housing_deficit"] / 1000,
            y=s2d["label"], orientation="h",
            marker_color="#7B4EA0",
            text=[f"{v:,.1f}k" for v in s2d["housing_deficit"] / 1000],
            textposition="outside",
        ))
        fig_d.update_layout(
            **LAYOUT_BASE,
            title="<b>Housing Deficit (students, 000s)</b>",
            xaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="k"),
            yaxis=dict(showgrid=False),
            height=max(360, len(s2d) * 22),
            margin=dict(l=10, r=80, t=45, b=30),
        )
        st.plotly_chart(fig_d, use_container_width=True)

    # Summary table
    section_title("Hidden Gems — Full Detail")
    cols_show = [c for c in [
        "county", "state", yield_col, "yield_change_pct",
        "median_home_value", "total_enrollment", "housing_deficit",
        "enrollment_intensity", "confidence",
    ] if c in s2.columns]
    rename = {
        yield_col: f"{year_sel} Yield", "yield_change_pct": "Δ vs 2024",
        "median_home_value": "Home Value", "total_enrollment": "Enrollment",
        "housing_deficit": "Housing Deficit", "enrollment_intensity": "Enroll. Intensity",
    }
    out = s2[cols_show].rename(columns=rename).copy()
    for col, fn in [
        (f"{year_sel} Yield", lambda v: f"{v:.2f}%"),
        ("Δ vs 2024",         lambda v: f"{v:+.2f}%"),
        ("Home Value",        lambda v: f"${v:,.0f}"),
        ("Enrollment",        lambda v: f"{v:,.0f}"),
        ("Housing Deficit",   lambda v: f"{v:,.0f}"),
        ("Enroll. Intensity", lambda v: f"{v:.3f}"),
    ]:
        if col in out.columns:
            out[col] = out[col].map(lambda v, f=fn: f(v) if pd.notna(v) else "—")
    st.dataframe(out.reset_index(drop=True), use_container_width=True)
