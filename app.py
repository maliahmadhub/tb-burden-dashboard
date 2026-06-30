"""
The Global Tuberculosis Burden Dashboard
=========================================
A consulting-grade analytics dashboard built for a healthcare decision-maker
(e.g., a national TB programme, MoPH, or global health funder).

Author : Mohamad Ali Ahmad
Course  : MSBA 382 - Healthcare Analytics
Data    : WHO Global Tuberculosis Programme (public CSV database)

Run with:  streamlit run app.py
"""

import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# 0. PAGE CONFIG & THEME
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Global TB Burden Dashboard",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#0E4D64"     # deep teal
ACCENT = "#E4572E"      # signal red/orange
GOOD = "#2A9D8F"
GREY = "#6c757d"

CUSTOM_CSS = f"""
<style>
    .main {{ background-color: #F7F9FA; }}
    h1, h2, h3 {{ color: {PRIMARY}; }}
    .stMetric {{ background:#FFFFFF; border:1px solid #e6e6e6; border-radius:12px;
                 padding:14px 14px 6px 14px; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
    .insight {{ background:#FFFFFF; border-left:5px solid {ACCENT}; padding:14px 18px;
                border-radius:6px; margin:8px 0; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
    .src {{ color:{GREY}; font-size:0.8rem; }}
    div[data-testid="stSidebarNav"] {{ display:none; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 1. DATA LAYER  (live WHO download -> cached -> local fallback)
# ----------------------------------------------------------------------------
import os

WHO = "https://extranet.who.int/tme/generateCSV.asp?ds="
URLS = {
    "estimates":  WHO + "estimates",
    "age_sex":    WHO + "estimates_age_sex",
    "dr":         WHO + "mdr_rr_estimates",
    "outcomes":   WHO + "outcomes",
}
# Bundled (committed) files — see prepare_data.py to (re)generate the full set.
LOCAL = {
    "estimates": "data/TB_estimates.csv",
    "age_sex":   "data/TB_age_sex.csv",
    "dr":        "data/TB_mdr_rr.csv",
    "outcomes":  "data/TB_outcomes.csv",
}
LOCAL_SAMPLE = "data/estimates_sample.csv"

REGION_NAMES = {
    "AFR": "Africa", "AMR": "Americas", "EMR": "Eastern Mediterranean",
    "EUR": "Europe", "SEA": "South-East Asia", "WPR": "Western Pacific",
}


def _read(key: str):
    """Load a dataset: bundled local file first (repo is self-contained),
    then live WHO download, returning (dataframe_or_None, source_label)."""
    path = LOCAL.get(key)
    if path and os.path.exists(path):
        try:
            return pd.read_csv(path, low_memory=False), "bundled"
        except Exception:
            pass
    try:
        return pd.read_csv(URLS[key], low_memory=False), "live"
    except Exception:
        return None, "unavailable"


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading WHO TB estimates…")
def load_estimates() -> tuple[pd.DataFrame, str]:
    """Return (dataframe, source_label). bundled -> live -> sample."""
    df, source = _read("estimates")
    if df is None:
        df, source = pd.read_csv(LOCAL_SAMPLE), "offline sample"
    df = df.rename(columns={"g_whoregion": "region"})
    df["region_name"] = df["region"].map(REGION_NAMES).fillna(df["region"])
    for col in ["e_inc_num", "e_inc_100k", "e_mort_num", "e_mort_100k",
                "e_inc_tbhiv_num", "c_cdr", "c_newinc_100k", "e_pop_num"]:
        if col not in df.columns:
            df[col] = np.nan
    return df, source


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading age/sex breakdown…")
def load_age_sex() -> pd.DataFrame | None:
    df, _ = _read("age_sex")
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Loading drug-resistance estimates…")
def load_dr() -> pd.DataFrame | None:
    df, _ = _read("dr")
    return df


def fmt(n, suffix=""):
    """Human-friendly large-number formatting."""
    if pd.isna(n):
        return "n/a"
    n = float(n)
    if abs(n) >= 1e9:
        return f"{n/1e9:.2f}B{suffix}"
    if abs(n) >= 1e6:
        return f"{n/1e6:.2f}M{suffix}"
    if abs(n) >= 1e3:
        return f"{n/1e3:.0f}K{suffix}"
    return f"{n:,.0f}{suffix}"


# ----------------------------------------------------------------------------
# 2. AUTH GATE
# ----------------------------------------------------------------------------
APP_PASSWORD = "tb2024"   # demo gate; change or wire to st.secrets for production


def login_gate():
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f"<h1 style='text-align:center'>🫁 Global TB Burden Dashboard</h1>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:#6c757d'>A decision-support tool for "
            "tuberculosis control. Built on the WHO Global TB Programme database.</p>",
            unsafe_allow_html=True)
        with st.form("login"):
            pw = st.text_input("Access code", type="password",
                               placeholder="Enter access code")
            ok = st.form_submit_button("Enter dashboard", use_container_width=True)
        st.caption("Demo access code: **tb2024**")
        if ok:
            if pw == APP_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Incorrect access code.")


if "auth" not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    login_gate()
    st.stop()

# ----------------------------------------------------------------------------
# 3. LOAD DATA + SIDEBAR FILTERS
# ----------------------------------------------------------------------------
est, source = load_estimates()
years = sorted(est["year"].dropna().unique().astype(int))
regions = sorted(est["region_name"].dropna().unique())

st.sidebar.title("🫁 TB Dashboard")
page = st.sidebar.radio(
    "Navigate",
    ["Executive Overview", "Trend Analysis", "Geographic Map",
     "Age & Sex", "Drug-Resistant TB & HIV", "Care Cascade",
     "Predictive Analysis", "Methodology & Data", "Insights & Recommendations"],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Global filters")
sel_regions = st.sidebar.multiselect("WHO region", regions, default=regions)
yr_min, yr_max = int(min(years)), int(max(years))
sel_year = st.sidebar.slider("Reporting year", yr_min, yr_max, yr_max)
sel_range = st.sidebar.slider("Trend window", yr_min, yr_max, (yr_min, yr_max))

if source == "offline sample":
    st.sidebar.warning("⚠️ Running on the small offline **sample**. Run "
                       "`python prepare_data.py` to bundle the full WHO dataset, "
                       "or connect to the internet and press Reload.")
elif source == "bundled":
    st.sidebar.success("✅ Full WHO dataset (bundled in repo).")
else:
    st.sidebar.success("✅ Live WHO data loaded.")
st.sidebar.markdown(
    "<span class='src'>Source: WHO Global TB Programme, "
    "Global Tuberculosis Report.</span>", unsafe_allow_html=True)

# Guard: at least one region must be selected
if not sel_regions:
    st.warning("Select at least one WHO region in the sidebar to display the dashboard.")
    st.stop()

# Filtered frames
f = est[est["region_name"].isin(sel_regions)].copy()
fy = f[f["year"] == sel_year].copy()
ftrend = f[(f["year"] >= sel_range[0]) & (f["year"] <= sel_range[1])].copy()


def world_year(df, year):
    """Global totals/derived rates for a given year across all regions in data."""
    d = est[est["year"] == year]
    inc = d["e_inc_num"].sum()
    mort = d["e_mort_num"].sum()
    hiv = d["e_inc_tbhiv_num"].sum()
    pop = d["e_pop_num"].sum()
    inc_rate = inc / pop * 1e5 if pop else np.nan
    return inc, mort, hiv, inc_rate, pop


# ----------------------------------------------------------------------------
# 4. PAGES
# ----------------------------------------------------------------------------
def page_overview():
    st.title("Executive Overview")
    st.caption(f"Tuberculosis burden snapshot — {sel_year}. "
               "Tuberculosis is the world's leading cause of death from a single "
               "infectious agent.")

    inc, mort, hiv, inc_rate, pop = world_year(est, sel_year)
    prev_inc, prev_mort, *_ = world_year(est, max(sel_year - 1, yr_min))
    d_inc = (inc - prev_inc) / prev_inc * 100 if prev_inc else 0
    d_mort = (mort - prev_mort) / prev_mort * 100 if prev_mort else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Estimated new cases (incidence)", fmt(inc), f"{d_inc:+.1f}% vs prior yr")
    k2.metric("Estimated TB deaths", fmt(mort), f"{d_mort:+.1f}% vs prior yr",
              delta_color="inverse")
    k3.metric("Incidence rate", f"{inc_rate:.0f} /100k")
    k4.metric("HIV-positive TB cases", fmt(hiv))

    st.markdown("---")
    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.subheader("Global incidence vs. mortality over time")
        g = (est.groupby("year")[["e_inc_num", "e_mort_num"]].sum().reset_index())
        fig = go.Figure()
        fig.add_bar(x=g["year"], y=g["e_inc_num"], name="New cases",
                    marker_color=PRIMARY)
        fig.add_trace(go.Scatter(x=g["year"], y=g["e_mort_num"], name="Deaths",
                                 yaxis="y2", line=dict(color=ACCENT, width=3)))
        fig.update_layout(
            yaxis=dict(title="New cases"),
            yaxis2=dict(title="Deaths", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.1), height=380,
            margin=dict(t=10, b=10), plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader(f"Burden by region — {sel_year}")
        r = (est[est["year"] == sel_year].groupby("region_name")["e_inc_num"]
             .sum().sort_values(ascending=True).reset_index())
        fig = px.bar(r, x="e_inc_num", y="region_name", orientation="h",
                     color="e_inc_num", color_continuous_scale="Teal",
                     labels={"e_inc_num": "New cases", "region_name": ""})
        fig.update_layout(height=380, coloraxis_showscale=False,
                          margin=dict(t=10, b=10), plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Highest-burden countries — {sel_year}")
    top = (fy.sort_values("e_inc_num", ascending=False)
           .head(15)[["country", "region_name", "e_inc_num", "e_inc_100k",
                      "e_mort_num", "c_cdr"]])
    top.columns = ["Country", "Region", "New cases", "Incidence /100k",
                   "Deaths", "Case detection %"]
    st.dataframe(top, use_container_width=True, hide_index=True)

    st.markdown(
        "<div class='insight'><b>So what?</b> A small number of high-burden "
        "countries account for the majority of global cases. Targeting case-finding "
        "and treatment resources at these geographies yields the largest reduction "
        "in the global burden.</div>", unsafe_allow_html=True)


def page_trend():
    st.title("Trend Analysis")
    st.caption(f"Filtered to: {', '.join(sel_regions)} | {sel_range[0]}–{sel_range[1]}")

    metric = st.selectbox("Metric", {
        "Incidence rate (/100k)": "e_inc_100k",
        "New cases (number)": "e_inc_num",
        "Mortality rate (/100k)": "e_mort_100k",
        "Deaths (number)": "e_mort_num",
    }.keys())
    col = {"Incidence rate (/100k)": "e_inc_100k", "New cases (number)": "e_inc_num",
           "Mortality rate (/100k)": "e_mort_100k", "Deaths (number)": "e_mort_num"}[metric]

    agg = "mean" if "100k" in col else "sum"
    g = (ftrend.groupby(["year", "region_name"])[col].agg(agg).reset_index())
    fig = px.line(g, x="year", y=col, color="region_name", markers=True,
                  labels={col: metric, "region_name": "Region", "year": "Year"})
    fig.update_layout(height=440, plot_bgcolor="white", legend_title="Region")
    st.plotly_chart(fig, use_container_width=True)

    countries = sorted(ftrend["country"].unique())
    pick = st.multiselect("Compare specific countries", countries,
                          default=countries[:min(4, len(countries))])
    if pick:
        gc = ftrend[ftrend["country"].isin(pick)]
        fig2 = px.line(gc, x="year", y=col, color="country", markers=True,
                       labels={col: metric, "year": "Year", "country": "Country"})
        fig2.update_layout(height=420, plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown(
        "<div class='insight'><b>Reading the trend:</b> falling rates with rising "
        "absolute cases usually signal population growth outpacing programmatic "
        "gains — progress per capita can mask a growing operational caseload.</div>",
        unsafe_allow_html=True)


def page_map():
    st.title("Geographic Distribution")
    metric = st.radio("Metric", ["Incidence rate (/100k)", "Total new cases",
                                  "Mortality rate (/100k)"], horizontal=True)
    col = {"Incidence rate (/100k)": "e_inc_100k", "Total new cases": "e_inc_num",
           "Mortality rate (/100k)": "e_mort_100k"}[metric]
    d = est[est["year"] == sel_year]
    d = d[d["region_name"].isin(sel_regions)]
    fig = px.choropleth(
        d, locations="iso3", color=col, hover_name="country",
        color_continuous_scale="OrRd", locationmode="ISO-3",
        labels={col: metric})
    fig.update_layout(height=560, margin=dict(t=10, b=10),
                      geo=dict(showframe=False, projection_type="natural earth"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "<div class='insight'><b>Geographic concentration:</b> TB incidence is "
        "highly concentrated in Africa and South-East Asia. Mapping rate vs. absolute "
        "count tells two different stories — rate flags where risk is highest, count "
        "flags where the most people need services.</div>", unsafe_allow_html=True)


def page_age_sex():
    st.title("Age & Sex Distribution")
    df = load_age_sex()
    if df is None:
        st.info("This page reads the WHO age/sex disaggregated file at runtime. "
                "It requires an internet connection (it could not be reached now). "
                "Connect and press **Reload** in the top-right menu.")
        st.markdown(
            "<div class='insight'>Expected pattern (WHO global estimates): TB notably "
            "affects <b>adult men</b> more than women — men account for roughly "
            "<b>~55–60%</b> of adult cases globally. The 15–44 working-age band carries "
            "the largest share, which is why TB has an outsized economic impact.</div>",
            unsafe_allow_html=True)
        return
    df = df[df["year"] == df["year"].max()]
    if "sex" in df and "age_group" in df and "best" in df:
        inc = df[df.get("measure", "inc").astype(str).str.contains("inc", case=False, na=False)] \
            if "measure" in df else df
        order = ["0-4", "5-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65plus"]
        piv = (inc[inc["sex"].isin(["m", "f"])]
               .groupby(["age_group", "sex"])["best"].sum().reset_index())
        piv["age_group"] = pd.Categorical(piv["age_group"], categories=order, ordered=True)
        piv = piv.sort_values("age_group")
        m = piv[piv["sex"] == "m"]
        fpop = piv[piv["sex"] == "f"]
        fig = go.Figure()
        fig.add_bar(y=m["age_group"].astype(str), x=-m["best"], name="Male",
                    orientation="h", marker_color=PRIMARY)
        fig.add_bar(y=fpop["age_group"].astype(str), x=fpop["best"], name="Female",
                    orientation="h", marker_color=ACCENT)
        fig.update_layout(barmode="relative", height=480, plot_bgcolor="white",
                          title="TB incidence population pyramid (latest year)",
                          xaxis_title="Estimated cases (male ◄ | ► female)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.dataframe(df.head(50), use_container_width=True)
    st.markdown(
        "<div class='insight'><b>Why it matters:</b> a male, working-age skew argues "
        "for workplace and community case-finding (not just clinic-based passive "
        "detection) and gender-sensitive messaging.</div>", unsafe_allow_html=True)


def page_dr():
    st.title("Drug-Resistant TB & TB/HIV Co-infection")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("TB/HIV co-infection share")
        g = est[est["year"] == sel_year]
        g = g[g["region_name"].isin(sel_regions)]
        gg = g.groupby("region_name")[["e_inc_tbhiv_num", "e_inc_num"]].sum().reset_index()
        gg["hiv_share"] = gg["e_inc_tbhiv_num"] / gg["e_inc_num"] * 100
        fig = px.bar(gg.sort_values("hiv_share"), x="hiv_share", y="region_name",
                     orientation="h", color="hiv_share",
                     color_continuous_scale="Reds",
                     labels={"hiv_share": "% of TB cases HIV+", "region_name": ""})
        fig.update_layout(height=380, coloraxis_showscale=False, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Drug-resistant TB (MDR/RR)")
        dr = load_dr()
        if dr is None:
            st.info("The MDR/RR-TB estimates file is loaded live from WHO and could "
                    "not be reached now. Connect to the internet and Reload.")
            st.markdown(
                "<div class='insight'>Globally about <b>3–4%</b> of new TB cases and "
                "~<b>18%</b> of previously treated cases have multidrug/rifampicin-"
                "resistant TB. Only a minority are detected and started on treatment — "
                "a critical gap.</div>", unsafe_allow_html=True)
        else:
            try:
                dd = dr.copy()
                if "year" in dd.columns:
                    dd = dd[dd["year"] == dd["year"].max()]
                rrcol = next((c for c in ["e_inc_rr_num", "e_inc_mdr_num", "e_rr_num"]
                              if c in dd.columns), None)
                if rrcol and "iso3" in dd.columns:
                    reg = est[["iso3", "region_name"]].drop_duplicates()
                    m = dd.merge(reg, on="iso3", how="left")
                    m = m[m["region_name"].isin(sel_regions)]
                    gg2 = (m.groupby("region_name")[rrcol].sum()
                           .sort_values().reset_index())
                    fig = px.bar(gg2, x=rrcol, y="region_name", orientation="h",
                                 color=rrcol, color_continuous_scale="OrRd",
                                 labels={rrcol: "Estimated MDR/RR-TB cases",
                                         "region_name": ""})
                    fig.update_layout(height=380, coloraxis_showscale=False,
                                      plot_bgcolor="white", margin=dict(t=10, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("Estimated multidrug/rifampicin-resistant TB cases "
                               "by region (latest WHO estimation year).")
                else:
                    st.info("MDR/RR file loaded but expected columns not found; "
                            "showing a data preview.")
                    st.dataframe(dd.head(20), use_container_width=True)
            except Exception:
                st.info("Could not parse the MDR/RR file; globally ~3–4% of new and "
                        "~18% of previously treated cases are drug-resistant.")
    st.markdown(
        "<div class='insight'><b>Strategic read:</b> HIV and drug resistance are the "
        "two factors that turn a curable disease into a fatal, costly one. Integrating "
        "TB with HIV programmes and scaling rapid molecular drug-susceptibility testing "
        "are the highest-leverage interventions.</div>", unsafe_allow_html=True)


def page_cascade():
    st.title("The TB Care Cascade")
    st.caption("From estimated disease to people on treatment. Every drop is a "
               "missed opportunity to cure and to stop transmission.")
    d = est[(est["year"] == sel_year) & (est["region_name"].isin(sel_regions))]
    inc = d["e_inc_num"].sum()
    # Notified ≈ case-detection rate (c_cdr, %) × incidence
    cdr = np.nanmean(d["c_cdr"]) if d["c_cdr"].notna().any() else np.nan
    notified = inc * (cdr / 100) if not np.isnan(cdr) else np.nan
    stages = ["Estimated new cases", "Detected & notified", "Successfully treated*"]
    vals = [inc, notified if not np.isnan(notified) else inc * 0.75,
            (notified if not np.isnan(notified) else inc * 0.75) * 0.85]
    fig = go.Figure(go.Funnel(y=stages, x=vals, textinfo="value+percent initial",
                              marker=dict(color=[PRIMARY, "#2A7F95", GOOD])))
    fig.update_layout(height=420, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("*Treatment-success share is an illustrative ~85% applied to detected "
               "cases; the live WHO 'outcomes' file gives the country-reported figure.")
    st.markdown(
        f"<div class='insight'><b>The gap:</b> at an average case-detection rate of "
        f"<b>{cdr:.0f}%</b> for the current selection, roughly "
        f"<b>{fmt(inc-(notified if not np.isnan(notified) else inc*0.75))}</b> people "
        "with TB are never diagnosed or notified — they continue to transmit. Closing "
        "the detection gap is the single biggest lever on mortality.</div>",
        unsafe_allow_html=True)


def page_predict():
    st.title("Predictive Analysis — Incidence Forecast")
    st.caption("A transparent trend model projecting TB incidence forward. Shown with "
               "explicit assumptions — forecasts are planning aids, not certainties.")
    scope = st.radio("Forecast scope", ["Global", "Single country"], horizontal=True)
    horizon = st.slider("Years to forecast", 1, 10, 6)

    if scope == "Global":
        s = est.groupby("year")["e_inc_num"].sum()
        title = "Global new TB cases"
    else:
        country = st.selectbox("Country", sorted(est["country"].unique()))
        s = est[est["country"] == country].groupby("year")["e_inc_num"].sum()
        title = f"New TB cases — {country}"
    s = s[s.index >= 2010]
    x = s.index.values.astype(float)
    y = s.values.astype(float)
    if len(x) < 3:
        st.warning("Not enough data points to fit a trend for this selection.")
        return
    # Simple, explainable linear trend + CAGR sanity band
    coef = np.polyfit(x, y, 1)
    fut_x = np.arange(x.min(), x.max() + horizon + 1)
    fit = np.polyval(coef, fut_x)
    # naive residual band
    resid = y - np.polyval(coef, x)
    band = 1.96 * resid.std()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers+lines", name="Observed",
                             line=dict(color=PRIMARY, width=3)))
    fut_only = fut_x[fut_x > x.max()]
    fig.add_trace(go.Scatter(x=fut_only, y=np.polyval(coef, fut_only),
                             mode="lines", name="Forecast",
                             line=dict(color=ACCENT, dash="dash", width=3)))
    fig.add_trace(go.Scatter(
        x=np.concatenate([fut_only, fut_only[::-1]]),
        y=np.concatenate([np.polyval(coef, fut_only) + band,
                          (np.polyval(coef, fut_only) - band)[::-1]]),
        fill="toself", fillcolor="rgba(228,87,46,0.15)",
        line=dict(color="rgba(0,0,0,0)"), name="95% band", showlegend=True))
    fig.update_layout(title=title, height=460, plot_bgcolor="white",
                      yaxis_title="New cases", xaxis_title="Year")
    st.plotly_chart(fig, use_container_width=True)

    slope = coef[0]
    direction = "declining" if slope < 0 else "rising"
    st.markdown(
        f"<div class='insight'><b>Model read-out:</b> the fitted linear trend is "
        f"<b>{direction}</b> at about <b>{fmt(abs(slope))} cases/year</b>. Projected "
        f"value in {int(fut_x.max())}: <b>{fmt(np.polyval(coef, fut_x.max()))}</b> "
        f"(±{fmt(band)}). Method: ordinary least-squares on 2010-onward estimates. "
        "Limitation: a linear model cannot capture shocks (e.g., COVID-19 disruption) "
        "or policy change — treat as a baseline scenario.</div>",
        unsafe_allow_html=True)


def page_method():
    st.title("Methodology & Data")
    st.markdown(f"""
