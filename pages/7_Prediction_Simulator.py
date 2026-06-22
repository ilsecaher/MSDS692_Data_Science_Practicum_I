import streamlit as st
import plotly.graph_objects as go
import numpy as np
from utils import NAVY, GOLD, GREEN, RED, GRAY, LIGHT, LAYOUT_BASE, load_merged, page_header, section_title

st.set_page_config(page_title="Prediction Simulator", page_icon="🎮", layout="wide")
page_header(
    "Prediction Simulator",
    "Adjust market inputs to estimate gross rental yield — powered by the Random Forest model logic",
)

df = load_merged()

st.markdown(
    f"""<div style="background:{LIGHT};border-left:4px solid {GOLD};border-radius:6px;
        padding:12px 16px;margin-bottom:16px;font-size:13px;color:{GRAY}">
      This simulator applies the core relationships learned by the Random Forest model
      to estimate gross rental yield from market inputs. The formula mirrors the model's
      top drivers: <strong>home value, rent, enrollment pressure, and vacancy rate</strong>.
      It is an illustrative approximation — actual predictions use 20+ features.
    </div>""",
    unsafe_allow_html=True,
)

# ── National benchmarks ───────────────────────────────────────────────────────
nat_med_hv    = df["median_home_value"].median()
nat_med_rent  = df["median_gross_rent"].median()
nat_med_enr   = df["total_enrollment"].dropna().median()
nat_med_cap   = df["total_housing_cap"].dropna().median()
nat_med_vac   = df["vacancy_rate"].dropna().median()
nat_med_yield = df["yield_2025_pct"].median()

# ── Sliders ───────────────────────────────────────────────────────────────────
col_l, col_r = st.columns([2, 3], gap="large")

with col_l:
    section_title("Market Inputs")

    home_value = st.slider(
        "Median Home Value ($)",
        min_value=100_000, max_value=1_500_000,
        value=int(nat_med_hv), step=10_000, format="$%d",
    )
    monthly_rent = st.slider(
        "Median Monthly Rent ($)",
        min_value=400, max_value=3_000,
        value=int(nat_med_rent), step=50, format="$%d",
    )
    enrollment = st.slider(
        "Total Student Enrollment",
        min_value=500, max_value=80_000,
        value=int(nat_med_enr), step=500,
    )
    housing_cap = st.slider(
        "On-Campus Housing Capacity",
        min_value=0, max_value=30_000,
        value=int(nat_med_cap), step=250,
    )
    vacancy_rate = st.slider(
        "Vacancy Rate (%)",
        min_value=2.0, max_value=25.0,
        value=float(nat_med_vac * 100), step=0.5, format="%.1f%%",
    )

# ── Estimation model ──────────────────────────────────────────────────────────
def estimate_yield(home_val, rent, enr, cap, vac_pct):
    base = (rent * 12) / home_val * 100

    housing_deficit = max(0, enr - cap)
    deficit_ratio   = housing_deficit / max(enr, 1)
    enr_boost       = 1 + 0.12 * deficit_ratio

    vac_penalty = 1 - max(0, (vac_pct / 100 - 0.05) * 2.5)
    vac_penalty = max(0.75, vac_penalty)

    estimated = base * enr_boost * vac_penalty
    return round(max(1.0, min(16.0, estimated)), 2)

est_yield    = estimate_yield(home_value, monthly_rent, enrollment, housing_cap, vacancy_rate)
base_yield   = round((monthly_rent * 12) / home_value * 100, 2)
deficit      = max(0, enrollment - housing_cap)
vs_national  = est_yield - nat_med_yield

