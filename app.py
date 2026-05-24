import os
import math
import subprocess
from datetime import datetime
from src.predict import predict_city_rain
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────────────────────
# Page config — MUST be the very first Streamlit call
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ireland Weather Hub",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after { font-family: 'Inter', sans-serif; box-sizing: border-box; }

/* ── Background ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #04080f 0%, #060d1a 35%, #081426 65%, #060c1a 100%);
    min-height: 100vh;
}

/* ── Header: transparent, but keep it in the DOM ── */
[data-testid="stHeader"] { background: transparent !important; }

/* ── Hide clutter — but NOT the toolbar itself (sidebar expand lives there) ── */
[data-testid="stMainMenu"]        { visibility: hidden !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
footer { visibility: hidden !important; }

/* ── Sidebar EXPAND button (appears in toolbar when sidebar is collapsed) ──
   data-testid="stExpandSidebarButton" confirmed from Streamlit 1.57 bundle  */
[data-testid="stExpandSidebarButton"] {
    visibility: visible !important;
    background: rgba(5,12,26,0.92) !important;
    border: 1px solid rgba(0,255,136,0.28) !important;
    border-left: none !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 4px 6px !important;
}
[data-testid="stExpandSidebarButton"] svg {
    fill: rgba(255,255,255,0.75) !important;
    color: rgba(255,255,255,0.75) !important;
}
[data-testid="stExpandSidebarButton"]:hover {
    background: rgba(0,255,136,0.12) !important;
    border-color: rgba(0,255,136,0.55) !important;
}
[data-testid="stExpandSidebarButton"]:hover svg {
    fill: #00ff88 !important;
    color: #00ff88 !important;
}

/* ── Sidebar COLLAPSE button (inside the sidebar to close it) ── */
[data-testid="stSidebarCollapseButton"] button {
    color: rgba(255,255,255,0.5) !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    color: #00ff88 !important;
    background: rgba(0,255,136,0.08) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #050c1a 0%, #060e1f 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg,
        rgba(0,80,0,0.25) 0%,
        rgba(0,50,120,0.35) 50%,
        rgba(0,80,0,0.2) 100%);
    border: 1px solid rgba(0,255,136,0.12);
    border-radius: 20px;
    padding: 2.4rem 3rem 2rem;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(12px);
}
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 60% 50% at 80% 50%, rgba(0,212,255,0.06), transparent);
    pointer-events: none;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(0,255,136,0.1);
    border: 1px solid rgba(0,255,136,0.25);
    border-radius: 30px;
    padding: 4px 13px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #00ff88;
    margin-bottom: 1rem;
}
.live-dot {
    width: 7px; height: 7px;
    background: #00ff88;
    border-radius: 50%;
    display: inline-block;
    animation: livePulse 2s ease infinite;
}
@keyframes livePulse {
    0%   { box-shadow: 0 0 0 0 rgba(0,255,136,0.7); }
    70%  { box-shadow: 0 0 0 8px rgba(0,255,136,0); }
    100% { box-shadow: 0 0 0 0 rgba(0,255,136,0); }
}
.hero-title {
    font-size: clamp(1.8rem, 4vw, 2.9rem);
    font-weight: 900;
    line-height: 1.15;
    background: linear-gradient(110deg, #00ff88 10%, #00d4ff 55%, #ffffff 90%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.5rem;
}
.hero-sub { color: rgba(255,255,255,0.48); font-size: 0.95rem; font-weight: 400; margin: 0; }
.hero-meta { display: flex; gap: 1.4rem; margin-top: 1.4rem; flex-wrap: wrap; }
.hero-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.55);
    font-weight: 500;
}
.hero-chip strong { color: rgba(255,255,255,0.9); font-weight: 600; }

/* ── KPI Cards ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.6rem; }
.kpi-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.4rem 1.2rem 1.2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(8px);
    transition: border-color 0.2s, transform 0.2s;
}
.kpi-card:hover { border-color: rgba(255,255,255,0.15); transform: translateY(-2px); }
.kpi-top-bar { position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 16px 16px 0 0; }
.kpi-card.blue   .kpi-top-bar { background: linear-gradient(90deg, #0066ff, #00d4ff); }
.kpi-card.teal   .kpi-top-bar { background: linear-gradient(90deg, #00ff88, #00d4ff); }
.kpi-card.amber  .kpi-top-bar { background: linear-gradient(90deg, #ff6b35, #ffcc00); }
.kpi-card.purple .kpi-top-bar { background: linear-gradient(90deg, #a855f7, #ec4899); }
.kpi-icon  { font-size: 1.7rem; margin-bottom: 0.6rem; line-height: 1; }
.kpi-label { color: rgba(255,255,255,0.42); font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.35rem; }
.kpi-value { color: #ffffff; font-size: 2.1rem; font-weight: 800; line-height: 1; margin-bottom: 0.25rem; }
.kpi-sub   { color: rgba(255,255,255,0.35); font-size: 0.75rem; }
.kpi-glow  { position: absolute; bottom: -30px; right: -20px; width: 80px; height: 80px; border-radius: 50%; filter: blur(30px); opacity: 0.15; }
.kpi-card.blue   .kpi-glow { background: #00d4ff; }
.kpi-card.teal   .kpi-glow { background: #00ff88; }
.kpi-card.amber  .kpi-glow { background: #ff9a00; }
.kpi-card.purple .kpi-glow { background: #a855f7; }

/* ── Section Header ── */
.section-hdr { display: flex; align-items: center; gap: 10px; margin: 1.6rem 0 1rem; }
.section-hdr-title { color: rgba(255,255,255,0.9); font-size: 1rem; font-weight: 700; white-space: nowrap; }
.section-hdr-line  { flex: 1; height: 1px; background: rgba(255,255,255,0.06); }