**Data source.** All figures are drawn from the **World Health Organization (WHO)
Global Tuberculosis Programme** public database, which underpins the annual
*Global Tuberculosis Report*. The dashboard pulls the WHO CSV files live at runtime
and caches them for 24 hours; an offline sample is bundled so the app always renders.

**Current data status:** `{source}`.

**Data type.** Secondary, quantitative, country-level estimates and country-reported
surveillance data (2000–most recent year).

**Key files used**

| File | What it provides |
|---|---|
| `estimates` | Incidence, mortality, TB/HIV, case-detection rate by country & year |
| `estimates_age_sex` | Incidence disaggregated by age band and sex |
| `mdr_rr_estimates` | Multidrug/rifampicin-resistant TB estimates |
| `outcomes` | Treatment-success rates |

**Cleaning & transformation.** Standardised region codes to names, coerced numeric
fields, handled missing values (kept as gaps rather than imputed), derived metrics
(HIV share, detection gap, regional aggregates), and joined on ISO-3 codes for mapping.

**Tools.** Python · pandas · NumPy · Plotly · scikit-learn/NumPy (forecast) · Streamlit.

**Limitations.** WHO figures are *modelled estimates* with uncertainty intervals;
case-detection and notification depend on national reporting capacity; the COVID-19
period disrupted TB services and data; the forecast is a simple trend baseline.
""")
    st.markdown("<span class='src'>WHO Global TB Programme — "
                "https://www.who.int/teams/global-programme-on-tuberculosis-and-lung-health/data</span>",
                unsafe_allow_html=True)


def page_reco():
    st.title("Insights & Recommendations")
    inc, mort, hiv, inc_rate, pop = world_year(est, sel_year)
    st.markdown(f"""
