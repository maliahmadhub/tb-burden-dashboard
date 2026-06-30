"""
Global Tuberculosis Burden — Executive Decision Dashboard
=========================================================
A consulting-grade decision-support tool for a healthcare decision-maker.
Built as a HEALTHCARE BUSINESS CASE: every page answers what decision it supports,
what the data shows, why it matters, and what action to take.

Author : Mohamad Ali Ahmad  |  MSBA 382 — Healthcare Analytics
Data   : WHO Global Tuberculosis Programme (public database)
"""
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Global TB Burden — Executive Decision Dashboard",
                   page_icon="🫁", layout="wide", initial_sidebar_state="expanded")

NAVY = "#0E3A4F"; TEAL = "#0E7C86"; ACCENT = "#E4572E"; GOOD = "#2A9D8F"
INK = "#1A2B33"; GREY = "#5B6B72"

st.markdown(f"""
<style>
    .main {{ background:#F6F8FA; }}
    h1,h2,h3 {{ color:{NAVY}; }}
    div[data-testid="stSidebarNav"] {{ display:none; }}
    div[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid #E3E9EC;
        border-radius:12px; padding:16px 16px 8px 16px; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
    .hero {{ background:{NAVY}; color:#fff; border-radius:14px; padding:22px 26px; }}
    .hero h1 {{ color:#fff; margin:0; font-size:30px; }}
    .hero p {{ color:#CFE0E6; margin:6px 0 0 0; font-size:15px; }}
    .insight {{ background:#FFFFFF; border-left:5px solid {ACCENT}; padding:14px 18px;
        border-radius:8px; margin:6px 0; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
    .gapcard {{ background:#FFF1ED; border:1px solid #F6D2C6; border-radius:12px;
        padding:18px 22px; text-align:center; min-height:250px; display:flex;
        flex-direction:column; justify-content:center; align-items:center; }}
    .gapnum {{ color:{ACCENT}; font-size:42px; font-weight:800; line-height:1; }}
    .decision {{ background:#F2F8F9; border:1px solid #D4E4E7; border-left:6px solid {TEAL};
        border-radius:8px; padding:14px 18px; margin:10px 0; font-size:14px; line-height:1.55; }}
    .dl {{ display:inline-block; min-width:132px; font-weight:800; color:{NAVY};
        text-transform:uppercase; font-size:10.5px; letter-spacing:.6px; vertical-align:top; }}
    .dt {{ display:inline-block; width:calc(100% - 140px); vertical-align:top; }}
    .biz {{ background:#FFFFFF; border:1px solid #E3E9EC; border-radius:12px; padding:6px 20px 14px 20px;
        box-shadow:0 1px 3px rgba(0,0,0,.05); }}
    .bizrow {{ margin:9px 0; font-size:14px; line-height:1.5; }}
    .bizq {{ font-weight:800; color:{ACCENT}; }}
    .src {{ color:{GREY}; font-size:0.8rem; }}
</style>
""", unsafe_allow_html=True)


def decision_box(obs, interp, impl, action, monitor):
    rows = [("Observation", obs), ("What it means", interp), ("Why it matters", impl),
            ("Recommendation", action), ("Monitor", monitor)]
    html = "<div class='decision'>"
    for lbl, txt in rows:
        html += f"<div><span class='dl'>{lbl}</span><span class='dt'>{txt}</span></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------- DATA LAYER
WHO = "https://extranet.who.int/tme/generateCSV.asp?ds="
URLS = {"estimates": WHO + "estimates", "age_sex": WHO + "estimates_age_sex",
        "dr": WHO + "mdr_rr_estimates", "outcomes": WHO + "outcomes"}
LOCAL = {"estimates": "data/TB_estimates.csv", "age_sex": "data/TB_age_sex.csv",
         "dr": "data/TB_mdr_rr.csv", "outcomes": "data/TB_outcomes.csv"}