/* ── City Cards ── */
.city-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.85rem; margin-bottom: 0.5rem; }
.city-card {
    background: rgba(255,255,255,0.032);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.1rem 0.9rem 1rem;
    text-align: center;
    transition: all 0.2s ease;
}
.city-card:hover {
    background: rgba(0,212,255,0.07);
    border-color: rgba(0,212,255,0.28);
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
.city-icon { font-size: 1.9rem; line-height: 1; margin-bottom: 0.4rem; }
.city-name { color: rgba(255,255,255,0.85); font-size: 0.82rem; font-weight: 600; margin-bottom: 0.25rem; }
.city-temp { color: #ffffff; font-size: 1.55rem; font-weight: 800; line-height: 1; margin-bottom: 0.2rem; }
.city-rain { color: #00d4ff; font-size: 0.73rem; font-weight: 500; margin-bottom: 0.35rem; }
.city-wind { color: rgba(255,255,255,0.35); font-size: 0.7rem; }
.rain-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.3rem; }
.badge-none     { background: rgba(120,120,120,0.2); color: #888; }
.badge-light    { background: rgba(0,150,255,0.18);  color: #60aaff; }
.badge-moderate { background: rgba(80,0,255,0.22);   color: #9080ff; }
.badge-heavy    { background: rgba(180,0,255,0.22);  color: #d080ff; }

/* ── Map zoom badge ── */
.zoom-hint {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(0,212,255,0.12); border: 1px solid rgba(0,212,255,0.25);
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.73rem; color: #00d4ff; font-weight: 600;
    margin-bottom: 0.6rem;
}

/* ── Chart containers ── */
.chart-wrap {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1rem 0.5rem 0.5rem;
    margin-bottom: 0.8rem;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 7px;
    color: rgba(255,255,255,0.45);
    font-weight: 500;
    font-size: 0.85rem;
    padding: 6px 16px;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(0,212,255,0.14) !important;
    color: #00d4ff !important;
    font-weight: 600;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #004d1a, #003d14) !important;
    color: #00ff88 !important;
    border: 1px solid rgba(0,255,136,0.28) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    padding: 0.55rem 1.2rem !important;
    width: 100%;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #006622, #004d1a) !important;
    border-color: rgba(0,255,136,0.55) !important;
    box-shadow: 0 4px 20px rgba(0,255,136,0.18) !important;
    transform: translateY(-1px) !important;
}

/* ── Sidebar labels ── */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] h3 { color: rgba(255,255,255,0.7) !important; }
[data-testid="stSidebar"] [data-testid="stMultiSelect"] > div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: white !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: rgba(255,255,255,0.7) !important; font-weight: 500; }

/* ── Source badge ── */
.src-badge {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 0.6rem 1rem; margin-top: 0.4rem;
}

/* ── Footer ── */
.footer {
    text-align: center; padding: 2rem 0 1rem;
    color: rgba(255,255,255,0.18); font-size: 0.72rem;
    border-top: 1px solid rgba(255,255,255,0.04); margin-top: 2rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }
hr { border-color: rgba(255,255,255,0.05) !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
ALL_OPT = "🗂️  All Cities"

CITY_COLORS = [
    "#00d4ff", "#00ff88", "#ff6b6b", "#ffd93d",
    "#a855f7", "#ff9a3c", "#4ecdc4", "#ff63c3",
    "#c0ff72", "#38bdf8",
]

CHART_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(6,14,28,0.55)",
    font=dict(color="rgba(255,255,255,0.6)", family="Inter", size=11),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)", showline=False,
        tickfont=dict(color="rgba(255,255,255,0.45)"),
        title_font=dict(color="rgba(255,255,255,0.55)"), zeroline=False,
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.04)", showline=False,
        tickfont=dict(color="rgba(255,255,255,0.45)"),
        title_font=dict(color="rgba(255,255,255,0.55)"), zeroline=False,
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.08)",
        borderwidth=1, font=dict(color="rgba(255,255,255,0.6)", size=10),
    ),
    margin=dict(t=20, b=40, l=50, r=20),
    hoverlabel=dict(
        bgcolor="rgba(6,14,28,0.92)", bordercolor="rgba(255,255,255,0.12)",
        font=dict(color="white", size=12),
    ),
)


def weather_icon(prob, precip, cloud):
    if prob >= 75 and precip > 2:    return "⛈️"
    if prob >= 60 and precip > 0.3:  return "🌧️"
    if prob >= 35:                    return "🌦️"
    if cloud >= 80:                   return "☁️"
    if cloud >= 40:                   return "⛅"
    return "🌤️"


def rain_badge(precip):
    if precip == 0:   return "badge-none",     "Dry"
    if precip < 0.5:  return "badge-light",    "Light"
    if precip < 2.0:  return "badge-moderate", "Moderate"
    return "badge-heavy", "Heavy"


def wind_label(speed):
    if speed < 5:  return "🍃 Calm"
    if speed < 15: return "💨 Breeze"
    if speed < 30: return "🌬️ Windy"
    return "🌪️ Strong"


