import streamlit as st
import tempfile
import base64
import os
import cv2
from dotenv import load_dotenv
from core.video_tools import VideoTools
from core.ai_decision import ask_gemini_decision, find_event_timestamp_with_ai

load_dotenv()

st.set_page_config(page_title="AI 3rd Umpire", page_icon="🏏", layout="wide", initial_sidebar_state="collapsed")

# =============================================
# 🎨  BROADCAST-GRADE CSS & ANIMATIONS
# =============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0a0e1a;
    color: #e2e8f0;
}
.main .block-container { padding: 1.5rem 3rem 3rem 3rem; max-width: 1400px; }
section[data-testid="stSidebar"] { display: none; }

/* ── Hero Header ── */
.hero-header {
    background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 40%, #1a0a2e 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 30% 50%, rgba(99,102,241,0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 50%, rgba(236,72,153,0.05) 0%, transparent 60%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 4.5rem;
    line-height: 1;
    background: linear-gradient(90deg, #6366f1, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    margin: 0;
}
.hero-sub {
    font-size: 1.05rem;
    color: #94a3b8;
    margin-top: 0.5rem;
    letter-spacing: 1px;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,0.2);
    border: 1px solid rgba(99,102,241,0.5);
    color: #a78bfa;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 4px 12px;
    border-radius: 100px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #ef4444;
    border-radius: 50%;
    margin-right: 6px;
    box-shadow: 0 0 8px #ef4444;
    animation: pulse-live 1.5s infinite;
}
@keyframes pulse-live {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px #ef4444; }
    50% { opacity: 0.4; box-shadow: 0 0 2px #ef4444; }
}

/* ── Video Info Pill ── */
.info-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 100px;
    padding: 6px 18px;
    font-size: 0.85rem;
    color: #94a3b8;
    margin-right: 10px;
    margin-bottom: 1rem;
}
.info-pill span { color: #e2e8f0; font-weight: 600; }

/* ── Section Labels ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #6366f1;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(99,102,241,0.4), transparent);
}

/* ── Card Panel ── */
.panel-card {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(10px);
}

/* ── Frame Viewer ── */
.frame-viewer-wrapper {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    border: 2px solid rgba(99,102,241,0.4);
    box-shadow: 0 0 30px rgba(99,102,241,0.15), inset 0 0 60px rgba(0,0,0,0.4);
    background: #000;
    display: flex;
    justify-content: center;
    align-items: center;
}
.frame-label {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.85));
    padding: 1rem 1.2rem 0.7rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}
.frame-number {
    font-family: 'Bebas Neue', cursive;
    font-size: 1.6rem;
    color: #6366f1;
    letter-spacing: 2px;
}
.frame-timestamp {
    font-size: 0.8rem;
    color: #94a3b8;
}
.corner-tl, .corner-tr, .corner-bl, .corner-br {
    position: absolute;
    width: 18px; height: 18px;
    border-color: #6366f1;
    border-style: solid;
    opacity: 0.8;
}
.corner-tl { top: 8px; left: 8px; border-width: 2px 0 0 2px; }
.corner-tr { top: 8px; right: 8px; border-width: 2px 2px 0 0; }
.corner-bl { bottom: 8px; left: 8px; border-width: 0 0 2px 2px; }
.corner-br { bottom: 8px; right: 8px; border-width: 0 2px 2px 0; }

/* ── Nav Buttons ── */
.stButton > button {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.12);
    background: rgba(255,255,255,0.05);
    color: #cbd5e1;
    transition: all 0.25s ease;
    letter-spacing: 0.5px;
}
.stButton > button:hover {
    transform: translateY(-2px);
    background: rgba(99,102,241,0.15);
    border-color: rgba(99,102,241,0.6);
    color: #a78bfa;
    box-shadow: 0 4px 15px rgba(99,102,241,0.2);
}

/* ── Primary Consult Button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    font-size: 1.1rem !important;
    font-weight: 800 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    box-shadow: 0 4px 20px rgba(99,102,241,0.45);
    padding: 0.85rem 0 !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
    box-shadow: 0 8px 30px rgba(99,102,241,0.65) !important;
    transform: translateY(-3px) !important;
}

/* ── Number Inputs & Radios ── */
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: white !important;
    font-family: 'Outfit', sans-serif;
}
.stRadio > div { gap: 0.5rem; }
.stRadio > div > label {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 8px 20px !important;
    transition: all 0.2s;
    cursor: pointer;
}
.stRadio > div > label:hover {
    border-color: rgba(99,102,241,0.5);
    background: rgba(99,102,241,0.08);
}

