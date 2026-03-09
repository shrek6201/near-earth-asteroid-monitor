import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Asteroid Tracker",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, .stApp {
    background-color: #06080f;
    color: #c9d1d9;
    font-family: 'Inter', sans-serif;
}

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 2rem 2.5rem; max-width: 1400px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #0a0e1a 100%);
    border-right: 1px solid #1c2333;
}
section[data-testid="stSidebar"] .stTextInput input {
    background: #0d1117;
    border: 1px solid #30363d;
    color: #e6edf3;
    border-radius: 8px;
}
section[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.3px;
    transition: opacity 0.2s;
}
section[data-testid="stSidebar"] .stButton button:hover { opacity: 0.85; }

/* ── KPI cards ── */
.kpi-card {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21262d;
    border-radius: 16px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    height: 110px;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.kpi-card.blue::before  { background: linear-gradient(90deg, #1f6feb, #58a6ff); }
.kpi-card.red::before   { background: linear-gradient(90deg, #da3633, #f85149); }
.kpi-card.green::before { background: linear-gradient(90deg, #238636, #3fb950); }
.kpi-card.amber::before { background: linear-gradient(90deg, #9e6a03, #e3b341); }

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #e6edf3;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 11px;
    color: #6e7681;
    margin-top: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Section headers ── */
.section-header {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #8b949e;
    border-bottom: 1px solid #21262d;
    padding-bottom: 8px;
    margin: 28px 0 16px 0;
}

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 50%, #0d1117 100%);
    border: 1px solid #1c2333;
    border-radius: 20px;
    padding: 36px 40px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '☄️';
    position: absolute;
    right: 40px; top: 50%;
    transform: translateY(-50%);
    font-size: 72px;
    opacity: 0.15;
}
.hero h1 {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #a5d6ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 6px 0;
    line-height: 1.2;
}
.hero p {
    color: #6e7681;
    font-size: 14px;
    margin: 0;
}

/* ── Hazard badge ── */
.badge-danger {
    background: rgba(248,81,73,0.15);
    color: #f85149;
    border: 1px solid rgba(248,81,73,0.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}
.badge-safe {
    background: rgba(63,185,80,0.12);
    color: #3fb950;
    border: 1px solid rgba(63,185,80,0.25);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}

/* ── Chart containers ── */
.chart-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 16px;
    padding: 20px;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid #21262d !important;
    border-radius: 12px !important;
}
.stDataFrame thead tr th {
    background: #161b22 !important;
    color: #8b949e !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
}

/* ── Live pill ── */
.live-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(63,185,80,0.1);
    border: 1px solid rgba(63,185,80,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #3fb950;
}
.live-dot {
    width: 7px; height: 7px;
    background: #3fb950;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%   { opacity: 1; transform: scale(1); }
    50%  { opacity: 0.4; transform: scale(0.8); }
    100% { opacity: 1; transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
REFRESH_MS = 5 * 60 * 1000
st_autorefresh(interval=REFRESH_MS, key="auto_refresh")

# ── API ───────────────────────────────────────────────────────────────────────
NASA_URL = "https://api.nasa.gov/neo/rest/v1/feed"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_asteroids(key: str) -> dict:
    start = datetime.now(timezone.utc).date()
    end = start + timedelta(days=6)
    resp = requests.get(NASA_URL, params={
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "api_key": key,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 20px 0;'>
        <div style='font-size:22px; font-weight:700; color:#58a6ff; letter-spacing:-0.5px;'>☄️ Asteroid Tracker</div>
        <div style='font-size:11px; color:#6e7681; margin-top:4px;'>Powered by NASA NeoWs API</div>
    </div>
    """, unsafe_allow_html=True)

    env_key = os.environ.get("NASA_API_KEY", "")
    api_key = st.text_input(
        "NASA API Key",
        value=env_key,
        type="password",
        placeholder="Paste key or set NASA_API_KEY",
        help="Get a free key at https://api.nasa.gov/",
        label_visibility="visible",
    )
    if not api_key:
        api_key = "DEMO_KEY"
        st.warning("Using DEMO_KEY — rate limited.", icon="⚠️")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if st.button("↻  Refresh Data", use_container_width=True):
        fetch_asteroids.clear()
        st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    now_utc = datetime.now(timezone.utc)
    st.markdown(f"""
    <div style='font-size:11px; color:#6e7681; line-height:1.8;'>
        <div>📅 <b style='color:#8b949e'>Date range</b></div>
        <div style='margin-left:18px;'>{now_utc.strftime('%b %d')} – {(now_utc + timedelta(days=6)).strftime('%b %d, %Y')}</div>
        <div style='margin-top:8px;'>🕐 <b style='color:#8b949e'>Last updated</b></div>
        <div style='margin-left:18px;'>{now_utc.strftime('%H:%M:%S UTC')}</div>
        <div style='margin-top:8px;'>🔄 <b style='color:#8b949e'>Auto-refresh</b></div>
        <div style='margin-left:18px;'>Every 5 minutes</div>
    </div>
    """, unsafe_allow_html=True)

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner(""):
    try:
        raw = fetch_asteroids(api_key)
    except requests.HTTPError as e:
        st.error(f"NASA API error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.stop()

# ── Parse ─────────────────────────────────────────────────────────────────────
def parse_data(raw: dict) -> pd.DataFrame:
    rows = []
    for date_str, neos in raw["near_earth_objects"].items():
        for neo in neos:
            ca = neo["close_approach_data"][0]
            diam = neo["estimated_diameter"]["meters"]
            rows.append({
                "Name": neo["name"].strip("()"),
                "Date": date_str,
                "Miss Distance (km)": float(ca["miss_distance"]["kilometers"]),
                "Diameter Min (m)": round(diam["estimated_diameter_min"], 1),
                "Diameter Max (m)": round(diam["estimated_diameter_max"], 1),
                "Diameter Avg (m)": round((diam["estimated_diameter_min"] + diam["estimated_diameter_max"]) / 2, 1),
                "Velocity (km/h)": round(float(ca["relative_velocity"]["kilometers_per_hour"]), 1),
                "Potentially Hazardous": neo["is_potentially_hazardous_asteroid"],
                "NASA Link": neo["nasa_jpl_url"],
            })
    return pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)

df = parse_data(raw)

total      = len(df)
hazardous  = int(df["Potentially Hazardous"].sum())
closest    = df.loc[df["Miss Distance (km)"].idxmin()]
fastest    = df.loc[df["Velocity (km/h)"].idxmax()]
largest    = df.loc[df["Diameter Avg (m)"].idxmax()]

# ── Hero ──────────────────────────────────────────────────────────────────────
now_str = datetime.now(timezone.utc).strftime("%b %d, %Y · %H:%M UTC")
st.markdown(f"""
<div class="hero">
    <div class="live-pill"><div class="live-dot"></div>LIVE</div>
    <h1 style="margin-top:12px;">Near-Earth Asteroid Monitor</h1>
    <p>Tracking <b style="color:#c9d1d9">{total} asteroids</b> approaching Earth over the next 7 days &nbsp;·&nbsp; {now_str}</p>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

def kpi(col, color, label, value, sub=""):
    col.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi(c1, "blue",  "Total Asteroids",   total,           f"Next 7 days")
kpi(c2, "red",   "Potentially Hazardous", hazardous,   f"{hazardous/total*100:.0f}% of total")
kpi(c3, "green", "Closest Approach",  f"{closest['Miss Distance (km)']:,.0f} km", closest["Name"])
kpi(c4, "amber", "Fastest",           f"{fastest['Velocity (km/h)']:,.0f}",       f"km/h · {fastest['Name']}")
kpi(c5, "blue",  "Largest",           f"{largest['Diameter Avg (m)']:.0f} m",     largest["Name"])

# ── Table ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Asteroid Catalogue</div>', unsafe_allow_html=True)

table_df = df[[
    "Name", "Date", "Miss Distance (km)",
    "Diameter Min (m)", "Diameter Max (m)",
    "Velocity (km/h)", "Potentially Hazardous",
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
        "Diameter Min (m)": "{:.1f}",
        "Diameter Max (m)": "{:.1f}",
        "Velocity (km/h)": "{:,.1f}",
    })
    .set_table_styles([{
        "selector": "th",
        "props": [
            ("background-color", "#161b22"),
            ("color", "#8b949e"),
            ("font-size", "11px"),
            ("text-transform", "uppercase"),
            ("letter-spacing", "0.8px"),
        ]
    }])
)

st.dataframe(styled, width="stretch", hide_index=True, height=320)

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Analytics</div>', unsafe_allow_html=True)

col_l, col_r = st.columns(2)

CHART_BG   = "#0d1117"
PANEL_BG   = "#0d1117"
GRID_COLOR = "#1c2333"
FONT_COLOR = "#8b949e"

chart_layout = dict(
    paper_bgcolor=CHART_BG,
    plot_bgcolor=PANEL_BG,
    font=dict(family="Inter, sans-serif", color=FONT_COLOR, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        bgcolor="rgba(13,17,23,0.8)",
        bordercolor="#21262d",
        borderwidth=1,
        font=dict(size=11),
    ),
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont=dict(size=11)),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont=dict(size=11)),
)

with col_l:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    scatter = px.scatter(
        df,
        x="Miss Distance (km)",
        y="Diameter Avg (m)",
        color="Potentially Hazardous",
        color_discrete_map={True: "#f85149", False: "#58a6ff"},
        size="Diameter Avg (m)",
        size_max=28,
        hover_name="Name",
        hover_data={"Date": True, "Velocity (km/h)": ":.0f", "Potentially Hazardous": False, "Diameter Avg (m)": False},
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
    daily = (
        df.groupby(["Date", "Potentially Hazardous"])
        .size()
        .reset_index(name="Count")
    )
    daily["Type"] = daily["Potentially Hazardous"].map({True: "Hazardous", False: "Safe"})

    bar = px.bar(
        daily,
        x="Date",
        y="Count",
        color="Type",
        color_discrete_map={"Hazardous": "#f85149", "Safe": "#58a6ff"},
        barmode="stack",
        title="Asteroids per Day",
        template="plotly_dark",
        labels={"Count": "Count", "Date": "Date", "Type": ""},
    )
    bar.update_traces(marker_line_width=0)
    bar.update_layout(**chart_layout, title_font=dict(size=14, color="#c9d1d9"), bargap=0.3)
    st.plotly_chart(bar, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Velocity distribution ─────────────────────────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
vel_fig = px.violin(
    df,
    x="Date",
    y="Velocity (km/h)",
    color="Potentially Hazardous",
    color_discrete_map={True: "#f85149", False: "#58a6ff"},
    box=True,
    points="all",
    hover_name="Name",
    title="Velocity Distribution by Day",
    template="plotly_dark",
    labels={"Potentially Hazardous": "Hazardous"},
)
vel_fig.update_traces(meanline_visible=True, marker=dict(size=4, opacity=0.7))
vel_fig.update_layout(**chart_layout, title_font=dict(size=14, color="#c9d1d9"), height=340)
st.plotly_chart(vel_fig, width="stretch")
st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-top:32px; padding-top:16px; border-top:1px solid #21262d;
            display:flex; justify-content:space-between; align-items:center;
            font-size:11px; color:#6e7681;'>
    <span>Source: <a href="https://api.nasa.gov/" style="color:#58a6ff; text-decoration:none;">NASA Center for Near Earth Object Studies (CNEOS)</a></span>
    <span>Auto-refreshes every 5 min · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
</div>
""", unsafe_allow_html=True)