def fit_zoom_center(lats: list, lons: list) -> tuple:
    """Return (zoom, center_dict) that fits all supplied lat/lon points."""
    if not lats:
        return 5.9, {"lat": 53.3, "lon": -8.1}
    if len(lats) == 1:
        return 10.5, {"lat": lats[0], "lon": lons[0]}

    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    center = {"lat": (lat_min + lat_max) / 2, "lon": (lon_min + lon_max) / 2}

    span = max(lat_max - lat_min, lon_max - lon_min)
    # Map degree span → Mapbox zoom level (empirically tuned for Ireland)
    if span < 0.05:  zoom = 13
    elif span < 0.2: zoom = 12
    elif span < 0.5: zoom = 11
    elif span < 1.0: zoom = 10
    elif span < 2.0: zoom = 9
    elif span < 3.5: zoom = 8
    elif span < 6.0: zoom = 7
    elif span < 10:  zoom = 6.5
    else:            zoom = 5.8
    return zoom, center


def styled_line(df_in, y_col, y_label, city_color_map, height=380):
    fig = px.line(
        df_in, x="forecast_time", y=y_col, color="city",
        markers=True, height=height,
        color_discrete_map=city_color_map,
        labels={"forecast_time": "Hour", y_col: y_label, "city": "City"},
    )
    fig.update_layout(**CHART_BASE)
    fig.update_traces(line_width=2.2, marker_size=5)
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# Data loading — PostgreSQL first, CSV fallback
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_postgres():
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.engine import URL
        load_dotenv()
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD") or None,
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME"),
        )
        engine = create_engine(
            url,
            connect_args={"sslmode": os.getenv("DB_SSLMODE", "require")}
        )
        df = pd.read_sql("""
            SELECT * FROM live_weather
            WHERE loaded_at >= (
                SELECT MAX(loaded_at) - INTERVAL '2 minutes' FROM live_weather
            )
            ORDER BY forecast_time, city
        """, engine)
        if df.empty:
            return None, None
        df["forecast_time"] = pd.to_datetime(df["forecast_time"])
        df["loaded_at"]     = pd.to_datetime(df["loaded_at"])
        return df, "PostgreSQL"
    except Exception:
        return None, None


@st.cache_data(ttl=300)
def load_csv():
    try:
        df = pd.read_csv("data/live_weather.csv")
        df["forecast_time"] = pd.to_datetime(df["forecast_time"])
        df["loaded_at"]     = pd.to_datetime(df["loaded_at"])
        return df, "CSV Cache"
    except Exception:
        return None, None

# ──────────────────────────────────────────────────────────────────────────────
# Prediction history loading — Neon/PostgreSQL
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_prediction_history():
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.engine import URL

        load_dotenv()

        url = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD") or None,
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME"),
        )

        engine = create_engine(
            url,
            connect_args={"sslmode": os.getenv("DB_SSLMODE", "require")}
        )

        query = """
            SELECT
                city,
                rain_prediction,
                rain_probability,
                risk_level,
                model_version,
                prediction_time,
                created_at
            FROM rain_predictions
            ORDER BY prediction_time DESC
            LIMIT 100;
        """

        pred_df = pd.read_sql(query, engine)

        if pred_df.empty:
            return pred_df

        pred_df["prediction_time"] = pd.to_datetime(pred_df["prediction_time"])
        pred_df["created_at"] = pd.to_datetime(pred_df["created_at"])

        return pred_df

    except Exception:
        return pd.DataFrame(columns=[
            "city",
            "rain_prediction",
            "rain_probability",
            "risk_level",
            "model_version",
            "prediction_time",
            "created_at",
        ])