/* ── Uploader ── */
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed rgba(99,102,241,0.5) !important;
    border-radius: 16px !important;
    background: rgba(99,102,241,0.03) !important;
    transition: all 0.3s ease;
}
[data-testid="stFileUploadDropzone"]:hover {
    background: rgba(99,102,241,0.08) !important;
    border-color: #6366f1 !important;
}

/* ── Evidence Frames ── */
.evidence-frame img { border-radius: 8px; border: 1px solid rgba(99,102,241,0.3); }

/* ── Decision Overlay – OUT ── */
@keyframes slam-in {
    0%   { transform: scale(3) rotate(-5deg); opacity: 0; }
    60%  { transform: scale(0.95) rotate(1deg); opacity: 1; }
    80%  { transform: scale(1.04) rotate(-0.5deg); }
    100% { transform: scale(1) rotate(0deg); }
}
@keyframes red-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.7), 0 0 80px rgba(239,68,68,0.3); }
    50%       { box-shadow: 0 0 0 20px rgba(239,68,68,0), 0 0 120px rgba(239,68,68,0.5); }
}
@keyframes green-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.7), 0 0 80px rgba(34,197,94,0.3); }
    50%       { box-shadow: 0 0 0 20px rgba(34,197,94,0), 0 0 120px rgba(34,197,94,0.5); }
}
@keyframes scanlines {
    0%   { background-position: 0 0; }
    100% { background-position: 0 100%; }
}
@keyframes glow-text {
    0%, 100% { text-shadow: 0 0 20px currentColor, 0 0 40px currentColor; }
    50%       { text-shadow: 0 0 5px currentColor; }
}

.decision-box {
    border-radius: 20px;
    padding: 3rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: slam-in 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}
