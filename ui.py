from typing import Optional
import streamlit as st


def load_css(path: str = "styles.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def sidebar_header():
    st.markdown(
        """
        <div class="logo-row">
            <div class="logo-icon">🤖</div>
            <div>
                <div class="logo-text">AI Placement <span>Mentor</span></div>
                <div class="logo-sub">Your Career Companion</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dashboard(
    total_chats: int,
    resume_status: str,
    interview_status: str = "Not Started",
    memory_status: str = "Enabled",
    last_model: Optional[str] = None,
    last_latency: Optional[float] = None,
    last_cost: Optional[float] = None,
    last_complexity: Optional[str] = None,
):
    st.markdown('<div class="sidebar-heading">Dashboard</div>', unsafe_allow_html=True)

    rsc = "green" if resume_status == "Uploaded" else "yellow"

    resume_display = f'<span class="dash-item-value {rsc}" style="font-size:12px;">{resume_status}</span>'
    interview_display = f'<span class="dash-item-value yellow" style="font-size:12px;">{interview_status}</span>'

    st.markdown(f"""
    <div class="dash-card">
        <div class="dash-header">
            <span class="dash-header-label">Session</span>
            <span class="dash-header-icon">📊</span>
        </div>
        <div class="dash-grid">
            <div class="dash-item">
                <span class="dash-item-label">💬 Messages</span>
                <span class="dash-item-value">{total_chats}</span>
            </div>
            <div class="dash-item">
                <span class="dash-item-label">📄 Resume</span>
                {resume_display}
            </div>
            <div class="dash-item">
                <span class="dash-item-label">🎤 Interview</span>
                {interview_display}
            </div>
            <div class="dash-item">
                <span class="dash-item-label">🧠 Memory</span>
                <span class="dash-item-value green" style="font-size:12px;">{memory_status}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if last_model is not None:
        st.markdown(f"""
        <div class="dash-card">
            <div class="dash-header">
                <span class="dash-header-label">Last Inference</span>
                <span class="dash-header-icon">⚡</span>
            </div>
            <div class="dash-grid">
                <div class="dash-item">
                    <span class="dash-item-label">Model</span>
                    <span class="dash-item-value accent">{last_model}</span>
                </div>
                <div class="dash-item">
                    <span class="dash-item-label">Latency</span>
                    <span class="dash-item-value">{last_latency:.0f}ms</span>
                </div>
                <div class="dash-item">
                    <span class="dash-item-label">Cost</span>
                    <span class="dash-item-value">${last_cost:.6f}</span>
                </div>
                <div class="dash-item">
                    <span class="dash-item-label">Complexity</span>
                    <span class="dash-item-value">{last_complexity}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-icon">🤖</div>
            <div class="hero-title">AI Placement <span>Mentor</span></div>
            <div class="hero-sub">Crack placements faster with AI-powered resume analysis, mock interviews, and career guidance.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def view_header(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="view-header">
            <div class="view-header-icon">{icon}</div>
            <div class="view-header-text">
                <h2>{title}</h2>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def glass_card(title: str = "", icon: str = ""):
    t = f'<div class="glass-card-title">{icon} {title}</div>' if title else ""
    st.markdown(f'<div class="glass-card">{t}', unsafe_allow_html=True)


def glass_card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def resume_card(filename: str):
    st.markdown(
        f"""
        <div class="resume-card">
            <div class="resume-card-icon">📄</div>
            <div>
                <div class="resume-card-name">{filename}</div>
                <div class="resume-card-status">✓ Uploaded & Analyzed</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def question_card(num: int, total: int, text: str):
    st.markdown(
        f"""
        <div class="interview-card">
            <div class="interview-q-badge">Question {num} of {total}</div>
            <div class="interview-q-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feedback_card(md: str):
    st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
    st.markdown(md)
    st.markdown("</div>", unsafe_allow_html=True)


def success_box(title: str, subtitle: str = ""):
    s = f'<div class="success-box-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="success-box">
            <div class="success-box-icon">🎉</div>
            <div class="success-box-title">{title}</div>
            {s}
        </div>
        """,
        unsafe_allow_html=True,
    )