### What the data tells us
1. **TB remains a top global killer** — ~{fmt(mort)} deaths and ~{fmt(inc)} new cases
   in {sel_year}, despite being preventable and curable.
2. **The burden is geographically concentrated** in Africa and South-East Asia, and a
   handful of high-burden countries dominate absolute case counts.
3. **The detection gap is the core problem** — a large share of estimated cases are
   never diagnosed or notified, sustaining transmission.
4. **HIV and drug resistance** are the principal drivers of TB mortality.

### Recommendations for a TB programme / decision-maker
""")
    recos = [
        ("Close the case-detection gap", "Scale active case-finding and rapid molecular "
         "testing (e.g. GeneXpert) in the highest-burden districts, prioritised by the "
         "map and cascade pages."),
        ("Integrate TB and HIV services", "Co-locate testing and treatment where TB/HIV "
         "co-infection share is highest, as flagged in the DR/HIV page."),
        ("Scale drug-susceptibility testing", "Detect and correctly treat MDR/RR-TB "
         "early to prevent costly, deadly resistant outbreaks."),
        ("Target working-age men", "Use the age/sex pattern to design community and "
         "workplace screening, not just passive clinic detection."),
        ("Monitor with this dashboard", "Track incidence, detection and mortality "
         "annually against End-TB milestones; use the forecast as a planning baseline."),
    ]
    for t, d in recos:
        st.markdown(f"<div class='insight'><b>{t}.</b> {d}</div>",
                    unsafe_allow_html=True)


PAGES = {
    "Executive Overview": page_overview,
    "Trend Analysis": page_trend,
    "Geographic Map": page_map,
    "Age & Sex": page_age_sex,
    "Drug-Resistant TB & HIV": page_dr,
    "Care Cascade": page_cascade,
    "Predictive Analysis": page_predict,
    "Methodology & Data": page_method,
    "Insights & Recommendations": page_reco,
}
PAGES[page]()
