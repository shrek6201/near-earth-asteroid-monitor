import os
import math
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh
from streamlit_js_eval import streamlit_js_eval
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Asteroid Tracker",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help":     "https://github.com/shrek6201",
        "Report a bug": "https://github.com/shrek6201",
        "About":        "### ☄️ Asteroid Tracker\nBuilt by [shrek6201](https://github.com/shrek6201) · Powered by NASA NeoWs API",
    }
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    background-color: #06080f;
    color: #c9d1d9;
    font-family: 'Inter', sans-serif;
}
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background-color: #06080f; border-bottom: none; }
/* Hide Streamlit Cloud "View source" GitHub button */
[data-testid="stToolbar"] { display: none !important; }
/* But keep the sidebar collapse toggle visible */
[data-testid="collapsedControl"] { display: flex !important; }
.block-container { padding: 2rem 2.5rem; max-width: 1400px; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #0a0e1a 100%);
    border-right: 1px solid #1c2333;
}
section[data-testid="stSidebar"] .stTextInput input {
    background: #0d1117; border: 1px solid #30363d;
    color: #e6edf3; border-radius: 8px;
}
section[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: white; border: none; border-radius: 8px;
    font-weight: 600; letter-spacing: 0.3px; transition: opacity 0.2s;
}
section[data-testid="stSidebar"] .stButton button:hover { opacity: 0.85; }