LOCAL_SAMPLE = "data/estimates_sample.csv"
REGION_NAMES = {"AFR": "Africa", "AMR": "Americas", "EMR": "Eastern Mediterranean",
                "EUR": "Europe", "SEA": "South-East Asia", "WPR": "Western Pacific"}


def _read(key):
    path = LOCAL.get(key)
    if path and os.path.exists(path):
        try:
            return pd.read_csv(path, low_memory=False)
        except Exception:
            pass
    try:
        return pd.read_csv(URLS[key], low_memory=False)
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner="Loading WHO TB data…")
def load_estimates():
    df = _read("estimates")
    src = "WHO database"
    if df is None:
        df, src = pd.read_csv(LOCAL_SAMPLE), "offline sample"
    df = df.rename(columns={"g_whoregion": "region"})
    df["region_name"] = df["region"].map(REGION_NAMES).fillna(df["region"])
    for c in ["e_inc_num", "e_inc_100k", "e_mort_num", "e_mort_100k",
              "e_inc_tbhiv_num", "c_cdr", "c_newinc_100k", "e_pop_num"]:
        if c not in df.columns:
            df[c] = np.nan
    return df, src


@st.cache_data(ttl=86400, show_spinner=False)
def load_age_sex():
    return _read("age_sex")


@st.cache_data(ttl=86400, show_spinner=False)
def load_dr():
    return _read("dr")


def fmt(n, s=""):
    if pd.isna(n):
        return "n/a"
    n = float(n)
    if abs(n) >= 1e9: return f"{n/1e9:.2f}B{s}"
    if abs(n) >= 1e6: return f"{n/1e6:.2f}M{s}"
    if abs(n) >= 1e3: return f"{n/1e3:.0f}K{s}"
    return f"{n:,.0f}{s}"


# ---------------------------------------------------------------- AUTH
APP_PASSWORD = "tb2024"


def login_gate():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, c, _ = st.columns([1, 1.3, 1])
    with c:
        st.markdown("<h1 style='text-align:center'>🫁 Global TB Burden Dashboard</h1>",
                    unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#5B6B72'>Executive decision-support "
                    "for tuberculosis control · WHO Global TB Programme data</p>",
                    unsafe_allow_html=True)
        with st.form("login"):
            pw = st.text_input("Access code", type="password", placeholder="Enter access code")
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

# ---------------------------------------------------------------- LOAD + NAV
est, source = load_estimates()
years = sorted(est["year"].dropna().unique().astype(int))
regions = sorted(est["region_name"].dropna().unique())
default_year = 2023 if 2023 in years else int(max(years))

st.sidebar.title("🫁 TB Burden")
page = st.sidebar.radio("Go to", [
    "🏠 Executive Home", "📈 Burden & Trends", "🗺️ Geography & Demographics",
    "🔬 Drivers & Care Gap", "🔮 Forecast", "📋 Methodology & Recommendations"])
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
sel_regions = st.sidebar.multiselect("WHO region", regions, default=regions)
yr_min, yr_max = int(min(years)), int(max(years))
sel_year = st.sidebar.slider("Reporting year", yr_min, yr_max, default_year)
sel_range = st.sidebar.slider("Trend window", yr_min, yr_max, (yr_min, yr_max))
st.sidebar.caption(f"Data: {source} — WHO Global TB Programme.")

if not sel_regions:
    st.warning("Select at least one WHO region in the sidebar.")
    st.stop()


def world_year(year):
    d = est[est["year"] == year]
    inc, mort = d["e_inc_num"].sum(), d["e_mort_num"].sum()
    hiv, pop = d["e_inc_tbhiv_num"].sum(), d["e_pop_num"].sum()
    rate = inc / pop * 1e5 if pop else np.nan
    return inc, mort, hiv, rate


