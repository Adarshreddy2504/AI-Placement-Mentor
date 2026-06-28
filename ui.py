"""Reusable Streamlit UI components — auth forms, dashboard cards, headers, DB setup message."""

import functools
import streamlit as st


@functools.lru_cache(maxsize=1)
def _read_css(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_css(path: str = "styles.css"):
    """Inject CSS into the Streamlit DOM. File content is cached after first read."""
    try:
        st.markdown(f"<style>{_read_css(path)}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def sidebar_header():
    """Render the sidebar logo and title block."""
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
):
    """Render the sidebar dashboard card with session stats (messages, resume status, interview, memory)."""
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


def hero():
    """Render the landing page hero section (logo, title, tagline)."""
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
    """Render a standard page header with icon, title, and subtitle."""
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
    """Open a glass-card container with optional title. Must be closed with glass_card_close()."""
    t = f'<div class="glass-card-title">{icon} {title}</div>' if title else ""
    st.markdown(f'<div class="glass-card">{t}', unsafe_allow_html=True)


def glass_card_close():
    """Close a glass-card container opened with glass_card()."""
    st.markdown("</div>", unsafe_allow_html=True)


def resume_card(filename: str):
    """Render a card showing the uploaded resume filename and status."""
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


def feedback_card(md: str):
    """Render a feedback card containing markdown content."""
    st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
    st.markdown(md)
    st.markdown("</div>", unsafe_allow_html=True)


def success_box(title: str, subtitle: str = ""):
    """Render a success/celebration box with optional subtitle."""
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


def show_db_setup_message(missing: list = None, error: str = None):
    """Display instructions for initializing Supabase tables when check_tables() fails."""
    st.markdown(
        """
        <div class="auth-hero">
            <div class="auth-logo">🤖</div>
            <div class="auth-title">AI Placement <span>Mentor</span></div>
            <div class="auth-sub">Database not initialized</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if missing:
        table_list = "\n\n".join(f"* `{t}`" for t in missing)
        st.error(
            f"**Missing database tables:**\n\n{table_list}\n\n"
            "Please run the SQL schema in your Supabase SQL Editor."
        )
    elif error:
        st.error(f"**Database check failed:**\n\n```\n{error}\n```")
    else:
        st.warning(
            "Supabase tables are missing. Please run the SQL schema in your Supabase SQL Editor:\n\n"
            "1. Go to https://supabase.com/dashboard\n"
            "2. Open your project → **SQL Editor**\n"
            "3. Copy and paste the content of **sql_schema.sql**\n"
            "4. Click **Run**\n\n"
            "After running the schema, refresh this page."
        )
    if st.button("\U0001f504 Refresh", use_container_width=True, type="primary"):
        st.rerun()


def show_auth_ui():
    """Render the sign-in / sign-up tabbed form for unauthenticated users."""
    st.markdown(
        """
        <div class="auth-hero">
            <div class="auth-logo">🤖</div>
            <div class="auth-title">AI Placement <span>Mentor</span></div>
            <div class="auth-sub">Sign in to continue your career journey</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

    with tab1:
        with st.form("signin_form", clear_on_submit=False):
            email = st.text_input("Email", key="signin_email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", key="signin_password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    from auth import sign_in
                    ok, msg = sign_in(email, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)

    with tab2:
        with st.form("signup_form", clear_on_submit=False):
            email = st.text_input("Email", key="signup_email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", key="signup_password", placeholder="At least 6 characters")
            confirm = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Repeat your password")
            submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            if submitted:
                if not email or not password or not confirm:
                    st.error("Please fill in all fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    from auth import sign_up
                    ok, msg = sign_up(email, password)
                    if ok:
                        st.success("Account created! You are now signed in.")
                        st.rerun()
                    else:
                        st.error(msg)
