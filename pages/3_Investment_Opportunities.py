import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from app_utils import (
    NAVY, GOLD, GREEN, RED, GRAY, LIGHT, LAYOUT_BASE,
    load_merged, page_header, section_title,
)

st.set_page_config(page_title="Investment Opportunities", page_icon="💰", layout="wide")
page_header(
    "Investment Opportunity Finder",
    "AI-curated insights to identify the strongest college-town rental markets",
)

df = load_merged()

year_sel  = st.radio("Forecast Year", [2025, 2026], horizontal=True)
yield_col = "yield_2025_pct" if year_sel == 2025 else "yield_2026_pct"
top_n     = st.slider("Counties to show per section", 10, 30, 15)

nat_med_yield = df[yield_col].median()
nat_med_hv    = df["median_home_value"].median()

df["label"] = df["county"] + ", " + df["state"]

def bar(data, x_col, title, color=NAVY, fmt=".2f", suffix="%"):
    data = data.sort_values(x_col)
    fig = go.Figure(go.Bar(
        x=data[x_col], y=data["label"], orientation="h",
        marker_color=color,
        text=[f"{v:{fmt}}{suffix}" for v in data[x_col]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>" + title.split("—")[0].strip() + ": %{x:.2f}%<extra></extra>",
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

# ── Section 1: High Yield + Low Affordability Pressure ───────────────────────
section_title("High Yield · Low Home Value Pressure")
st.markdown(
    f"""<div style="background:{LIGHT};border-left:4px solid {GOLD};border-radius:6px;
        padding:10px 14px;margin-bottom:12px;font-size:13px;color:{GRAY}">
      Counties where predicted yield is <strong>above the national median ({nat_med_yield:.2f}%)</strong>
      AND median home value is <strong>below the national median
      (${nat_med_hv:,.0f})</strong>. These markets combine strong returns with lower capital
      requirements — the most accessible entry point for investors.
    </div>""",
    unsafe_allow_html=True,
)

s1 = df[
    (df[yield_col] > nat_med_yield) &
    (df["median_home_value"].notna()) &
    (df["median_home_value"] < nat_med_hv)
].nlargest(top_n, yield_col)

col1a, col1b = st.columns(2)
with col1a:
    st.plotly_chart(bar(s1, yield_col, f"Predicted Yield ({year_sel})"), use_container_width=True)
with col1b:
    if "median_home_value" in s1.columns:
        s1_sorted = s1.sort_values("median_home_value")
        fig2 = go.Figure(go.Bar(
            x=s1_sorted["median_home_value"] / 1000,
            y=s1_sorted["label"], orientation="h",
            marker_color="#4472C4",
            text=[f"${v:,.0f}k" for v in s1_sorted["median_home_value"] / 1000],
            textposition="outside",
        ))
        fig2.update_layout(
            **LAYOUT_BASE,
            title="<b>Median Home Value (Lower = More Accessible)</b>",
            xaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="k"),
            yaxis=dict(showgrid=False),
            height=max(360, len(s1_sorted) * 22),
            margin=dict(l=10, r=80, t=45, b=30),
        )
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Section 2: Counties Expected to Improve ───────────────────────────────────
section_title("Counties Expected to Improve — Going Up in 2025")
st.markdown(
    f"""<div style="background:{LIGHT};border-left:4px solid {GREEN};border-radius:6px;
        padding:10px 14px;margin-bottom:12px;font-size:13px;color:{GRAY}">
      Counties with a <strong>positive predicted yield change vs 2024</strong>, sorted by the
      size of the improvement. These markets show upward momentum — early positioning
      may capture outsized gains.
    </div>""",
    unsafe_allow_html=True,
)

s2 = df[df["yield_change_pct"] > 0].nlargest(top_n, "yield_change_pct")

col2a, col2b = st.columns(2)
with col2a:
    s2c = s2.sort_values("yield_change_pct")
    fig_chg = go.Figure(go.Bar(
        x=s2c["yield_change_pct"], y=s2c["label"], orientation="h",
        marker_color=GREEN,
        text=[f"+{v:.2f}%" for v in s2c["yield_change_pct"]],
        textposition="outside",
    ))
    fig_chg.update_layout(
        **LAYOUT_BASE,
        title="<b>Yield Improvement vs 2024</b>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="%"),
        yaxis=dict(showgrid=False),
        height=max(360, len(s2c) * 22),
        margin=dict(l=10, r=80, t=45, b=30),
    )
    st.plotly_chart(fig_chg, use_container_width=True)
with col2b:
    fig_2026 = go.Figure(go.Bar(
        x=s2.sort_values(yield_col)[yield_col],
        y=s2.sort_values(yield_col)["label"],
        orientation="h",
        marker_color=NAVY,
        text=[f"{v:.2f}%" for v in s2.sort_values(yield_col)[yield_col]],
        textposition="outside",
    ))
    fig_2026.update_layout(
        **LAYOUT_BASE,
        title=f"<b>Absolute Predicted Yield ({year_sel})</b>",
        xaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="%"),
        yaxis=dict(showgrid=False),
        height=max(360, len(s2) * 22),
        margin=dict(l=10, r=80, t=45, b=30),
    )
    st.plotly_chart(fig_2026, use_container_width=True)

st.divider()

# ── Section 3: Hidden Opportunities ───────────────────────────────────────────
section_title("Hidden Opportunities — High Yield · Housing Deficit · Affordable Entry")
st.markdown(
    f"""<div style="background:{LIGHT};border-left:4px solid {NAVY};border-radius:6px;
        padding:10px 14px;margin-bottom:12px;font-size:13px;color:{GRAY}">
      Counties that satisfy <em>all three</em> criteria: predicted yield
      <strong>above the national median</strong>, an active
      <strong>housing deficit</strong> (enrollment exceeds on-campus capacity, creating
      persistent off-campus demand), and home values
      <strong>below the national median</strong>. These are the most structurally
      advantaged markets in the dataset.
    </div>""",
    unsafe_allow_html=True,
)

s3_mask = (
    (df[yield_col] > nat_med_yield) &
    (df["housing_deficit"].notna()) &
    (df["housing_deficit"] > 0) &
    (df["median_home_value"].notna()) &
    (df["median_home_value"] < nat_med_hv)
)
s3 = df[s3_mask].nlargest(top_n, yield_col)

if len(s3) == 0:
    st.info("No counties match all three criteria with current data. Try relaxing the affordability filter in the County Explorer.")
else:
    cols_show = [c for c in [
        "county", "state", yield_col, "yield_change_pct",
        "median_home_value", "total_enrollment", "housing_deficit",
        "enrollment_intensity", "confidence",
    ] if c in s3.columns]

    rename = {
        yield_col: f"{year_sel} Yield",
        "yield_change_pct": "Δ vs 2024",
        "median_home_value": "Home Value",
        "total_enrollment": "Enrollment",
        "housing_deficit": "Housing Deficit",
        "enrollment_intensity": "Enroll. Intensity",
    }
    out = s3[cols_show].rename(columns=rename).copy()
    for col, fn in [
        (f"{year_sel} Yield", lambda v: f"{v:.2f}%"),
        ("Δ vs 2024", lambda v: f"{v:+.2f}%"),
        ("Home Value", lambda v: f"${v:,.0f}"),
        ("Enrollment", lambda v: f"{v:,.0f}"),
        ("Housing Deficit", lambda v: f"{v:,.0f}"),
        ("Enroll. Intensity", lambda v: f"{v:.3f}"),
    ]:
        import pandas as pd
        if col in out.columns:
            out[col] = out[col].map(lambda v, f=fn: f(v) if pd.notna(v) else "—")

    st.dataframe(out.reset_index(drop=True), use_container_width=True)

    col3a, col3b = st.columns(2)
    with col3a:
        st.plotly_chart(
            bar(s3.copy(), yield_col, f"Hidden Gem Yield ({year_sel})", GOLD),
            use_container_width=True,
        )
    with col3b:
        if "housing_deficit" in s3.columns:
            s3d = s3.sort_values("housing_deficit")
            fig_d = go.Figure(go.Bar(
                x=s3d["housing_deficit"] / 1000,
                y=s3d["label"], orientation="h",
                marker_color="#7B4EA0",
                text=[f"{v:,.0f}k" for v in s3d["housing_deficit"] / 1000],
                textposition="outside",
            ))
            fig_d.update_layout(
                **LAYOUT_BASE,
                title="<b>Housing Deficit (students, thousands)</b>",
                xaxis=dict(showgrid=True, gridcolor="#E5E7EB", ticksuffix="k"),
                yaxis=dict(showgrid=False),
                height=max(360, len(s3d) * 22),
                margin=dict(l=10, r=80, t=45, b=30),
            )
            st.plotly_chart(fig_d, use_container_width=True)