# ──────────────────────────────────────────────────────────────────────────────
# Process any pending map-click zoom from last render (before sidebar renders)
# ──────────────────────────────────────────────────────────────────────────────
if "pending_map_click" in st.session_state:
    clicked = st.session_state.pop("pending_map_click")
    # Toggle: clicking the already-zoomed city resets the view
    if clicked == st.session_state.get("map_zoom_city"):
        st.session_state.pop("map_zoom_city", None)
    else:
        st.session_state["map_zoom_city"] = clicked


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.4rem 0 1rem; text-align:center;
                border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:1.2rem;">
        <div style="font-size:2.8rem; line-height:1;">🌧️</div>
        <div style="color:#00ff88; font-size:1.05rem; font-weight:800; margin:0.5rem 0 0.1rem;">
            Ireland Weather</div>
        <div style="color:rgba(255,255,255,0.35); font-size:0.72rem;">Live Monitoring Hub</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**🔄 Data**")
    refresh_clicked = st.button("⟳  Refresh Weather Data", use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**🏙️ Cities**")
    city_placeholder   = st.empty()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**⏰ Forecast Hour**")
    time_placeholder   = st.empty()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**🌧️ Rain Threshold**")
    min_rain = st.slider("Min probability %", 0, 100, 0, 5, label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)
    source_placeholder = st.empty()

    # Reset map zoom from sidebar
    if st.session_state.get("map_zoom_city"):
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button(f"🔍 Reset zoom  ({st.session_state['map_zoom_city']})", use_container_width=True):
            st.session_state.pop("map_zoom_city", None)
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Handle refresh
# ──────────────────────────────────────────────────────────────────────────────
if refresh_clicked:
    with st.spinner("Fetching latest weather data..."):
        r = subprocess.run(
            ["python", "src/fetch_weather_to_postgres.py"],
            capture_output=True, text=True,
        )
    if r.returncode == 0:
        st.cache_data.clear()
        st.rerun()
    else:
        r2 = subprocess.run(["python", "src/fetch_weather.py"], capture_output=True, text=True)
        if r2.returncode == 0:
            st.cache_data.clear()
            st.rerun()
        else:
            st.sidebar.error("Update failed — check network/DB.")


# ──────────────────────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────────────────────
df, source = load_postgres()
if df is None:
    df, source = load_csv()

if df is None or df.empty:
    st.error("⚠️ No weather data found. Click **Refresh Weather Data** in the sidebar.")
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# Populate sidebar filters
# ──────────────────────────────────────────────────────────────────────────────
all_cities     = sorted(df["city"].unique())
forecast_times = sorted(df["forecast_time"].unique())
city_color_map = {c: CITY_COLORS[i % len(CITY_COLORS)] for i, c in enumerate(all_cities)}

# ── City selector ──────────────────────────────────────────────────────────
# "All Cities" is a virtual first option — when selected (default) it means
# all cities. Remove clutter: user sees one chip instead of ten.
with city_placeholder:
    city_opts = [ALL_OPT] + all_cities
    raw_sel   = st.multiselect(
        "Cities", city_opts, default=[ALL_OPT],
        label_visibility="collapsed",
    )

if not raw_sel or ALL_OPT in raw_sel:
    active_cities = all_cities
else:
    active_cities = [c for c in raw_sel if c != ALL_OPT]

# If the user picks specific cities AND keeps "All Cities" ticked, simplify
if ALL_OPT in raw_sel and len(raw_sel) > 1:
    # Quietly drop individual city picks — "All Cities" wins
    active_cities = all_cities

# ── Forecast hour slider ───────────────────────────────────────────────────
time_labels = [pd.Timestamp(t).strftime("%H:%M") for t in forecast_times]
with time_placeholder:
    time_idx = st.select_slider(
        "Hour", options=list(range(len(forecast_times))),
        format_func=lambda i: time_labels[i], value=0,
        label_visibility="collapsed",
    )
selected_time = forecast_times[time_idx]

# ── Data source badge ──────────────────────────────────────────────────────
src_color = "#00ff88" if source == "PostgreSQL" else "#ffcc00"
with source_placeholder:
    st.markdown(f"""
    <div class="src-badge">
        <span style="width:8px;height:8px;border-radius:50%;
                     background:{src_color};display:inline-block;"></span>
        <span style="color:{src_color};font-size:0.75rem;font-weight:700;">{source}</span>
        <span style="color:rgba(255,255,255,0.3);font-size:0.7rem;">· data source</span>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Filtered dataframes
# ──────────────────────────────────────────────────────────────────────────────
city_df    = df[df["city"].isin(active_cities)].copy()
trend_df   = city_df.copy()
current_df = city_df[
    (city_df["forecast_time"] == selected_time) &
    (city_df["precipitation_probability"] >= min_rain)
].copy()


# ──────────────────────────────────────────────────────────────────────────────
# Hero Banner
# ──────────────────────────────────────────────────────────────────────────────
latest_refresh = df["loaded_at"].max()
now_str  = datetime.now().strftime("%A, %d %B %Y")
hour_str = datetime.now().strftime("%H:%M IST")

st.markdown(f"""
<div class="hero">
    <div class="hero-eyebrow">
        <span class="live-dot"></span>
        Live Weather · Updated {latest_refresh.strftime("%H:%M:%S")}
    </div>
    <h1 class="hero-title">🇮🇪 Ireland Weather Hub</h1>
    <p class="hero-sub">Real-time rainfall monitoring &amp; 24-hour forecasting across 10 Irish cities</p>
    <div class="hero-meta">
        <span class="hero-chip">📅 <strong>{now_str}</strong></span>
        <span class="hero-chip">🕐 <strong>{hour_str}</strong></span>
        <span class="hero-chip">🏙️ <strong>{len(active_cities)}</strong> cities active</span>
        <span class="hero-chip">📡 <strong>{source}</strong></span>
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# KPI Cards
# ──────────────────────────────────────────────────────────────────────────────
if not current_df.empty:
    highest_prob   = current_df["precipitation_probability"].max()
    avg_temp       = current_df["temperature"].mean()
    active_rain_zn = current_df[current_df["precipitation_probability"] >= 70]["city"].nunique()
    wettest_row    = current_df.loc[current_df["precipitation"].idxmax()]
    wettest_city   = wettest_row["city"]
    wettest_precip = wettest_row["precipitation"]
else:
    highest_prob = avg_temp = active_rain_zn = wettest_precip = 0
    wettest_city = "N/A"

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card blue">
        <div class="kpi-top-bar"></div>
        <div class="kpi-icon">💧</div>
        <div class="kpi-label">Peak Rain Probability</div>
        <div class="kpi-value">{highest_prob:.0f}<span style="font-size:1rem;font-weight:500">%</span></div>
        <div class="kpi-sub">Across selected cities</div>
        <div class="kpi-glow"></div>
    </div>
    <div class="kpi-card teal">
        <div class="kpi-top-bar"></div>
        <div class="kpi-icon">🌊</div>
        <div class="kpi-label">Wettest Location</div>
        <div class="kpi-value" style="font-size:1.4rem;padding-top:0.2rem">{wettest_city}</div>
        <div class="kpi-sub">{wettest_precip:.1f} mm precipitation</div>
        <div class="kpi-glow"></div>
    </div>
    <div class="kpi-card amber">
        <div class="kpi-top-bar"></div>
        <div class="kpi-icon">🌡️</div>
        <div class="kpi-label">Average Temperature</div>
        <div class="kpi-value">{avg_temp:.1f}<span style="font-size:1rem;font-weight:500">°C</span></div>
        <div class="kpi-sub">Mean across selection</div>
        <div class="kpi-glow"></div>
    </div>
    <div class="kpi-card purple">
        <div class="kpi-top-bar"></div>
        <div class="kpi-icon">⚡</div>
        <div class="kpi-label">Active Rain Zones</div>
        <div class="kpi-value">{active_rain_zn}</div>
        <div class="kpi-sub">Cities with ≥70% chance</div>
        <div class="kpi-glow"></div>
    </div>
</div>
""", unsafe_allow_html=True)

prediction_df = load_prediction_history()

if not prediction_df.empty:
    avg_prob = prediction_df["rain_probability"].mean()
    high_risk_count = (prediction_df["risk_level"] == "High").sum()
else:
    avg_prob = 0
    high_risk_count = 0

high_risk_count = (
    prediction_df["risk_level"] == "High"
).sum()

# ──────────────────────────────────────────────────────────────────────────────
# ML Rainfall Prediction
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-hdr">
    <span class="section-hdr-title">🤖 AI Rainfall Prediction</span>
    <div class="section-hdr-line"></div>
    <span style="color:rgba(255,255,255,0.25);font-size:0.72rem;white-space:nowrap;">
        XGBoost Forecasting Engine
    </span>
</div>
""", unsafe_allow_html=True)

ml_city = st.selectbox(
    "Select city for AI prediction",
    sorted(city_df["city"].unique()),
    key="ml_city_select"
)

try:
    prediction_result = predict_city_rain(ml_city)

    pred_col1, pred_col2, pred_col3 = st.columns(3)

    with pred_col1:
        st.markdown(f"""
        <div class="kpi-card blue">
            <div class="kpi-top-bar"></div>
            <div class="kpi-icon">🌧️</div>
            <div class="kpi-label">Rain Probability</div>
            <div class="kpi-value">
                {prediction_result['rain_probability']:.1f}
                <span style="font-size:1rem;font-weight:500">%</span>
            </div>
            <div class="kpi-sub">Predicted for next hour</div>
            <div class="kpi-glow"></div>
        </div>
        """, unsafe_allow_html=True)

    with pred_col2:
        risk_color = {
            "Low": "#00ff88",
            "Medium": "#ffcc00",
            "High": "#ff4d4d"
        }.get(prediction_result["risk_level"], "#00d4ff")

        st.markdown(f"""
        <div class="kpi-card teal">
            <div class="kpi-top-bar"></div>
            <div class="kpi-icon">⚠️</div>
            <div class="kpi-label">Risk Level</div>
            <div class="kpi-value" style="color:{risk_color};">
                {prediction_result['risk_level']}
            </div>
            <div class="kpi-sub">AI weather risk assessment</div>
            <div class="kpi-glow"></div>
        </div>
        """, unsafe_allow_html=True)

    with pred_col3:
        pred_text = (
            "Rain Likely"
            if prediction_result["rain_prediction"] == 1
            else "No Rain Likely"
        )

        pred_icon = (
            "🌧️"
            if prediction_result["rain_prediction"] == 1
            else "☀️"
        )

        st.markdown(f"""
        <div class="kpi-card purple">
            <div class="kpi-top-bar"></div>
            <div class="kpi-icon">{pred_icon}</div>
            <div class="kpi-label">Prediction</div>
            <div class="kpi-value" style="font-size:1.3rem;padding-top:0.2rem;">
                {pred_text}
            </div>
            <div class="kpi-sub">Next hour forecast</div>
            <div class="kpi-glow"></div>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.warning(f"AI prediction unavailable right now: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Recent AI Prediction History
# ──────────────────────────────────────────────────────────────────────────────
prediction_df = load_prediction_history()

st.markdown("""
<div class="section-hdr">
    <span class="section-hdr-title">🧠 Recent AI Predictions</span>
    <div class="section-hdr-line"></div>
    <span style="color:rgba(255,255,255,0.25);font-size:0.72rem;white-space:nowrap;">
        Stored in Neon PostgreSQL
    </span>
</div>
""", unsafe_allow_html=True)

if prediction_df.empty:
    st.info("No AI prediction history found yet. Select a city above to generate predictions.")
else:
    avg_prediction_prob = prediction_df["rain_probability"].mean()
    high_risk_predictions = (prediction_df["risk_level"] == "High").sum()
    latest_prediction_time = prediction_df["prediction_time"].max()

    hist_col1, hist_col2, hist_col3 = st.columns(3)

    with hist_col1:
        st.markdown(f"""
        <div class="kpi-card blue">
            <div class="kpi-top-bar"></div>
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">Avg AI Rain Probability</div>
            <div class="kpi-value">{avg_prediction_prob:.1f}<span style="font-size:1rem;font-weight:500">%</span></div>
            <div class="kpi-sub">Last {len(prediction_df)} predictions</div>
            <div class="kpi-glow"></div>
        </div>
        """, unsafe_allow_html=True)

    with hist_col2:
        st.markdown(f"""
        <div class="kpi-card amber">
            <div class="kpi-top-bar"></div>
            <div class="kpi-icon">🚨</div>
            <div class="kpi-label">High Risk Predictions</div>
            <div class="kpi-value">{high_risk_predictions}</div>
            <div class="kpi-sub">Stored prediction history</div>
            <div class="kpi-glow"></div>
        </div>
        """, unsafe_allow_html=True)

    with hist_col3:
        st.markdown(f"""
        <div class="kpi-card teal">
            <div class="kpi-top-bar"></div>
            <div class="kpi-icon">🕒</div>
            <div class="kpi-label">Latest AI Prediction</div>
            <div class="kpi-value" style="font-size:1.35rem;padding-top:0.2rem;">
                {latest_prediction_time.strftime('%H:%M:%S')}
            </div>
            <div class="kpi-sub">{latest_prediction_time.strftime('%d %b %Y')}</div>
            <div class="kpi-glow"></div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("View recent AI prediction records"):
        display_predictions = prediction_df.copy()
        display_predictions["prediction_time"] = display_predictions["prediction_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        display_predictions["created_at"] = display_predictions["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

        st.dataframe(
            display_predictions,
            use_container_width=True,
            hide_index=True,
            column_config={
                "city": st.column_config.TextColumn("City"),
                "rain_prediction": st.column_config.NumberColumn("Prediction"),
                "rain_probability": st.column_config.NumberColumn("Rain Probability %", format="%.2f"),
                "risk_level": st.column_config.TextColumn("Risk Level"),
                "model_version": st.column_config.TextColumn("Model Version"),
                "prediction_time": st.column_config.TextColumn("Prediction Time"),
                "created_at": st.column_config.TextColumn("Created At"),
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# City Snapshot Grid
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-hdr">
    <span class="section-hdr-title">🏙️ City Snapshots</span>
    <div class="section-hdr-line"></div>
    <span style="color:rgba(255,255,255,0.25);font-size:0.72rem;white-space:nowrap;">
        Selected forecast hour
    </span>
</div>
""", unsafe_allow_html=True)

snapshot_df = city_df[city_df["forecast_time"] == selected_time].copy()

if not snapshot_df.empty:
    cards = '<div class="city-grid">'
    for _, row in snapshot_df.iterrows():
        icon                  = weather_icon(row["precipitation_probability"], row["precipitation"], row["cloud_cover"])
        badge_cls, badge_lbl  = rain_badge(row["precipitation"])
        wlabel                = wind_label(row["wind_speed"])
        cards += f"""
        <div class="city-card">
            <div class="city-icon">{icon}</div>
            <div class="city-name">{row['city']}</div>
            <div class="city-temp">{row['temperature']:.1f}°</div>
            <div class="city-rain">💧 {row['precipitation_probability']:.0f}% · {row['precipitation']:.1f}mm</div>
            <div class="city-wind">{wlabel} · {row['wind_speed']:.0f} km/h</div>
            <div class="rain-badge {badge_cls}">{badge_lbl}</div>
        </div>"""
    cards += "</div>"
    st.markdown(cards, unsafe_allow_html=True)
else:
    st.info("No city data matches the current filters.")


# ──────────────────────────────────────────────────────────────────────────────
# Map — dynamic zoom: fits selected cities; click any dot to zoom in
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-hdr">
    <span class="section-hdr-title">🗺️ Live Rainfall Map</span>
    <div class="section-hdr-line"></div>
    <span style="color:rgba(255,255,255,0.25);font-size:0.72rem;white-space:nowrap;">
        Click a city dot to zoom in · click again to reset
    </span>
</div>
""", unsafe_allow_html=True)

if current_df.empty:
    st.warning("No cities match the current filters — try lowering the rain probability threshold.")
else:
    map_df = current_df.copy()
    map_df["weather_icon"] = map_df.apply(
        lambda r: weather_icon(r["precipitation_probability"], r["precipitation"], r["cloud_cover"]), axis=1
    )
    map_df = map_df.reset_index(drop=True)

    # ── Determine zoom / center ─────────────────────────────────────────────
    zoom_city = st.session_state.get("map_zoom_city")

    if zoom_city and zoom_city in map_df["city"].values:
        # Single-city zoom
        cr         = map_df[map_df["city"] == zoom_city].iloc[0]
        map_zoom   = 10.5
        map_center = {"lat": cr["latitude"], "lon": cr["longitude"]}
        st.markdown(f"""
        <div class="zoom-hint">
            🔍 Zoomed: <strong>{zoom_city}</strong> &nbsp;·&nbsp;
            Click the dot again or use sidebar to reset
        </div>
        """, unsafe_allow_html=True)
    else:
        # Fit all visible cities
        map_zoom, map_center = fit_zoom_center(
            map_df["latitude"].tolist(), map_df["longitude"].tolist()
        )

    # ── Build map ──────────────────────────────────────────────────────────
    # Build traces manually for full layout control
    fig_map = go.Figure()

    fig_map.add_trace(go.Scattermapbox(
        lat=map_df["latitude"].tolist(),
        lon=map_df["longitude"].tolist(),
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=map_df["precipitation_probability"].apply(
                lambda p: 10 + (p / 100) * 28
            ).tolist(),
            color=map_df["precipitation_probability"].tolist(),
            colorscale=[
                [0.00, "#003355"],
                [0.25, "#005599"],
                [0.55, "#0088dd"],
                [0.80, "#00ccff"],
                [1.00, "#00ffee"],
            ],
            cmin=0,
            cmax=100,
            opacity=0.88,
            colorbar=dict(
                title=dict(
                    text="Rain %",
                    font=dict(color="rgba(255,255,255,0.65)", size=11),
                ),
                tickfont=dict(color="rgba(255,255,255,0.55)", size=10),
                bgcolor="rgba(4,10,22,0.75)",
                bordercolor="rgba(255,255,255,0.08)",
                thickness=12,
                len=0.55,
                x=1.01,
            ),
            sizemode="diameter",
        ),
        text=map_df.apply(
            lambda r: (
                f"<b>{r['city']}</b><br>"
                f"🌡 {r['temperature']:.1f}°C<br>"
                f"💧 Rain: {r['precipitation_probability']:.0f}% · {r['precipitation']:.2f}mm<br>"
                f"💦 Humidity: {r['humidity']:.0f}%<br>"
                f"💨 Wind: {r['wind_speed']:.1f} km/h<br>"
                f"☁ Cloud: {r['cloud_cover']:.0f}%<br>"
                f"📊 Pressure: {r['pressure']:.1f} hPa"
            ),
            axis=1,
        ).tolist(),
        hovertemplate="%{text}<extra></extra>",
        customdata=map_df["city"].tolist(),
        name="",
    ))

    # uirevision tied to zoom_city: changes only when programmatic zoom changes,
    # letting the user freely pan/zoom the rest of the time without map reset.
    ui_rev = f"zoom-{zoom_city}" if zoom_city else "free"

    fig_map.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            zoom=map_zoom,
            center=map_center,
            uirevision=ui_rev,
        ),
        uirevision=ui_rev,
        margin=dict(r=0, t=0, l=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="rgba(4,10,22,0.92)",
            bordercolor="rgba(0,212,255,0.35)",
            font=dict(color="white", size=12, family="Inter"),
            align="left",
        ),
        showlegend=False,
        height=580,
        clickmode="event+select",
    )

    # ── Render — scrollZoom enables mouse wheel / trackpad pinch zoom ───────
    map_event = st.plotly_chart(
        fig_map,
        use_container_width=True,
        key="live_map",
        on_select="rerun",
        selection_mode="points",
        config={
            "scrollZoom": True,           # mouse wheel / two-finger trackpad
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage"],
            "toImageButtonOptions": {"format": "png"},
        },
    )

    # Process click → store city for zoom on next render
    if map_event and map_event.selection and map_event.selection.points:
        pt  = map_event.selection.points[0]
        idx = pt.get("point_index", -1)
        if 0 <= idx < len(map_df):
            st.session_state["pending_map_click"] = map_df.iloc[idx]["city"]
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Analytics Tabs
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-hdr">
    <span class="section-hdr-title">📊 24-Hour Analytics</span>
    <div class="section-hdr-line"></div>
</div>
""", unsafe_allow_html=True)

tab_rain, tab_temp, tab_wind, tab_snapshot = st.tabs([
    "🌧️  Rainfall",
    "🌡️  Temperature & Humidity",
    "💨  Wind & Pressure",
    "📸  Hour Snapshot",
])

# ── Rainfall ─────────────────────────────────────────────────────────────────
with tab_rain:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Precipitation (mm)</span>", unsafe_allow_html=True)
        st.plotly_chart(styled_line(trend_df, "precipitation", "mm", city_color_map), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Rain Probability (%)</span>", unsafe_allow_html=True)
        st.plotly_chart(styled_line(trend_df, "precipitation_probability", "%", city_color_map), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if not current_df.empty:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Top Rainfall Locations — Current Hour</span>", unsafe_allow_html=True)
        bar_df = (
            current_df.groupby("city", as_index=False)["precipitation"]
            .max().sort_values("precipitation", ascending=True)
        )
        fig_bar = px.bar(
            bar_df, x="precipitation", y="city", orientation="h",
            color="precipitation", height=340,
            color_continuous_scale=[[0, "#003a66"], [0.5, "#0077cc"], [1, "#00d4ff"]],
            labels={"precipitation": "Precipitation (mm)", "city": ""},
        )
        fig_bar.update_layout(**CHART_BASE, showlegend=False, coloraxis_showscale=False)
        fig_bar.update_traces(marker_line_width=0)
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── Temp & Humidity ───────────────────────────────────────────────────────────
with tab_temp:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Temperature (°C)</span>", unsafe_allow_html=True)
        st.plotly_chart(styled_line(trend_df, "temperature", "°C", city_color_map), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Relative Humidity (%)</span>", unsafe_allow_html=True)
        st.plotly_chart(styled_line(trend_df, "humidity", "%", city_color_map), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if not current_df.empty:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Temperature vs Humidity — Current Hour</span>", unsafe_allow_html=True)
        fig_sc = px.scatter(
            current_df, x="temperature", y="humidity",
            color="city", size="precipitation_probability", text="city", height=400,
            color_discrete_map=city_color_map,
            labels={"temperature": "Temperature (°C)", "humidity": "Humidity (%)", "city": "City"},
        )
        fig_sc.update_traces(textposition="top center", textfont=dict(size=10, color="rgba(255,255,255,0.7)"), marker_line_width=0)
        fig_sc.update_layout(**CHART_BASE)
        st.plotly_chart(fig_sc, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── Wind & Pressure ───────────────────────────────────────────────────────────
with tab_wind:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Wind Speed (km/h)</span>", unsafe_allow_html=True)
        st.plotly_chart(styled_line(trend_df, "wind_speed", "km/h", city_color_map), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Atmospheric Pressure (hPa)</span>", unsafe_allow_html=True)
        st.plotly_chart(styled_line(trend_df, "pressure", "hPa", city_color_map), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if not current_df.empty:
        c3, c4 = st.columns(2)
        with c3:
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Cloud Cover % — Current Hour</span>", unsafe_allow_html=True)
            fig_cloud = go.Figure(go.Barpolar(
                r=current_df["cloud_cover"].tolist(),
                theta=current_df["city"].tolist(),
                marker=dict(
                    color=current_df["cloud_cover"].tolist(),
                    colorscale=[[0, "#002244"], [0.5, "#0055aa"], [1, "#88ccff"]],
                    line_width=0,
                ),
            ))
            fig_cloud.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                polar=dict(
                    bgcolor="rgba(6,14,28,0.55)",
                    radialaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="rgba(255,255,255,0.4)", size=9)),
                    angularaxis=dict(tickfont=dict(color="rgba(255,255,255,0.55)", size=10)),
                ),
                font=dict(color="rgba(255,255,255,0.6)", family="Inter"),
                margin=dict(t=20, b=20, l=20, r=20),
                height=340, showlegend=False,
            )
            st.plotly_chart(fig_cloud, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c4:
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.markdown("<span style='color:rgba(255,255,255,0.55);font-size:0.8rem;font-weight:600;padding-left:0.5rem'>Wind Speed by City — Current Hour</span>", unsafe_allow_html=True)
            fig_wb = px.bar(
                current_df.sort_values("wind_speed", ascending=True),
                x="wind_speed", y="city", orientation="h",
                color="wind_speed", height=340,
                color_continuous_scale=[[0, "#001a33"], [0.5, "#006688"], [1, "#00ccdd"]],
                labels={"wind_speed": "Wind Speed (km/h)", "city": ""},
            )
            fig_wb.update_layout(**CHART_BASE, showlegend=False, coloraxis_showscale=False)
            fig_wb.update_traces(marker_line_width=0)
            st.plotly_chart(fig_wb, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ── Hour Snapshot Radar ───────────────────────────────────────────────────────
with tab_snapshot:
    if current_df.empty:
        st.info("No data for selected hour / filters.")
    else:
        st.markdown(
            f"<p style='color:rgba(255,255,255,0.45);font-size:0.82rem;margin-bottom:1rem'>"
            f"Snapshot at <strong style='color:#00d4ff'>{pd.Timestamp(selected_time).strftime('%H:%M')}"
            f"</strong> · {len(current_df)} cities</p>",
            unsafe_allow_html=True,
        )
        cat_labels = ["Temp", "Humidity", "Rain %", "Wind", "Cloud"]
        fig_radar  = go.Figure()
        for i, (_, row) in enumerate(current_df.iterrows()):
            vals = [
                min(row["temperature"] / 30 * 100, 100),
                row["humidity"],
                row["precipitation_probability"],
                min(row["wind_speed"] / 40 * 100, 100),
                row["cloud_cover"],
            ]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cat_labels + [cat_labels[0]],
                name=row["city"],
                line=dict(color=CITY_COLORS[i % len(CITY_COLORS)], width=2),
                fill="toself",
            ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="rgba(6,14,28,0.55)",
                radialaxis=dict(
                    visible=True, range=[0, 100],
                    gridcolor="rgba(255,255,255,0.06)",
                    tickfont=dict(color="rgba(255,255,255,0.3)", size=8),
                ),
                angularaxis=dict(
                    tickfont=dict(color="rgba(255,255,255,0.6)", size=11),
                    gridcolor="rgba(255,255,255,0.06)",
                ),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(255,255,255,0.6)", family="Inter"),
            legend=dict(
                bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.08)",
                borderwidth=1, font=dict(color="rgba(255,255,255,0.6)", size=10),
            ),
            height=500,
            margin=dict(t=30, b=30, l=40, r=40),
        )
        st.plotly_chart(fig_radar, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# Raw Data
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-hdr" style="margin-top:0.5rem">
    <span class="section-hdr-title">🗃️ Raw Data</span>
    <div class="section-hdr-line"></div>
</div>
""", unsafe_allow_html=True)