# ── Results ───────────────────────────────────────────────────────────────────
with col_r:
    section_title("Estimated Rental Yield")

    color = GREEN if est_yield >= nat_med_yield else RED
    st.markdown(
        f"""<div style="background:{NAVY};border-radius:12px;padding:28px 32px;
            text-align:center;margin-bottom:16px">
          <div style="color:{GOLD};font-size:13px;letter-spacing:1px;margin-bottom:6px">
            ESTIMATED GROSS RENTAL YIELD
          </div>
          <div style="color:white;font-size:56px;font-weight:700;line-height:1">
            {est_yield:.2f}%
          </div>
          <div style="color:{color};font-size:16px;margin-top:10px">
            {'+' if vs_national >= 0 else ''}{vs_national:.2f}% vs national median ({nat_med_yield:.2f}%)
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Decomposition
    sub1, sub2, sub3 = st.columns(3)
    sub1.markdown(
        f'<div style="background:{LIGHT};border-left:3px solid {NAVY};border-radius:6px;'
        f'padding:10px;text-align:center"><div style="font-size:18px;font-weight:700;color:{NAVY}">'
        f'{base_yield:.2f}%</div><div style="font-size:11px;color:{GRAY}">Base Yield<br>(rent/price)</div></div>',
        unsafe_allow_html=True,
    )
    sub2.markdown(
        f'<div style="background:{LIGHT};border-left:3px solid {GOLD};border-radius:6px;'
        f'padding:10px;text-align:center"><div style="font-size:18px;font-weight:700;color:{NAVY}">'
        f'{deficit:,.0f}</div><div style="font-size:11px;color:{GRAY}">Housing<br>Deficit</div></div>',
        unsafe_allow_html=True,
    )
    sub3.markdown(
        f'<div style="background:{LIGHT};border-left:3px solid {RED if vacancy_rate > 8 else GREEN};'
        f'border-radius:6px;padding:10px;text-align:center">'
        f'<div style="font-size:18px;font-weight:700;color:{NAVY}">{vacancy_rate:.1f}%</div>'
        f'<div style="font-size:11px;color:{GRAY}">Vacancy<br>Rate</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Gauge-style bar vs comparators
    section_title("How Does This Compare?")

    comparators = {
        "Your estimate":        est_yield,
        "National median":      nat_med_yield,
        "Top quartile (75th)":  df["yield_2025_pct"].quantile(0.75),
        "Bottom quartile (25th)": df["yield_2025_pct"].quantile(0.25),
    }
    c_names  = list(comparators.keys())
    c_values = list(comparators.values())
    c_colors = [GOLD if n == "Your estimate" else NAVY for n in c_names]

    fig_comp = go.Figure(go.Bar(
        x=c_values, y=c_names, orientation="h",
        marker_color=c_colors,
        text=[f"{v:.2f}%" for v in c_values],
        textposition="outside",
    ))
    fig_comp.update_layout(
        **LAYOUT_BASE,
        xaxis=dict(title="Gross Rental Yield (%)", ticksuffix="%",
                   showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(showgrid=False),
        height=240, margin=dict(l=10, r=80, t=20, b=30),
        showlegend=False,
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Sensitivity — home value
    section_title("Sensitivity — How Yield Changes with Home Value")
    hv_range   = np.linspace(100_000, 1_500_000, 50)
    sens_yields = [estimate_yield(hv, monthly_rent, enrollment, housing_cap, vacancy_rate)
                   for hv in hv_range]

    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(
        x=hv_range / 1000, y=sens_yields,
        mode="lines",
        line=dict(color=NAVY, width=2.5),
        name="Estimated Yield",
    ))
    fig_sens.add_vline(x=home_value / 1000, line_dash="dot",
                       line_color=GOLD, line_width=2,
                       annotation_text=f"Current: ${home_value/1000:.0f}k",
                       annotation_font_color=GOLD)
    fig_sens.update_layout(
        **LAYOUT_BASE,
        xaxis=dict(title="Home Value ($000s)", ticksuffix="k",
                   showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(title="Estimated Yield (%)", ticksuffix="%",
                   showgrid=True, gridcolor="#E5E7EB"),
        height=280, margin=dict(l=10, r=20, t=20, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_sens, use_container_width=True)