.kpi-card {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21262d; border-radius: 16px;
    padding: 20px 24px; position: relative; overflow: hidden; height: 110px;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 16px 16px 0 0;
}
.kpi-card.blue::before  { background: linear-gradient(90deg, #1f6feb, #58a6ff); }
.kpi-card.red::before   { background: linear-gradient(90deg, #da3633, #f85149); }
.kpi-card.green::before { background: linear-gradient(90deg, #238636, #3fb950); }
.kpi-card.amber::before { background: linear-gradient(90deg, #9e6a03, #e3b341); }
.kpi-card.purple::before{ background: linear-gradient(90deg, #6e40c9, #a371f7); }
.kpi-label { font-size:11px; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:#8b949e; margin-bottom:6px; }
.kpi-value { font-size:28px; font-weight:700; color:#e6edf3; line-height:1.1; }
.kpi-sub   { font-size:11px; color:#6e7681; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.section-header {
    font-size:13px; font-weight:600; letter-spacing:1.2px; text-transform:uppercase;
    color:#8b949e; border-bottom:1px solid #21262d; padding-bottom:8px; margin:28px 0 16px 0;
}

.hero {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 50%, #0d1117 100%);
    border: 1px solid #1c2333; border-radius: 20px;
    padding: 36px 40px; margin-bottom: 28px; position: relative; overflow: hidden;
}
.hero::after {
    content: '☄️'; position: absolute; right: 40px; top: 50%;
    transform: translateY(-50%); font-size: 72px; opacity: 0.15;
}
.hero h1 {
    font-size: 32px; font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #a5d6ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 6px 0; line-height: 1.2;
}
.hero p { color: #6e7681; font-size: 14px; margin: 0; }

.chart-card { background:#0d1117; border:1px solid #21262d; border-radius:16px; padding:20px; }

.detail-card {
    background: linear-gradient(135deg, #0d1117, #111827);
    border: 1px solid #21262d; border-radius: 16px; padding: 24px;
}
.detail-row { display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #1c2333; font-size:13px; }
.detail-row:last-child { border-bottom: none; }
.detail-label { color: #8b949e; }
.detail-value { color: #e6edf3; font-weight: 500; }

.threat-bar-wrap { background:#1c2333; border-radius:99px; height:8px; overflow:hidden; margin-top:4px; }
.threat-bar { height:8px; border-radius:99px; }

.record-badge {
    display:inline-block; background:rgba(227,179,65,0.15); color:#e3b341;
    border:1px solid rgba(227,179,65,0.3); border-radius:20px;
    padding:2px 10px; font-size:11px; font-weight:600; margin-left:8px;
}

.hist-delta-pos { color:#3fb950; font-weight:600; }
.hist-delta-neg { color:#f85149; font-weight:600; }

.live-pill {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(63,185,80,0.1); border:1px solid rgba(63,185,80,0.3);
    border-radius:20px; padding:4px 12px; font-size:11px; font-weight:600; color:#3fb950;
}
.live-dot {
    width:7px; height:7px; background:#3fb950; border-radius:50%;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%   { opacity:1; transform:scale(1); }
    50%  { opacity:0.4; transform:scale(0.8); }
    100% { opacity:1; transform:scale(1); }
}
.stDataFrame { border:1px solid #21262d !important; border-radius:12px !important; }
</style>
""", unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
REFRESH_MS = 5 * 60 * 1000
st_autorefresh(interval=REFRESH_MS, key="auto_refresh")

# ── Browser timezone ──────────────────────────────────────────────────────────
browser_tz_str = streamlit_js_eval(
    js_expressions="Intl.DateTimeFormat().resolvedOptions().timeZone", key="browser_tz"
)
try:
    user_tz = ZoneInfo(browser_tz_str) if browser_tz_str else timezone.utc
except ZoneInfoNotFoundError:
    user_tz = timezone.utc
tz_label = browser_tz_str if browser_tz_str else "UTC"

# ── API helpers ───────────────────────────────────────────────────────────────
NASA_FEED = "https://api.nasa.gov/neo/rest/v1/feed"
NASA_NEO  = "https://api.nasa.gov/neo/rest/v1/neo"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_feed(key: str, start: str, end: str) -> dict:
    resp = requests.get(NASA_FEED, params={"start_date": start, "end_date": end, "api_key": key}, timeout=15)
    resp.raise_for_status()
    return resp.json()

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_neo_detail(key: str, neo_id: str) -> dict:
    resp = requests.get(f"{NASA_NEO}/{neo_id}", params={"api_key": key}, timeout=15)
    resp.raise_for_status()
    return resp.json()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:8px 0 20px 0;'>
        <div style='font-size:22px; font-weight:700; color:#58a6ff; letter-spacing:-0.5px;'>☄️ Asteroid Tracker</div>
        <div style='font-size:11px; color:#6e7681; margin-top:4px;'>Powered by NASA NeoWs API</div>
    </div>
    """, unsafe_allow_html=True)

    env_key = os.environ.get("NASA_API_KEY", "")
    if env_key:
        api_key = env_key
        st.markdown("""
        <div style='background:rgba(63,185,80,0.08); border:1px solid rgba(63,185,80,0.2);
                    border-radius:8px; padding:10px 14px; font-size:12px; color:#3fb950;'>
            ✓ API key configured
        </div>
        """, unsafe_allow_html=True)
    else:
        api_key = st.text_input("NASA API Key", type="password",
                                placeholder="Paste key or set NASA_API_KEY",
                                help="Get a free key at https://api.nasa.gov/")
        if not api_key:
            api_key = "DEMO_KEY"
            st.warning("Using DEMO_KEY — rate limited.", icon="⚠️")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if st.button("↻  Refresh Data", use_container_width=True):
        fetch_feed.clear()
        st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    now_local = datetime.now(user_tz)
    st.markdown(f"""
    <div style='font-size:11px; color:#6e7681; line-height:1.8;'>
        <div>📅 <b style='color:#8b949e'>Date range</b></div>
        <div style='margin-left:18px;'>{now_local.strftime('%b %d')} – {(now_local + timedelta(days=6)).strftime('%b %d, %Y')}</div>
        <div style='margin-top:8px;'>🕐 <b style='color:#8b949e'>Last updated</b></div>
        <div style='margin-left:18px;'>{now_local.strftime('%I:%M:%S %p')}</div>
        <div style='margin-left:18px; color:#4a5568;'>{tz_label}</div>
        <div style='margin-top:8px;'>🔄 <b style='color:#8b949e'>Auto-refresh</b></div>
        <div style='margin-left:18px;'>Every 5 minutes</div>
    </div>
    """, unsafe_allow_html=True)

# ── Fetch current + historical ────────────────────────────────────────────────
today      = datetime.now(timezone.utc).date()
week_start = today.isoformat()
week_end   = (today + timedelta(days=6)).isoformat()
hist_start = (today - timedelta(days=7)).isoformat()
hist_end   = (today - timedelta(days=1)).isoformat()

with st.spinner(""):
    try:
        raw      = fetch_feed(api_key, week_start, week_end)
        raw_hist = fetch_feed(api_key, hist_start, hist_end)
    except requests.HTTPError as e:
        st.error(f"NASA API error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.stop()

# ── Parse ─────────────────────────────────────────────────────────────────────
def compute_threat(diam_avg, miss_km, velocity, is_hazardous,
                   max_diam, max_vel, min_dist):
    s = min(diam_avg / max_diam, 1.0) * 0.35
    v = min(velocity / max_vel, 1.0) * 0.25
    d = max(0.0, 1.0 - (miss_km - min_dist) / (max_dist - min_dist + 1)) * 0.40
    score = (s + v + d) * 100
    return min(round(score * (1.4 if is_hazardous else 1.0), 1), 100.0)

def parse_feed(data: dict) -> pd.DataFrame:
    rows = []
    for date_str, neos in data["near_earth_objects"].items():
        for neo in neos:
            ca   = neo["close_approach_data"][0]
            diam = neo["estimated_diameter"]["meters"]
            d_avg = (diam["estimated_diameter_min"] + diam["estimated_diameter_max"]) / 2
            rows.append({
                "ID":                  neo["id"],
                "Name":                neo["name"].strip("()"),
                "Date":                date_str,
                "Miss Distance (km)":  float(ca["miss_distance"]["kilometers"]),
                "Diameter Min (m)":    round(diam["estimated_diameter_min"], 1),
                "Diameter Max (m)":    round(diam["estimated_diameter_max"], 1),
                "Diameter Avg (m)":    round(d_avg, 1),
                "Velocity (km/h)":     round(float(ca["relative_velocity"]["kilometers_per_hour"]), 1),
                "Potentially Hazardous": neo["is_potentially_hazardous_asteroid"],
                "NASA Link":           neo["nasa_jpl_url"],
            })
    return pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)

df      = parse_feed(raw)
df_hist = parse_feed(raw_hist)

# Threat score
max_diam = df["Diameter Avg (m)"].max()
max_vel  = df["Velocity (km/h)"].max()
min_dist = df["Miss Distance (km)"].min()
max_dist = df["Miss Distance (km)"].max()
df["Threat Score"] = df.apply(
    lambda r: compute_threat(r["Diameter Avg (m)"], r["Miss Distance (km)"],
                             r["Velocity (km/h)"], r["Potentially Hazardous"],
                             max_diam, max_vel, min_dist), axis=1
)

# ── Closest-ever detection (top 5 by miss distance) ───────────────────────────
closest_ids = df.nsmallest(5, "Miss Distance (km)")["ID"].tolist()
record_ids  = set()
for neo_id in closest_ids:
    try:
        detail = fetch_neo_detail(api_key, neo_id)
        history = detail.get("close_approach_data", [])
        if not history:
            continue
        all_dists = [float(c["miss_distance"]["kilometers"]) for c in history]
        current   = df.loc[df["ID"] == neo_id, "Miss Distance (km)"].values[0]
        if current <= min(all_dists) * 1.01:   # within 1% of all-time closest
            record_ids.add(neo_id)
    except Exception:
        pass

df["Record Approach"] = df["ID"].isin(record_ids)

# ── Aggregates ────────────────────────────────────────────────────────────────
total     = len(df)
hazardous = int(df["Potentially Hazardous"].sum())
closest   = df.loc[df["Miss Distance (km)"].idxmin()]
fastest   = df.loc[df["Velocity (km/h)"].idxmax()]
largest   = df.loc[df["Diameter Avg (m)"].idxmax()]
riskiest  = df.loc[df["Threat Score"].idxmax()]

# ── Historical aggregates ─────────────────────────────────────────────────────
h_total   = len(df_hist)
h_haz     = int(df_hist["Potentially Hazardous"].sum())
h_avg_dist= df_hist["Miss Distance (km)"].mean()

def delta_str(curr, prev, higher_is_bad=True):
    if prev == 0:
        return ""
    pct = (curr - prev) / prev * 100
    sign = "↑" if pct > 0 else "↓"
    cls  = "neg" if (pct > 0 and higher_is_bad) or (pct < 0 and not higher_is_bad) else "pos"
    return f'<span class="hist-delta-{cls}">{sign}{abs(pct):.0f}% vs last week</span>'

# ── Hero ──────────────────────────────────────────────────────────────────────
now_str = f"{datetime.now(user_tz).strftime('%b %d, %Y · %I:%M %p')} ({tz_label})"
st.markdown(f"""
<div class="hero">
    <div class="live-pill"><div class="live-dot"></div>LIVE</div>
    <h1 style="margin-top:12px;">Near-Earth Asteroid Monitor</h1>
    <p>Tracking <b style="color:#c9d1d9">{total} asteroids</b> approaching Earth over the next 7 days &nbsp;·&nbsp; {now_str}</p>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ─────────────────────────────────────────────────────────────────
def kpi(col, color, label, value, sub=""):
    col.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
kpi(c1, "blue",   "Total Asteroids",      total,                            f"Next 7 days")
kpi(c2, "red",    "Potentially Hazardous",hazardous,                        f"{hazardous/total*100:.0f}% of total")
kpi(c3, "green",  "Closest Approach",     f"{closest['Miss Distance (km)']:,.0f} km", closest["Name"])
kpi(c4, "amber",  "Fastest",              f"{fastest['Velocity (km/h)']:,.0f}",       f"km/h · {fastest['Name']}")
kpi(c5, "purple", "Highest Threat Score", f"{riskiest['Threat Score']:.0f}/100",      riskiest["Name"])

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Historical Comparison ─────────────────────────────────────────────────────
st.markdown('<div class="section-header">Week-over-Week Comparison</div>', unsafe_allow_html=True)
h1, h2, h3, h4 = st.columns(4)

def hist_card(col, label, this_week, last_week, fmt="{}", higher_is_bad=True, suffix=""):
    d = delta_str(this_week, last_week, higher_is_bad)
    col.markdown(f"""
    <div style='background:#0d1117; border:1px solid #21262d; border-radius:12px; padding:16px 20px;'>
        <div style='font-size:11px; color:#8b949e; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:8px;'>{label}</div>
        <div style='display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;'>
            <span style='font-size:22px; font-weight:700; color:#e6edf3;'>{fmt.format(this_week)}{suffix}</span>
            <span style='font-size:13px; color:#6e7681;'>vs <b style='color:#8b949e'>{fmt.format(last_week)}{suffix}</b></span>
        </div>
        <div style='margin-top:6px; font-size:12px;'>{d}</div>
    </div>
    """, unsafe_allow_html=True)

hist_card(h1, "Total Asteroids",       total,                   h_total,  fmt="{}")
hist_card(h2, "Hazardous Asteroids",   hazardous,               h_haz,    fmt="{}")
hist_card(h3, "Avg Miss Distance",     df["Miss Distance (km)"].mean(), h_avg_dist, fmt="{:,.0f}", higher_is_bad=False, suffix=" km")
hist_card(h4, "Avg Threat Score",      df["Threat Score"].mean(), df_hist["Velocity (km/h)"].mean() * 0.02, fmt="{:.1f}", higher_is_bad=True)

# ── Catalogue table ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Asteroid Catalogue</div>', unsafe_allow_html=True)

table_df = df[[
    "Name", "Date", "Miss Distance (km)",
    "Diameter Min (m)", "Diameter Max (m)",
    "Velocity (km/h)", "Threat Score", "Potentially Hazardous", "Record Approach",
]].copy()

def style_table(row):
    if row["Potentially Hazardous"]:
        return ["background-color:#1a0d0d; color:#f85149"] * len(row)
    return ["background-color:#0d1117; color:#c9d1d9"] * len(row)

styled = (
    table_df.style
    .apply(style_table, axis=1)
    .format({
        "Miss Distance (km)": "{:,.0f}",
        "Diameter Min (m)":   "{:.1f}",
        "Diameter Max (m)":   "{:.1f}",
        "Velocity (km/h)":    "{:,.1f}",
        "Threat Score":       "{:.1f}",
    })
)
st.dataframe(styled, width="stretch", hide_index=True, height=300)

# ── Asteroid Detail Panel ─────────────────────────────────────────────────────
st.markdown('<div class="section-header">Asteroid Detail Panel</div>', unsafe_allow_html=True)

names = df["Name"].tolist()
selected = st.selectbox("Select an asteroid to inspect", names,
                        index=int(df["Threat Score"].idxmax()))

row = df[df["Name"] == selected].iloc[0]
is_record = row["Record Approach"]
is_haz    = row["Potentially Hazardous"]
threat    = row["Threat Score"]
threat_color = "#f85149" if threat >= 70 else "#e3b341" if threat >= 40 else "#3fb950"

badge_haz    = '<span style="background:rgba(248,81,73,0.15);color:#f85149;border:1px solid rgba(248,81,73,0.3);border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600;">⚠ Potentially Hazardous</span>' if is_haz else '<span style="background:rgba(63,185,80,0.12);color:#3fb950;border:1px solid rgba(63,185,80,0.25);border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600;">✓ Safe</span>'
badge_record = '<span class="record-badge">⭐ Record Close Approach</span>' if is_record else ""

d1, d2 = st.columns([2, 1])

with d1:
    st.markdown(f"""
    <div class="detail-card">
        <div style='display:flex; align-items:center; gap:10px; margin-bottom:20px; flex-wrap:wrap;'>
            <span style='font-size:20px; font-weight:700; color:#e6edf3;'>{row['Name']}</span>
            {badge_haz}{badge_record}
        </div>
        <div class="detail-row"><span class="detail-label">Close Approach Date</span><span class="detail-value">{row['Date']}</span></div>
        <div class="detail-row"><span class="detail-label">Miss Distance</span><span class="detail-value">{row['Miss Distance (km)']:,.0f} km</span></div>
        <div class="detail-row"><span class="detail-label">Velocity</span><span class="detail-value">{row['Velocity (km/h)']:,.1f} km/h</span></div>
        <div class="detail-row"><span class="detail-label">Estimated Diameter</span><span class="detail-value">{row['Diameter Min (m)']:.1f} – {row['Diameter Max (m)']:.1f} m</span></div>
        <div class="detail-row">
            <span class="detail-label">Threat Score</span>
            <span class="detail-value" style="color:{threat_color}; font-weight:700;">{threat:.1f} / 100</span>
        </div>
        <div style='margin-top:10px;'>
            <div class="threat-bar-wrap">
                <div class="threat-bar" style="width:{threat}%; background:{threat_color};"></div>
            </div>
        </div>
        <div style='margin-top:16px;'>
            <a href="{row['NASA Link']}" target="_blank"
               style='font-size:12px; color:#58a6ff; text-decoration:none;
                      background:rgba(88,166,255,0.1); border:1px solid rgba(88,166,255,0.2);
                      border-radius:8px; padding:6px 14px;'>
                ↗ View on NASA JPL
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

with d2:
    # Threat gauge
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=threat,
        number={"suffix": "/100", "font": {"size": 22, "color": "#e6edf3"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8b949e", "tickfont": {"size": 10}},
            "bar": {"color": threat_color, "thickness": 0.25},
            "bgcolor": "#161b22",
            "bordercolor": "#21262d",
            "steps": [
                {"range": [0,  40], "color": "rgba(63,185,80,0.15)"},
                {"range": [40, 70], "color": "rgba(227,179,65,0.15)"},
                {"range": [70,100], "color": "rgba(248,81,73,0.15)"},
            ],
            "threshold": {"line": {"color": threat_color, "width": 3}, "thickness": 0.8, "value": threat},
        },
        title={"text": "Threat Score", "font": {"size": 13, "color": "#8b949e"}},
    ))
    gauge.update_layout(
        paper_bgcolor="#0d1117", font_color="#c9d1d9",
        margin=dict(l=20, r=20, t=40, b=10), height=220,
    )
    st.plotly_chart(gauge, width="stretch")

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Analytics</div>', unsafe_allow_html=True)

CHART_BG   = "#0d1117"
GRID_COLOR = "#1c2333"
FONT_COLOR = "#8b949e"
chart_layout = dict(
    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
    font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(13,17,23,0.8)", bordercolor="#21262d", borderwidth=1, font=dict(size=11)),
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont=dict(size=11)),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont=dict(size=11)),
)

col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    scatter = px.scatter(
        df, x="Miss Distance (km)", y="Diameter Avg (m)",
        color="Potentially Hazardous",
        color_discrete_map={True: "#f85149", False: "#58a6ff"},
        size="Diameter Avg (m)", size_max=28,
        hover_name="Name",
        hover_data={"Date": True, "Velocity (km/h)": ":.0f",
                    "Threat Score": ":.1f", "Potentially Hazardous": False, "Diameter Avg (m)": False},
        labels={"Miss Distance (km)": "Miss Distance (km)", "Diameter Avg (m)": "Avg Diameter (m)", "Potentially Hazardous": "Hazardous"},
        title="Diameter vs. Miss Distance",
        template="plotly_dark",
    )
    scatter.update_traces(marker=dict(opacity=0.85, line=dict(width=0.5, color="#21262d")))
    scatter.update_layout(**chart_layout, title_font=dict(size=14, color="#c9d1d9"))
    st.plotly_chart(scatter, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    daily = (df.groupby(["Date", "Potentially Hazardous"]).size().reset_index(name="Count"))
    daily["Type"] = daily["Potentially Hazardous"].map({True: "Hazardous", False: "Safe"})
    bar = px.bar(daily, x="Date", y="Count", color="Type",
                 color_discrete_map={"Hazardous": "#f85149", "Safe": "#58a6ff"},
                 barmode="stack", title="Asteroids per Day", template="plotly_dark",
                 labels={"Count": "Count", "Date": "Date", "Type": ""})
    bar.update_traces(marker_line_width=0)
    bar.update_layout(**chart_layout, title_font=dict(size=14, color="#c9d1d9"), bargap=0.3)
    st.plotly_chart(bar, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

# Velocity distribution
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
vel_fig = px.violin(df, x="Date", y="Velocity (km/h)",
                    color="Potentially Hazardous",
                    color_discrete_map={True: "#f85149", False: "#58a6ff"},
                    box=True, points="all", hover_name="Name",
                    title="Velocity Distribution by Day", template="plotly_dark",
                    labels={"Potentially Hazardous": "Hazardous"})
vel_fig.update_traces(meanline_visible=True, marker=dict(size=4, opacity=0.7))
vel_fig.update_layout(**chart_layout, title_font=dict(size=14, color="#c9d1d9"), height=340)
st.plotly_chart(vel_fig, width="stretch")
st.markdown('</div>', unsafe_allow_html=True)

# ── 3D Orbit Viewer ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">3D Orbit Viewer</div>', unsafe_allow_html=True)
st.markdown("""
<div style='font-size:12px; color:#6e7681; margin-bottom:12px;'>
    Asteroid positions relative to Earth &nbsp;·&nbsp; distances to scale &nbsp;·&nbsp; drag to rotate
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="chart-card">', unsafe_allow_html=True)

# Distribute asteroids in 3D using golden-angle spiral for even spread
def spherical_positions(distances):
    n = len(distances)
    xs, ys, zs = [], [], []
    golden = math.pi * (3 - math.sqrt(5))
    for i, d in enumerate(distances):
        y     = 1 - (i / max(n - 1, 1)) * 2
        r     = math.sqrt(max(0, 1 - y * y))
        theta = golden * i
        xs.append(d * r * math.cos(theta))
        ys.append(d * y)
        zs.append(d * r * math.sin(theta))
    return xs, ys, zs

xs, ys, zs = spherical_positions(df["Miss Distance (km)"].tolist())
df["x3d"], df["y3d"], df["z3d"] = xs, ys, zs

MOON_DIST = 384_400  # km

# Moon orbit ring
theta_ring = [i * 2 * math.pi / 100 for i in range(101)]
moon_x = [MOON_DIST * math.cos(t) for t in theta_ring]
moon_y = [0] * 101
moon_z = [MOON_DIST * math.sin(t) for t in theta_ring]

fig3d = go.Figure()

# Moon orbit
fig3d.add_trace(go.Scatter3d(
    x=moon_x, y=moon_y, z=moon_z,
    mode="lines",
    line=dict(color="rgba(139,148,158,0.3)", width=1),
    name="Moon Orbit",
    hoverinfo="skip",
))

# Earth
fig3d.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[0],
    mode="markers+text",
    marker=dict(size=14, color="#1f77d4",
                line=dict(color="#58a6ff", width=2)),
    text=["Earth"], textposition="top center",
    textfont=dict(color="#58a6ff", size=11),
    name="Earth", hoverinfo="name",
))

# Moon
fig3d.add_trace(go.Scatter3d(
    x=[MOON_DIST], y=[0], z=[0],
    mode="markers+text",
    marker=dict(size=6, color="#8b949e",
                line=dict(color="#c9d1d9", width=1)),
    text=["Moon"], textposition="top center",
    textfont=dict(color="#8b949e", size=10),
    name="Moon", hoverinfo="name",
))

# Safe asteroids
safe_df = df[~df["Potentially Hazardous"]]
fig3d.add_trace(go.Scatter3d(
    x=safe_df["x3d"], y=safe_df["y3d"], z=safe_df["z3d"],
    mode="markers",
    marker=dict(
        size=safe_df["Diameter Avg (m)"].clip(upper=500) / 20 + 3,
        color="#58a6ff", opacity=0.75,
        line=dict(color="#1f6feb", width=0.5),
    ),
    text=safe_df["Name"],
    customdata=safe_df[["Miss Distance (km)", "Diameter Avg (m)", "Velocity (km/h)", "Threat Score"]].values,
    hovertemplate=(
        "<b>%{text}</b><br>"
        "Miss Distance: %{customdata[0]:,.0f} km<br>"
        "Diameter: %{customdata[1]:.1f} m<br>"
        "Velocity: %{customdata[2]:,.0f} km/h<br>"
        "Threat Score: %{customdata[3]:.1f}<extra></extra>"
    ),
    name="Safe",
))

# Hazardous asteroids
haz_df = df[df["Potentially Hazardous"]]
if not haz_df.empty:
    fig3d.add_trace(go.Scatter3d(
        x=haz_df["x3d"], y=haz_df["y3d"], z=haz_df["z3d"],
        mode="markers",
        marker=dict(
            size=haz_df["Diameter Avg (m)"].clip(upper=500) / 20 + 4,
            color="#f85149", opacity=0.85,
            line=dict(color="#da3633", width=0.5),
            symbol="diamond",
        ),
        text=haz_df["Name"],
        customdata=haz_df[["Miss Distance (km)", "Diameter Avg (m)", "Velocity (km/h)", "Threat Score"]].values,
        hovertemplate=(
            "<b>%{text}</b> ⚠<br>"
            "Miss Distance: %{customdata[0]:,.0f} km<br>"
            "Diameter: %{customdata[1]:.1f} m<br>"
            "Velocity: %{customdata[2]:,.0f} km/h<br>"
            "Threat Score: %{customdata[3]:.1f}<extra></extra>"
        ),
        name="Hazardous",
    ))

fig3d.update_layout(
    paper_bgcolor="#0d1117",
    scene=dict(
        bgcolor="#06080f",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   title="", backgroundcolor="#06080f"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   title="", backgroundcolor="#06080f"),
        zaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   title="", backgroundcolor="#06080f"),
        camera=dict(eye=dict(x=1.4, y=0.8, z=0.8)),
    ),
    legend=dict(bgcolor="rgba(13,17,23,0.8)", bordercolor="#21262d",
                borderwidth=1, font=dict(size=11, color="#c9d1d9")),
    margin=dict(l=0, r=0, t=10, b=0),
    height=520,
    font=dict(color="#c9d1d9"),
)
st.plotly_chart(fig3d, width="stretch")
st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-top:32px; padding-top:16px; border-top:1px solid #21262d;
            display:flex; justify-content:space-between; align-items:center;
            font-size:11px; color:#6e7681;'>
    <span>Source: <a href="https://api.nasa.gov/" style="color:#58a6ff;text-decoration:none;">NASA Center for Near Earth Object Studies (CNEOS)</a></span>
    <span>Auto-refreshes every 5 min · Last refresh: {datetime.now(user_tz).strftime('%I:%M:%S %p')} ({tz_label})</span>
</div>
""", unsafe_allow_html=True)