.decision-box::before {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.05) 3px, rgba(0,0,0,0.05) 4px);
    animation: scanlines 8s linear infinite;
    pointer-events: none;
}
.decision-out {
    background: linear-gradient(135deg, rgba(127,29,29,0.9), rgba(69,10,10,0.95));
    border: 3px solid #ef4444;
    animation: slam-in 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards, red-pulse 2s ease-in-out 0.8s infinite;
}
.decision-not-out {
    background: linear-gradient(135deg, rgba(20,83,45,0.9), rgba(5,46,22,0.95));
    border: 3px solid #22c55e;
    animation: slam-in 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards, green-pulse 2s ease-in-out 0.8s infinite;
}
.decision-inconclusive {
    background: linear-gradient(135deg, rgba(92,68,0,0.9), rgba(51,38,0,0.95));
    border: 3px solid #f59e0b;
}
.decision-word {
    font-family: 'Bebas Neue', cursive;
    font-size: 6rem;
    line-height: 1;
    letter-spacing: 8px;
    animation: glow-text 2s ease-in-out 0.8s infinite;
}
.decision-out .decision-word   { color: #ef4444; }
.decision-not-out .decision-word { color: #22c55e; }
.decision-inconclusive .decision-word { color: #f59e0b; font-size: 4rem; }

.decision-icon  { font-size: 3.5rem; margin-bottom: 0.5rem; }
.decision-label {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 5px;
    text-transform: uppercase;
    opacity: 0.7;
    margin-top: 0.3rem;
}

/* ── Reasoning Box ── */
.reasoning-box {
    background: rgba(15,23,42,0.9);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid #6366f1;
    border-radius: 0 12px 12px 0;
    padding: 1.5rem;
    font-size: 0.95rem;
    line-height: 1.7;
    color: #cbd5e1;
}

/* ── Spinner & Alerts ── */
.stSpinner > div { border-top-color: #6366f1 !important; }
.stAlert { border-radius: 12px !important; }

/* ── Horizontal Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Number Input label ── */
.stNumberInput label, .stRadio label { color: #94a3b8 !important; font-size: 0.85rem !important; }
</style>
""", unsafe_allow_html=True)


# ── HERO HEADER ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-badge"><span class="live-dot"></span>AI-POWERED · GEMINI VISION</div>
    <div class="hero-title">🏏 AI 3RD UMPIRE</div>
    <div class="hero-sub">INTELLIGENT RUN-OUT DETECTION &nbsp;·&nbsp; POWERED BY GOOGLE GEMINI</div>
</div>
""", unsafe_allow_html=True)

# ── API Key Check ─────────────────────────────────────────────────────────────
if not os.getenv("GEMINI_API_KEY"):
    st.warning("⚠️ GEMINI_API_KEY is not set. Please add it to your .env file.")

# ── FILE UPLOADER ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">📂 &nbsp; Load Footage</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("", type=["mp4", "avi", "mov"], label_visibility="collapsed")

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    with st.expander("▶ Watch Original Footage", expanded=False):
        st.video(uploaded_file)

    try:
        vt = VideoTools(video_path)

        # Video metadata pills
        duration_s = vt.total_frames / vt.fps if vt.fps > 0 else 0
        st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <span class="info-pill">🎞 <span>{vt.total_frames}</span> frames</span>
            <span class="info-pill">⚡ <span>{vt.fps:.1f}</span> FPS</span>
            <span class="info-pill">⏱ <span>{duration_s:.1f}s</span> duration</span>
            <span class="info-pill">📹 <span>{uploaded_file.name}</span></span>
        </div>
        """, unsafe_allow_html=True)

        # Init session state
        if 'last_video' not in st.session_state or st.session_state.last_video != uploaded_file.name:
            st.session_state.last_video = uploaded_file.name
            st.session_state.event_idx = int(vt.total_frames / 2)
            st.session_state.ai_processed = False
            st.session_state.ai_msg = ""
            st.session_state.decision_result = None

        # ── TWO-COLUMN LAYOUT ─────────────────────────────────────────────────
        left_col, right_col = st.columns([3, 2], gap="large")

        with left_col:
            # ── FRAME VIEWER ──────────────────────────────────────────────────
            st.markdown('<div class="section-label">🎯 &nbsp; Event Frame Viewer</div>', unsafe_allow_html=True)

            event_idx = st.session_state.event_idx
            frame = vt.get_frame(event_idx)
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
                img_str = base64.b64encode(buffer).decode()
                ts = event_idx / vt.fps if vt.fps > 0 else 0
                st.markdown(f"""
                <div class="frame-viewer-wrapper">
                    <img src="data:image/jpeg;base64,{img_str}"
                         style="max-height: 420px; max-width: 100%; display: block; margin: auto;">
                    <div class="corner-tl"></div>
                    <div class="corner-tr"></div>
                    <div class="corner-bl"></div>
                    <div class="corner-br"></div>
                    <div class="frame-label">
                        <span class="frame-number">FRAME {event_idx}</span>
                        <span class="frame-timestamp">{ts:.3f}s</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── NAVIGATION ────────────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            n1, n2, n3, n4, n5 = st.columns([1, 1, 1.6, 1, 1])
            with n1:
                if st.button("⏮ -10", use_container_width=True):
                    st.session_state.event_idx = max(0, st.session_state.event_idx - 10)
                    st.rerun()
            with n2:
                if st.button("◀  -1", use_container_width=True):
                    st.session_state.event_idx = max(0, st.session_state.event_idx - 1)
                    st.rerun()
            with n3:
                st.markdown(f"""<div style="text-align:center; padding: 8px 0;">
                    <div style="font-size:0.7rem; color:#64748b; letter-spacing:2px; text-transform:uppercase;">Frame</div>
                    <div style="font-family:'Bebas Neue',cursive; font-size:2rem; color:#a78bfa; line-height:1.1;">{event_idx}</div>
                </div>""", unsafe_allow_html=True)
            with n4:
                if st.button("+1  ▶", use_container_width=True):
                    st.session_state.event_idx = min(vt.total_frames - 1, st.session_state.event_idx + 1)
                    st.rerun()
            with n5:
                if st.button("+10 ⏭", use_container_width=True):
                    st.session_state.event_idx = min(vt.total_frames - 1, st.session_state.event_idx + 10)
                    st.rerun()

        with right_col:
            # ── AI DETECTION ──────────────────────────────────────────────────
            st.markdown('<div class="section-label">🤖 &nbsp; AI Detection Mode</div>', unsafe_allow_html=True)
            selection_mode = st.radio("", ["Manual Navigation", "AI Smart Detection"], index=1, horizontal=True, label_visibility="collapsed")

            if selection_mode == "AI Smart Detection":
                if not st.session_state.get('ai_processed', False):
                    with st.spinner("🔭 Uploading footage to Gemini — scanning for stump hit..."):
                        try:
                            timestamp = find_event_timestamp_with_ai(video_path)
                            st.session_state.ai_processed = True
                            if timestamp is None or timestamp == 0.0:
                                st.session_state.ai_msg = "warning|⚠️ Gemini could not confidently locate a run-out moment."
                            else:
                                detected_frame = int(timestamp * vt.fps)
                                st.session_state.event_idx = max(0, min(detected_frame, vt.total_frames - 1))
                                st.session_state.ai_msg = f"success|🤖 Stump-hit detected at **{timestamp:.2f}s** → Frame {st.session_state.event_idx}"
                        except Exception as e:
                            st.session_state.ai_processed = True
                            st.session_state.ai_msg = f"error|AI Detection failed: {e}"
                    st.rerun()

                msg = st.session_state.get('ai_msg', '')
                if msg and "|" in msg:
                    kind, text = msg.split("|", 1)
                    if kind == "success": st.success(text)
                    elif kind == "warning": st.warning(text)
                    else: st.error(text)
                elif msg:
                    st.info(msg)

                if st.button("🔄 Re-scan Footage", use_container_width=True):
                    st.session_state.ai_processed = False
                    st.session_state.ai_msg = ""
                    st.session_state.decision_result = None
                    st.rerun()

            # ── ANALYSIS SETTINGS ─────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">⚙️ &nbsp; Analysis Configuration</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                frame_step = st.number_input("Step Interval", min_value=1, max_value=10, value=2, help="Frames to skip between samples sent to AI.")
            with c2:
                num_before = st.number_input("Frames Before", min_value=0, max_value=5, value=2)
            with c3:
                num_after = st.number_input("Frames After", min_value=0, max_value=5, value=2)

            total_frames_sent = num_before + 1 + num_after
            st.markdown(f"""<div style="font-size:0.8rem; color:#64748b; text-align:center; margin-top:0.3rem;">
                {total_frames_sent} frames · spanning {((num_before + num_after) * frame_step / vt.fps):.2f}s window
            </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            consult_btn = st.button("⚖️  CONSULT 3RD UMPIRE", type="primary", use_container_width=True)

        # ── UMPIRE DECISION (full width below) ────────────────────────────────
        if consult_btn:
            st.session_state.decision_result = None
            event_idx = st.session_state.event_idx
            with st.spinner("📡 Transmitting footage to AI Umpire..."):
                frames = vt.get_frame_range(event_idx, num_before=num_before, num_after=num_after, step=frame_step)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">📽 &nbsp; Evidence Submitted</div>', unsafe_allow_html=True)
            cols = st.columns(len(frames))
            for i, (idx, f) in enumerate(frames):
                with cols[i]:
                    ts_f = idx / vt.fps
                    st.image(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), caption=f"F{idx} · {ts_f:.2f}s", use_container_width=True)

            with st.spinner("🤖 Gemini is deliberating..."):
                try:
                    result = ask_gemini_decision(frames)
                    st.session_state.decision_result = result
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        if st.session_state.get('decision_result'):
            result = st.session_state.decision_result
            decision = result.get('decision', 'UNKNOWN').upper().strip()
            reasoning = result.get('reasoning', 'No reasoning provided.')

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">📺 &nbsp; Umpire Decision</div>', unsafe_allow_html=True)

            if decision == "OUT":
                box_class, icon, label = "decision-out", "🚨", "THE BATSMAN IS"
            elif decision == "NOT OUT":
                box_class, icon, label = "decision-not-out", "✅", "THE BATSMAN IS"
            else:
                box_class, icon, label = "decision-inconclusive", "❓", "DECISION"
                decision = "INCONCLUSIVE"

            st.markdown(f"""
            <div class="decision-box {box_class}">
                <div class="decision-icon">{icon}</div>
                <div class="decision-label">{label}</div>
                <div class="decision-word">{decision}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">🔍 &nbsp; Reasoning</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="reasoning-box">{reasoning}</div>', unsafe_allow_html=True)

    finally:
        vt.release()
        try:
            os.unlink(video_path)
        except:
            pass