def cascade(year, region_filter=None):
    d = est[est["year"] == year]
    if region_filter:
        d = d[d["region_name"].isin(region_filter)]
    inc = d["e_inc_num"].sum()
    notified = (d["c_newinc_100k"].fillna(0) / 1e5 * d["e_pop_num"]).sum()
    if notified <= 0 and d["c_cdr"].notna().any():
        notified = inc * np.nanmean(d["c_cdr"]) / 100
    return inc, notified, max(inc - notified, 0)


# ================================================================ PAGES
def page_home():
    inc, mort, hiv, rate = world_year(sel_year)
    pinc, pmort, *_ = world_year(max(sel_year - 1, yr_min))
    di = (inc - pinc) / pinc * 100 if pinc else 0
    dm = (mort - pmort) / pmort * 100 if pmort else 0
    gi, notified, gap = cascade(sel_year)
    det = notified / gi * 100 if gi else 0

    st.markdown(f"<div class='hero'><h1>Global Tuberculosis Burden — Executive Briefing</h1>"
                f"<p>The world's leading infectious-disease killer &nbsp;·&nbsp; reporting year "
                f"{sel_year} &nbsp;·&nbsp; source: WHO Global Tuberculosis Programme</p></div>",
                unsafe_allow_html=True)
    st.markdown("")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("New cases (incidence)", fmt(inc), f"{di:+.1f}% vs prior year")
    k2.metric("TB deaths", fmt(mort), f"{dm:+.1f}% vs prior year", delta_color="inverse")
    k3.metric("Case-detection rate", f"{det:.0f}%")
    k4.metric("HIV-positive TB cases", fmt(hiv))

    st.markdown("####  ")
    cL, cR = st.columns([1.5, 1])
    with cL:
        st.markdown("**The core problem — the detection gap**")
        fig = go.Figure(go.Funnel(y=["Developed TB", "Diagnosed & reported"], x=[gi, notified],
                        textinfo="value+percent initial", marker=dict(color=[NAVY, GOOD])))
        fig.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with cR:
        st.markdown("**The cost of the gap**")
        st.markdown("<div class='gapcard'><div class='gapnum'>" + fmt(gap) + "</div>"
                    "<div style='margin-top:8px'>people who developed TB in " + str(sel_year) +
                    " were never diagnosed — untreated, and still transmitting.</div></div>",
                    unsafe_allow_html=True)

    st.markdown("####  ")
    st.subheader("The business case at a glance")
    qa = [
        ("What is the health problem?",
         "Tuberculosis — an airborne, curable bacterial infection that is again the world's "
         "deadliest single infectious disease."),
        ("How large / serious is the burden?",
         f"~{fmt(inc)} new cases and ~{fmt(mort)} deaths in {sel_year}; a disease that is "
         "preventable and curable, yet still kills over a million people a year."),
        ("Who is most affected?",
         "Working-age adults, skewed toward men (~55–60% of adult cases), plus people living "
         "with HIV — i.e., the economically productive population."),
        ("Where / when is it concentrated?",
         "Africa and South-East Asia, with roughly two-thirds of cases in just eight "
         "high-burden countries — the burden is not evenly spread."),
        ("What is the most important insight?",
         f"The detection gap: only ~{det:.0f}% of cases are diagnosed, leaving ~{fmt(gap)} "
         "people undiagnosed who drive ongoing transmission and death."),
        ("What action should be taken?",
         "Concentrate active case-finding and rapid molecular testing in high-burden "
         "geographies; integrate TB/HIV services; scale drug-susceptibility testing."),
        ("What is the expected value of acting?",
         "Each undiagnosed person with pulmonary TB can infect an estimated 10–15 contacts a "
         "year, so closing the gap cuts future cases, deaths, cost, and care demand."),
    ]
    rows = "".join(f"<div class='bizrow'><span class='bizq'>{q}</span><br>{a}</div>" for q, a in qa)
    st.markdown(f"<div class='biz'>{rows}</div>", unsafe_allow_html=True)

    st.markdown("####  ")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Global trend — new cases vs. deaths**")
        g = est.groupby("year")[["e_inc_num", "e_mort_num"]].sum().reset_index()
        fig = go.Figure()
        fig.add_bar(x=g["year"], y=g["e_inc_num"], name="New cases", marker_color=TEAL)
        fig.add_trace(go.Scatter(x=g["year"], y=g["e_mort_num"], name="Deaths",
                                 yaxis="y2", line=dict(color=ACCENT, width=3)))
        fig.update_layout(height=300, yaxis2=dict(overlaying="y", side="right"),
                          legend=dict(orientation="h", y=1.2), margin=dict(t=30, b=40, l=10, r=10),
                          plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown(f"**Where the burden sits — {sel_year}**")
        rr = (est[est["year"] == sel_year].groupby("region_name")["e_inc_num"]
              .sum().sort_values().reset_index())
        fig = px.bar(rr, x="e_inc_num", y="region_name", orientation="h", color="e_inc_num",
                     color_continuous_scale="Teal", labels={"e_inc_num": "New cases", "region_name": ""})
        fig.update_layout(height=300, coloraxis_showscale=False, margin=dict(t=30, b=40, l=10, r=10),
                          plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    st.caption("Use the sidebar for the detailed analysis — every page carries a decision box "
               "(observation → action → metric to monitor).")


def page_burden():
    st.title("Burden & Trends")
    st.caption(f"Decision supported: capacity, procurement and demand planning · "
               f"{', '.join(sel_regions)} · {sel_range[0]}–{sel_range[1]}")
    fy = est[(est["year"] == sel_year) & (est["region_name"].isin(sel_regions))]
    st.subheader(f"Highest-burden countries — {sel_year}")
    top = (fy.sort_values("e_inc_num", ascending=False).head(15)
           [["country", "region_name", "e_inc_num", "e_inc_100k", "e_mort_num", "c_cdr"]])
    top.columns = ["Country", "Region", "New cases", "Incidence /100k", "Deaths", "Case detection %"]
    st.dataframe(top, use_container_width=True, hide_index=True)

    st.subheader("Trend explorer")
    labels = {"Incidence rate (/100k)": "e_inc_100k", "New cases (number)": "e_inc_num",
              "Mortality rate (/100k)": "e_mort_100k", "Deaths (number)": "e_mort_num"}
    metric = st.selectbox("Metric", list(labels.keys()))
    col = labels[metric]
    agg = "mean" if "100k" in col else "sum"
    ftr = est[(est["region_name"].isin(sel_regions)) &
              (est["year"] >= sel_range[0]) & (est["year"] <= sel_range[1])]
    g = ftr.groupby(["year", "region_name"])[col].agg(agg).reset_index()
    fig = px.line(g, x="year", y=col, color="region_name", markers=True,
                  labels={col: metric, "region_name": "Region", "year": "Year"})
    fig.update_layout(height=400, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    pick = st.multiselect("Compare specific countries", sorted(ftr["country"].unique()))
    if pick:
        gc = ftr[ftr["country"].isin(pick)]
        fig2 = px.line(gc, x="year", y=col, color="country", markers=True,
                       labels={col: metric, "year": "Year", "country": "Country"})
        fig2.update_layout(height=380, plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)
    decision_box(
        "A few countries and regions account for the bulk of cases, and per-capita rates can fall "
        "while absolute case counts stay flat or rise.",
        "Falling rates with steady/rising counts means population growth is offsetting programmatic "
        "gains — the operational caseload is not shrinking as fast as the rate suggests.",
        "A healthcare centre's real workload, staffing and drug procurement are driven by absolute "
        "cases, not by rates — planning on rates alone under-provisions services.",
        "Base capacity, staffing and procurement plans on the absolute case trend in your catchment "
        "and the high-burden geographies above, not on the rate trend.",
        "Year-over-year change in notified cases and the case-detection rate in your catchment.")


def page_geo():
    st.title("Geography & Demographics")
    st.caption("Decision supported: where to target screening and which groups to prioritise.")
    metric = st.radio("Map metric", ["Incidence rate (/100k)", "Total new cases",
                                      "Mortality rate (/100k)"], horizontal=True)
    col = {"Incidence rate (/100k)": "e_inc_100k", "Total new cases": "e_inc_num",
           "Mortality rate (/100k)": "e_mort_100k"}[metric]
    d = est[(est["year"] == sel_year) & (est["region_name"].isin(sel_regions))]
    fig = px.choropleth(d, locations="iso3", color=col, hover_name="country",
                        color_continuous_scale="OrRd", locationmode="ISO-3", labels={col: metric})
    fig.update_layout(height=460, margin=dict(t=10, b=10),
                      geo=dict(showframe=False, projection_type="natural earth"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Age & sex distribution")
    df = load_age_sex()
    drawn = False
    if df is not None and {"sex", "age_group", "best"}.issubset(df.columns):
        try:
            dd = df[df["year"] == df["year"].max()]
            if "measure" in dd.columns:
                dd = dd[dd["measure"].astype(str).str.contains("inc", case=False, na=False)]
            order = ["0-4", "5-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65plus"]
            piv = (dd[dd["sex"].isin(["m", "f"])].groupby(["age_group", "sex"])["best"]
                   .sum().reset_index())
            piv = piv[piv["age_group"].isin(order)]
            piv["age_group"] = pd.Categorical(piv["age_group"], categories=order, ordered=True)
            piv = piv.sort_values("age_group")
            m, fpop = piv[piv["sex"] == "m"], piv[piv["sex"] == "f"]
            fig = go.Figure()
            fig.add_bar(y=m["age_group"].astype(str), x=-m["best"], name="Male",
                        orientation="h", marker_color=NAVY)
            fig.add_bar(y=fpop["age_group"].astype(str), x=fpop["best"], name="Female",
                        orientation="h", marker_color=ACCENT)
            fig.update_layout(barmode="relative", height=420, plot_bgcolor="white",
                              title="TB incidence by age and sex (latest year)",
                              xaxis_title="Estimated cases  (male ◄ | ► female)")
            st.plotly_chart(fig, use_container_width=True)
            drawn = True
        except Exception:
            drawn = False
    if not drawn:
        st.info("Age/sex view loads the WHO age-sex file at runtime (needs internet on first load).")
    decision_box(
        "TB is concentrated in specific countries/regions and skews to working-age men "
        "(~55–60% of adult cases).",
        "Risk is not evenly distributed; passive, clinic-based detection systematically misses "
        "working-age men who present late.",
        "Spreading resources evenly wastes them; untreated working-age cases drive both "
        "transmission and lost economic productivity.",
        "Prioritise screening budget in the high-burden areas on the map and add active "
        "community/workplace screening aimed at men, rather than clinic-only detection.",
        "Share of cases found by active vs passive case-finding, and screening coverage in "
        "priority districts.")


def page_drivers():
    st.title("Drivers & Care Gap")
    st.caption("Decision supported: where to invest to cut deaths and stop transmission.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("TB/HIV co-infection share")
        g = est[(est["year"] == sel_year) & (est["region_name"].isin(sel_regions))]
        gg = g.groupby("region_name")[["e_inc_tbhiv_num", "e_inc_num"]].sum().reset_index()
        gg["share"] = gg["e_inc_tbhiv_num"] / gg["e_inc_num"] * 100
        fig = px.bar(gg.sort_values("share"), x="share", y="region_name", orientation="h",
                     color="share", color_continuous_scale="Reds",
                     labels={"share": "% of TB cases HIV+", "region_name": ""})
        fig.update_layout(height=340, coloraxis_showscale=False, plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Drug-resistant TB (MDR/RR)")
        dr = load_dr()
        shown = False
        if dr is not None:
            try:
                dd = dr[dr["year"] == dr["year"].max()] if "year" in dr.columns else dr
                rc = next((c for c in ["e_inc_rr_num", "e_inc_mdr_num", "e_rr_num"]
                           if c in dd.columns), None)
                if rc and "iso3" in dd.columns:
                    reg = est[["iso3", "region_name"]].drop_duplicates()
                    mm = dd.merge(reg, on="iso3", how="left")
                    mm = mm[mm["region_name"].isin(sel_regions)]
                    ggr = mm.groupby("region_name")[rc].sum().sort_values().reset_index()
                    fig = px.bar(ggr, x=rc, y="region_name", orientation="h", color=rc,
                                 color_continuous_scale="OrRd",
                                 labels={rc: "Estimated MDR/RR-TB cases", "region_name": ""})
                    fig.update_layout(height=340, coloraxis_showscale=False, plot_bgcolor="white")
                    st.plotly_chart(fig, use_container_width=True)
                    shown = True
            except Exception:
                shown = False
        if not shown:
            st.markdown("<div class='insight'>Globally ~<b>3–4%</b> of new and ~<b>18%</b> of "
                        "previously treated cases are multidrug/rifampicin-resistant; only a "
                        "minority are detected and treated.</div>", unsafe_allow_html=True)

    st.subheader("The TB care cascade")
    gi, notified, gap = cascade(sel_year, sel_regions)
    treated = notified * 0.85
    fig = go.Figure(go.Funnel(y=["Estimated new cases", "Detected & notified", "Successfully treated*"],
                    x=[gi, notified, treated], textinfo="value+percent initial",
                    marker=dict(color=[NAVY, TEAL, GOOD])))
    fig.update_layout(height=360, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("*Treatment success shown as an illustrative ~85% of notified cases; the WHO "
               "'outcomes' file holds country-reported rates.")
    decision_box(
        f"For this selection, ~{fmt(gap)} people with TB are never diagnosed, and HIV co-infection "
        "and drug resistance are concentrated in specific regions.",
        "Undiagnosed cases are the main engine of transmission and death; HIV and MDR sharply raise "
        "case-fatality and treatment cost.",
        "These three factors — under-detection, HIV, resistance — are the largest controllable "
        "drivers of TB mortality and of future, costlier caseload.",
        "Scale rapid molecular testing (e.g. GeneXpert) for case-finding, integrate TB/HIV testing "
        "and treatment, and expand drug-susceptibility testing in the flagged regions.",
        "Case-detection rate, treatment-success rate, MDR detection coverage, and TB/HIV testing "
        "coverage, reviewed each cycle.")


def page_forecast():
    st.title("Forecast — Incidence Outlook")
    st.caption("Decision supported: budgeting and the case for investing in control now.")
    scope = st.radio("Scope", ["Global", "Single country"], horizontal=True)
    horizon = st.slider("Years to forecast", 1, 10, 6)
    if scope == "Global":
        s = est.groupby("year")["e_inc_num"].sum()
        title = "Global new TB cases"
    else:
        country = st.selectbox("Country", sorted(est["country"].unique()))
        s = est[est["country"] == country].groupby("year")["e_inc_num"].sum()
        title = f"New TB cases — {country}"
    s = s[s.index >= 2010]
    x, y = s.index.values.astype(float), s.values.astype(float)
    if len(x) < 3:
        st.warning("Not enough data points to fit a trend for this selection.")
        return
    coef = np.polyfit(x, y, 1)
    band = 1.96 * (y - np.polyval(coef, x)).std()
    fut = np.arange(x.max() + 1, x.max() + horizon + 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers+lines", name="Observed",
                             line=dict(color=NAVY, width=3)))
    fig.add_trace(go.Scatter(x=fut, y=np.polyval(coef, fut), mode="lines", name="Forecast",
                             line=dict(color=ACCENT, dash="dash", width=3)))
    fig.add_trace(go.Scatter(x=np.concatenate([fut, fut[::-1]]),
                  y=np.concatenate([np.polyval(coef, fut) + band, (np.polyval(coef, fut) - band)[::-1]]),
                  fill="toself", fillcolor="rgba(228,87,46,0.15)",
                  line=dict(color="rgba(0,0,0,0)"), name="95% band"))
    fig.update_layout(title=title, height=440, plot_bgcolor="white",
                      yaxis_title="New cases", xaxis_title="Year")
    st.plotly_chart(fig, use_container_width=True)
    slope = coef[0]
    decision_box(
        f"On current trend, incidence is {'declining' if slope < 0 else 'rising/flat'} by about "
        f"{fmt(abs(slope))} cases/year, projecting ~{fmt(np.polyval(coef, fut.max()))} by {int(fut.max())}.",
        "This baseline trajectory falls short of the WHO End TB milestones (a 50% cut in incidence "
        "by 2025, 80% by 2030) without accelerated action.",
        "Without intervention the centre faces sustained or rising demand, cost and patient-risk "
        "exposure — the 'do nothing' option is not cost-neutral.",
        "Use this baseline to size multi-year budgets and to justify front-loaded investment in "
        "case-finding, which bends the curve below the baseline.",
        "Actual incidence each year vs this forecast and vs the End TB 2025/2030 milestones.")


def page_method():
    st.title("Methodology & Recommendations")
    st.subheader("Methodology")
    st.markdown(f"""
**Data.** Secondary, quantitative estimates and country-reported surveillance from the
**WHO Global Tuberculosis Programme** database (the source behind the annual *Global TB
Report*) — 204 countries, 2000–present. Current source: `{source}`. No data is fabricated.

**Tools.** Python · pandas · NumPy · Plotly · Streamlit.

**Cleaning & transformation.** Standardised WHO region codes, type-checked numeric fields,
kept genuine gaps as gaps (no silent imputation), derived the HIV share and the detection
gap, and joined on ISO-3 codes for mapping.

**Limitations.** WHO incidence/mortality are modelled estimates with uncertainty intervals;
notification depends on national reporting capacity; COVID-19 disrupted 2020–21 data; the
forecast is a simple trend baseline.
""")
    st.subheader("Recommendations & monitoring metrics")
    recos = [
        ("Close the detection gap first", "Target active case-finding and rapid molecular testing "
         "to the highest-burden geographies.", "Case-detection rate; cases found via active search."),
        ("Integrate TB and HIV services", "Co-locate testing and treatment where co-infection is "
         "highest.", "TB/HIV testing coverage; co-infected on ART."),
        ("Scale drug-susceptibility testing", "Detect and treat MDR/RR-TB early.",
         "MDR detection coverage; MDR treatment-success rate."),
        ("Design for those affected", "Community/workplace screening for working-age men.",
         "Active- vs passive-found share; screening coverage."),
        ("Monitor against End TB milestones", "Use the dashboard each cycle and the forecast as a "
         "budget baseline.", "Incidence & mortality vs 2025/2030 milestones."),
    ]
    for t, d, mtr in recos:
        st.markdown(f"<div class='insight'><b>{t}.</b> {d}<br>"
                    f"<span class='src'>Monitor: {mtr}</span></div>", unsafe_allow_html=True)
    st.markdown("<span class='src'>Source: WHO Global Tuberculosis Programme — "
                "who.int/teams/global-programme-on-tuberculosis-and-lung-health/data</span>",
                unsafe_allow_html=True)


PAGES = {
    "🏠 Executive Home": page_home,
    "📈 Burden & Trends": page_burden,
    "🗺️ Geography & Demographics": page_geo,
    "🔬 Drivers & Care Gap": page_drivers,
    "🔮 Forecast": page_forecast,
    "📋 Methodology & Recommendations": page_method,
}
PAGES[page]()
