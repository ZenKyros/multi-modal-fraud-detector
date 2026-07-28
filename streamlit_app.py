import streamlit as st
import requests
import json
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ─── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Multi‑Modal Fraud Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); }
    .stApp { background: transparent; }
    .stButton button {
        background: linear-gradient(90deg, #06b6d4, #8b5cf6);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
    }
    .stButton button:active { transform: scale(0.98); }
    .stMetric { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 1rem; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
    .stMetric label { color: rgba(255,255,255,0.6); font-weight: 400; }
    .stMetric value { font-size: 2rem; font-weight: 800; }
    .stAlert { border-radius: 12px; backdrop-filter: blur(10px); }
    .sidebar .sidebar-content { background: rgba(15,23,42,0.9); backdrop-filter: blur(10px); }
    .css-1d391kg { background: transparent; }
    .stProgress > div > div { background: linear-gradient(90deg, #06b6d4, #8b5cf6); }
    .stSpinner > div { border-top-color: #8b5cf6 !important; }
    .stTextArea textarea { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; color: white; }
    .stTextArea textarea:focus { border-color: #8b5cf6; }
</style>
""", unsafe_allow_html=True)

# ─── Backend API ──────────────────────────────────────────────
API_URL = "http://localhost:8000"

# ─── Session State ────────────────────────────────────────────
if "transcripts" not in st.session_state:
    st.session_state.transcripts = []
if "threat_index" not in st.session_state:
    st.session_state.threat_index = 0.0
if "pillar_scores" not in st.session_state:
    st.session_state.pillar_scores = {"linguistic": 0.0, "behavioral": 0.0, "acoustic": 0.0}
if "posterior" not in st.session_state:
    st.session_state.posterior = {}
if "payoff_matrix" not in st.session_state:
    st.session_state.payoff_matrix = None
if "defender_equilibrium" not in st.session_state:
    st.session_state.defender_equilibrium = [1/3, 1/3, 1/3]
if "attacker_equilibrium" not in st.session_state:
    st.session_state.attacker_equilibrium = [1/3, 1/3, 1/3]
if "alert" not in st.session_state:
    st.session_state.alert = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_update" not in st.session_state:
    st.session_state.last_update = time.time()

# ─── Helper: Update Dashboard ────────────────────────────────
def update_dashboard(data):
    if "threat_index" in data:
        st.session_state.threat_index = data["threat_index"]
    if "pillar_results" in data:
        for p in ["linguistic", "behavioral", "acoustic"]:
            if p in data["pillar_results"]:
                st.session_state.pillar_scores[p] = data["pillar_results"][p].get("pillar_score", 0.0)
    if "transcripts" in data:
        for t in data["transcripts"]:
            if t and t not in [x["text"] for x in st.session_state.transcripts]:
                st.session_state.transcripts.append({
                    "text": t,
                    "timestamp": data.get("timestamp", time.time()),
                    "is_fraud": data.get("is_fraud", False)
                })
        st.session_state.transcripts = st.session_state.transcripts[-100:]
    if "strategy_weights" in data:
        sw = data["strategy_weights"]
        if "payoff_matrix" in sw:
            st.session_state.payoff_matrix = sw["payoff_matrix"]
        if "defender_equilibrium" in sw:
            st.session_state.defender_equilibrium = sw["defender_equilibrium"]
        if "attacker_equilibrium" in sw:
            st.session_state.attacker_equilibrium = sw["attacker_equilibrium"]
    if "posterior" in data:
        st.session_state.posterior = data["posterior"]
    if "is_fraud" in data and data["is_fraud"]:
        st.session_state.alert = {"type": "danger", "message": "🚨 Fraud Detected!", "details": data.get("verification", {}).get("reasons", ["Multiple indicators"])}
    elif st.session_state.threat_index > 0.4:
        st.session_state.alert = {"type": "warning", "message": "⚠️ Suspicious Activity", "details": "Threat index approaching threshold"}
    else:
        st.session_state.alert = None
    st.session_state.last_update = time.time()

# ─── File Upload Handler ─────────────────────────────────────
def upload_file(file):
    st.session_state.processing = True
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        with st.spinner("⏳ Analysing audio..."):
            response = requests.post(f"{API_URL}/api/upload", files=files, timeout=120)
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Analysis complete!")
            update_dashboard(data)
            if "chunks_processed" in data:
                st.info(f"Processed {data['chunks_processed']} chunks.")
        else:
            st.error(f"Upload failed: {response.text}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        st.session_state.processing = False

# ─── Text Analysis Handler ──────────────────────────────────
def analyze_text(text):
    st.session_state.processing = True
    try:
        with st.spinner("⏳ Analysing text..."):
            response = requests.post(f"{API_URL}/api/analyze_text", json={"text": text}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Text analysis complete!")
            update_dashboard(data)
        else:
            st.error(f"Analysis failed: {response.text}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        st.session_state.processing = False

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🛡️ FraudDetect")
    st.caption("Bayesian Fusion · 3‑Pillar Analysis")

    status = st.empty()
    status.success("🟢 Connected")

    st.divider()

    st.caption("📁 Upload Audio")
    uploaded_file = st.file_uploader("Choose a file", type=["wav","mp3","m4a","webm","flac","ogg"], label_visibility="collapsed")
    if uploaded_file is not None and not st.session_state.processing:
        upload_file(uploaded_file)

    st.caption("📝 Or Paste Conversation")
    pasted_text = st.text_area("", height=120, placeholder="Paste conversation text here...")
    if st.button("Analyze Text", use_container_width=True):
        if pasted_text.strip():
            analyze_text(pasted_text)
        else:
            st.warning("Please paste some text.")

    if st.session_state.processing:
        st.info("⏳ Processing...")

    st.divider()
    st.caption("📊 Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analysis", "Active" if st.session_state.processing else "Idle")
    with col2:
        st.metric("Upload", "Ready" if not st.session_state.processing else "Processing")

# ─── Main Dashboard ──────────────────────────────────────────

# Alert Banner
if st.session_state.alert:
    alert = st.session_state.alert
    if alert["type"] == "danger":
        st.error(f"**{alert['message']}**\n\n{alert['details']}", icon="🚨")
    elif alert["type"] == "warning":
        st.warning(f"**{alert['message']}**\n\n{alert['details']}", icon="⚠️")
    else:
        st.success(f"**{alert['message']}**\n\n{alert['details']}", icon="✅")

# ─── Pillar Scores as Gauges ────────────────────────────────
st.subheader("🎯 Pillar Scores")
cols = st.columns(3)
for i, (pillar, color) in enumerate([("linguistic", "#06b6d4"), ("behavioral", "#10b981"), ("acoustic", "#a855f7")]):
    score = st.session_state.pillar_scores[pillar]
    with cols[i]:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = score * 100,
            title = {"text": pillar.capitalize(), "font": {"color": "white", "size": 18}},
            domain = {"x": [0,1], "y": [0,1]},
            gauge = {
                "axis": {"range": [0,100], "tickwidth": 1, "tickcolor": "white"},
                "bar": {"color": color},
                "steps": [
                    {"range": [0,30], "color": "rgba(255,255,255,0.05)"},
                    {"range": [30,70], "color": "rgba(255,255,255,0.1)"},
                    {"range": [70,100], "color": "rgba(255,255,255,0.15)"}
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 60}
            },
            delta = {"reference": 50, "increasing": {"color": "green"}, "decreasing": {"color": "red"}}
        ))
        fig.update_layout(height=200, margin=dict(l=20,r=20,t=30,b=20), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

# ─── Payoff Matrix & Nash Equilibrium ──────────────────────────
st.subheader("🎯 Payoff Matrix & Nash Equilibrium")

if st.session_state.payoff_matrix:
    matrix = np.array(st.session_state.payoff_matrix)
    def_eq = st.session_state.defender_equilibrium
    att_eq = st.session_state.attacker_equilibrium

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=["Linguistic", "Behavioral", "Acoustic"],
        y=["Linguistic", "Behavioral", "Acoustic"],
        colorscale="Viridis",
        zmin=0, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont={"color": "white"},
        hoverongaps=False
    ))

    # Highlight the Nash equilibrium cell (max value)
    best_cell = np.unravel_index(np.argmax(matrix), matrix.shape)
    fig.add_annotation(
        x=best_cell[1], y=best_cell[0],
        text="⚡ Nash",
        showarrow=False,
        font=dict(color="white", size=14, family="Arial Black"),
        bgcolor="rgba(255,0,0,0.7)",
        borderpad=4
    )

    fig.update_layout(
        title="Payoff Matrix (Defender vs Attacker) · Nash Equilibrium Highlighted",
        xaxis_title="Attacker Strategy",
        yaxis_title="Defender Strategy",
        height=400,
        margin=dict(l=40,r=40,t=60,b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Display equilibrium probabilities
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Defender's Mixed Strategy",
                  f"L:{def_eq[0]*100:.0f}%  B:{def_eq[1]*100:.0f}%  A:{def_eq[2]*100:.0f}%")
    with col2:
        st.metric("Attacker's Mixed Strategy",
                  f"L:{att_eq[0]*100:.0f}%  B:{att_eq[1]*100:.0f}%  A:{att_eq[2]*100:.0f}%")
else:
    st.caption("No payoff matrix yet. Upload a file or paste text to generate one.")

# ─── Threat Level ────────────────────────────────────────────
st.subheader("⚠️ Current Threat Level")
threat = st.session_state.threat_index
color = "red" if threat > 0.55 else "orange" if threat > 0.35 else "green"
st.markdown(f"""
<div style="background: rgba(255,255,255,0.05); border-radius: 16px; padding: 1.5rem; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1);">
    <div style="display: flex; justify-content: space-between; font-weight: 600;">
        <span>Threat Index</span>
        <span style="color:{color};">{threat*100:.1f}%</span>
    </div>
    <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 20px; overflow: hidden; margin: 0.5rem 0;">
        <div style="width: {min(100, threat*100)}%; height: 100%; background: {color}; transition: width 1s ease-in-out;"></div>
    </div>
    <div style="font-size: 0.8rem; opacity: 0.7; text-align: center;">
        { "🚨 High Threat – Fraud Detected" if threat > 0.55 else "⚡ Medium Threat – Monitor" if threat > 0.35 else "✅ Low Threat – Normal Call" }
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Posterior Probabilities ────────────────────────────────
if st.session_state.posterior:
    st.subheader("🧠 Call Type Probabilities")
    post = st.session_state.posterior
    df = pd.DataFrame({
        "Type": ["Normal", "Bank Scam", "Tech Support", "Government"],
        "Probability": [post.get("normal",0), post.get("bank_scam",0), post.get("tech_support",0), post.get("government",0)]
    })
    df = df.sort_values("Probability", ascending=False)
    fig = go.Figure(go.Bar(
        x=df["Probability"],
        y=df["Type"],
        orientation='h',
        marker_color=["#10b981" if t=="Normal" else "#ef4444" for t in df["Type"]],
        text=[f"{p*100:.1f}%" for p in df["Probability"]],
        textposition="outside"
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        height=200,
        margin=dict(l=20,r=60,t=20,b=20),
        xaxis_range=[0,1],
        transition=dict(duration=500, easing="cubic-in-out")
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── Transcript ──────────────────────────────────────────────
st.subheader("📝 Live Transcript")
if st.session_state.transcripts:
    for entry in st.session_state.transcripts[-10:]:
        if entry["is_fraud"]:
            st.markdown(f'<div style="background: rgba(239,68,68,0.1); border-left: 4px solid #ef4444; padding: 0.5rem; border-radius: 4px; margin: 0.25rem 0;">⚠️ {entry["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background: rgba(255,255,255,0.03); padding: 0.5rem; border-radius: 4px; margin: 0.25rem 0;">{entry["text"]}</div>', unsafe_allow_html=True)
else:
    st.caption("No transcripts yet. Upload a file or paste text.")

# ─── Refresh Button ──────────────────────────────────────────
if st.button("🔄 Refresh", use_container_width=True):
    st.rerun()

# ─── Footer ──────────────────────────────────────────────────
st.caption("Built with ❤️ using Streamlit · Bayesian Fusion · Real‑time Fraud Detection")