with st.expander(f"View dataset — {len(current_df)} rows for selected hour"):
    if current_df.empty:
        st.info("No rows match current filters.")
    else:
        show = current_df.copy()
        show["forecast_time"] = show["forecast_time"].dt.strftime("%Y-%m-%d %H:%M")
        show["loaded_at"]     = show["loaded_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(
            show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "city":          st.column_config.TextColumn("City", width="small"),
                "forecast_time": st.column_config.TextColumn("Forecast Time"),
                "temperature":   st.column_config.NumberColumn("Temp °C",    format="%.1f"),
                "humidity":      st.column_config.NumberColumn("Humidity %",  format="%.0f"),
                "precipitation": st.column_config.NumberColumn("Precip mm",   format="%.2f"),
                "precipitation_probability": st.column_config.ProgressColumn(
                    "Rain Prob", min_value=0, max_value=100, format="%.0f%%"
                ),
                "wind_speed":    st.column_config.NumberColumn("Wind km/h",   format="%.1f"),
                "cloud_cover":   st.column_config.ProgressColumn(
                    "Cloud Cover", min_value=0, max_value=100, format="%.0f%%"
                ),
                "pressure":      st.column_config.NumberColumn("Pressure hPa", format="%.1f"),
                "latitude":      None,
                "longitude":     None,
                "loaded_at":     st.column_config.TextColumn("Loaded At", width="medium"),
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
    Ireland Weather Hub &nbsp;·&nbsp;
    Powered by <a href="https://open-meteo.com"
        style="color:rgba(0,212,255,0.6);text-decoration:none;">Open-Meteo</a>
    &nbsp;·&nbsp; Built with Streamlit
    &nbsp;·&nbsp; Last sync {latest_refresh.strftime("%H:%M:%S")}
    &nbsp;·&nbsp; {source}
</div>
""", unsafe_allow_html=True)
