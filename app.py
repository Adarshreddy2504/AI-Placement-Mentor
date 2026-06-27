import streamlit as st
import streamlit.components.v1 as components
import time
import uuid
import json
from datetime import datetime, date, timedelta

from memory import save_interview_report
from ai import ask_ai, analyze_resume
from resume import extract_resume_text
from interview import (
    generate_interview_questions,
    evaluate_answer,
    generate_final_report,
)
from career import recommend_career

import ui
import chat_store

st.set_page_config(
    page_title="AI Placement Mentor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.load_css("styles.css")

# --- theme state ---
if "theme" not in st.session_state:
    params = st.query_params
    t = params.get("t", "dark")
    st.session_state.theme = t if t in ("light", "dark") else "dark"

# --- Top bar (pure HTML buttons, JS injected via iframe) ---
cur_theme = st.session_state.theme
theme_icon = "\U0001f319" if cur_theme == "dark" else "\u2600\ufe0f"
st.markdown(f"""
<div id="top-bar-overlay">
<button id="hamburger-btn" aria-label="Toggle sidebar">\u2630</button>
<button id="theme-toggle-btn" aria-label="Toggle theme">{theme_icon}</button>
</div>
""", unsafe_allow_html=True)

# --- JS via same-origin iframe (not stripped by Streamlit) ---
components.html(f"""
<script>
(function() {{
  var w = window.parent;
  var doc = w.document;
  var el = doc.documentElement;
  if (!el.hasAttribute('data-theme')) el.setAttribute('data-theme', '{cur_theme}');
  if (!el.hasAttribute('data-sidebar-open')) el.setAttribute('data-sidebar-open', 'true');
  if (!w.__apmBooted) {{
    w.__apmBooted = true;
    try {{ var s = w.localStorage.getItem('apm_theme'); if (s && s !== '{cur_theme}' && w.location.search.indexOf('t=') < 0) {{ w.location.search = '?t=' + s; return; }} }} catch(e) {{}}
    try {{ var ss = w.localStorage.getItem('apm_sidebar'); if (ss) el.setAttribute('data-sidebar-open', ss); }} catch(e) {{}}
    try {{ var mq = w.matchMedia('(prefers-color-scheme:light)'); mq.addEventListener('change', function(e) {{ try {{ if (!w.localStorage.getItem('apm_theme')) el.setAttribute('data-theme', e.matches ? 'light' : 'dark'); }} catch(ex) {{}} }}); }} catch(ex) {{}}
  }}
  var b = doc.getElementById('theme-toggle-btn');
  if (b) {{ var t = el.getAttribute('data-theme') || 'dark'; b.textContent = t === 'dark' ? '\\u{{1F319}}' : '\\u{{2600}}\\u{{FE0F}}'; }}
  var h = doc.getElementById('hamburger-btn');
  if (h) {{ h.onclick = function() {{
    var e2 = doc.documentElement;
    var c2 = e2.getAttribute('data-sidebar-open');
    var n2 = c2 === 'true' ? 'false' : 'true';
    e2.setAttribute('data-sidebar-open', n2);
    try {{ w.localStorage.setItem('apm_sidebar', n2); }} catch(ex) {{}}
  }}; }}
  var t2 = doc.getElementById('theme-toggle-btn');
  if (t2) {{ t2.onclick = function() {{
    var e3 = doc.documentElement;
    var c3 = e3.getAttribute('data-theme');
    var n3 = c3 === 'dark' ? 'light' : 'dark';
    e3.setAttribute('data-theme', n3);
    this.textContent = n3 === 'dark' ? '\\u{{1F319}}' : '\\u{{2600}}\\u{{FE0F}}';
    try {{ w.localStorage.setItem('apm_theme', n3); }} catch(ex) {{}}
  }}; }}
}})();
</script>
""", height=0)

# --- session state ---
for key in [
    "messages", "interview_started", "interview_questions",
    "interview_finished", "current_question", "feedback",
    "answer_submitted", "interview_results", "career_report",
    "show_uploader", "resume_filename", "resume_analysis",
]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in [
            "messages", "interview_questions", "interview_results"
        ] else (False if key in [
            "interview_started", "interview_finished", "answer_submitted", "show_uploader"
        ] else (""))

if "resume_analysis" in st.session_state and st.session_state.resume_analysis is None:
    st.session_state.resume_analysis = ""

if "resume_filename" in st.session_state and st.session_state.resume_filename is None:
    st.session_state.resume_filename = ""

if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

# --- chat state ---
if "chats" not in st.session_state:
    st.session_state.chats = chat_store.load_chats()
    if not st.session_state.chats:
        cid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        st.session_state.chats[cid] = {
            "id": cid, "title": "New Chat",
            "created_at": now, "updated_at": now,
            "pinned": False, "messages": [],
        }

if "current_chat_id" not in st.session_state:
    sorted_chats = sorted(
        st.session_state.chats.items(),
        key=lambda x: x[1].get("updated_at", x[1]["created_at"]),
        reverse=True,
    )
    st.session_state.current_chat_id = sorted_chats[0][0]
    st.session_state.messages = list(sorted_chats[0][1]["messages"])

if "chat_search" not in st.session_state:
    st.session_state.chat_search = ""
if "rename_chat_id" not in st.session_state:
    st.session_state.rename_chat_id = None
if "delete_chat_id" not in st.session_state:
    st.session_state.delete_chat_id = None

# --- chat functions ---
def _new_chat():
    cid = str(uuid.uuid4())
    now = datetime.now().isoformat()
    st.session_state.chats[cid] = {
        "id": cid, "title": "New Chat",
        "created_at": now, "updated_at": now,
        "pinned": False, "messages": [],
    }
    st.session_state.current_chat_id = cid
    st.session_state.messages = []
    chat_store.save_chats(st.session_state.chats)

def _select_chat(cid):
    st.session_state.current_chat_id = cid
    chat = st.session_state.chats.get(cid)
    if chat:
        st.session_state.messages = list(chat["messages"])

def _delete_chat(cid):
    if cid in st.session_state.chats:
        del st.session_state.chats[cid]
    if st.session_state.current_chat_id == cid:
        if st.session_state.chats:
            sorted_c = sorted(
                st.session_state.chats.items(),
                key=lambda x: x[1].get("updated_at", x[1]["created_at"]), reverse=True,
            )
            _select_chat(sorted_c[0][0])
        else:
            _new_chat()
    chat_store.save_chats(st.session_state.chats)

def _toggle_pin(cid):
    if cid in st.session_state.chats:
        st.session_state.chats[cid]["pinned"] = not st.session_state.chats[cid]["pinned"]
        st.session_state.chats[cid]["updated_at"] = datetime.now().isoformat()
    chat_store.save_chats(st.session_state.chats)

def _rename_chat(cid, title):
    if cid in st.session_state.chats:
        st.session_state.chats[cid]["title"] = title
        st.session_state.chats[cid]["updated_at"] = datetime.now().isoformat()
    chat_store.save_chats(st.session_state.chats)

def _duplicate_chat(cid):
    chat = st.session_state.chats[cid]
    new_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    st.session_state.chats[new_id] = {
        "id": new_id, "title": chat["title"] + " (Copy)",
        "created_at": now, "updated_at": now,
        "pinned": False, "messages": list(chat["messages"]),
    }
    chat_store.save_chats(st.session_state.chats)

def _generate_chat_title(msg):
    msg = msg.strip().replace("\n", " ")
    if len(msg) > 40:
        return msg[:40] + "..."
    return msg

def _split_markdown_blocks(text):
    blocks = []
    current = []
    in_code = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            current.append(line)
        elif in_code:
            current.append(line)
        elif line.strip() == "":
            if current:
                blocks.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks

def _sync_current_chat():
    if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
        st.session_state.chats[st.session_state.current_chat_id]["messages"] = list(st.session_state.messages)
        st.session_state.chats[st.session_state.current_chat_id]["updated_at"] = datetime.now().isoformat()

def _render_chat_list():
    chats = st.session_state.chats
    search = st.session_state.chat_search.strip().lower()
    current_id = st.session_state.current_chat_id

    if not chats:
        st.markdown('<div class="chat-empty">No conversations yet.</div>', unsafe_allow_html=True)
        return

    filtered = {}
    for cid, chat in chats.items():
        if not search or search in chat["title"].lower():
            filtered[cid] = chat

    today_d = date.today()
    yesterday_d = today_d - timedelta(days=1)
    week_ago_d = today_d - timedelta(days=7)

    groups = {"pinned": [], "today": [], "yesterday": [], "week": [], "older": []}
    for cid, chat in filtered.items():
        try:
            created = datetime.fromisoformat(chat.get("updated_at", chat["created_at"])).date()
        except (ValueError, TypeError):
            created = today_d
        if chat.get("pinned"):
            groups["pinned"].append(cid)
        elif created == today_d:
            groups["today"].append(cid)
        elif created == yesterday_d:
            groups["yesterday"].append(cid)
        elif created >= week_ago_d:
            groups["week"].append(cid)
        else:
            groups["older"].append(cid)

    for key in groups:
        groups[key].sort(key=lambda cid: chats[cid].get("updated_at", chats[cid]["created_at"]), reverse=True)

    group_labels = {"pinned": "\U0001f4cc Pinned", "today": "Today", "yesterday": "Yesterday", "week": "Last 7 Days", "older": "Older"}

    for key, label in group_labels.items():
        ids = groups[key]
        if not ids:
            continue
        st.markdown(f'<div class="chat-group-label">{label}</div>', unsafe_allow_html=True)
        for cid in ids:
            chat = chats[cid]
            active = cid == current_id
            title = chat["title"]

            if st.session_state.rename_chat_id == cid:
                new_title = st.text_input("", value=title, key=f"rin_{cid}", label_visibility="collapsed", placeholder="Chat title...")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("\u2705 Save", key=f"rns_{cid}", use_container_width=True):
                        _rename_chat(cid, new_title)
                        st.session_state.rename_chat_id = None
                        st.rerun()
                with rc2:
                    if st.button("\u274c", key=f"rnc_{cid}", use_container_width=True):
                        st.session_state.rename_chat_id = None
                        st.rerun()
                continue

            if st.session_state.delete_chat_id == cid:
                st.warning(f"Delete \u201c{title}\u201d?")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("\U0001f5d1\ufe0f Delete", key=f"cfd_{cid}", use_container_width=True):
                        _delete_chat(cid)
                        st.session_state.delete_chat_id = None
                        st.rerun()
                with dc2:
                    if st.button("Cancel", key=f"ccl_{cid}", use_container_width=True):
                        st.session_state.delete_chat_id = None
                        st.rerun()
                continue

            cols = st.columns([5, 1, 1])
            with cols[0]:
                sel = "\u25c0 " if active else ""
                btn_label = f"{sel}{title}"
                if st.button(btn_label, key=f"cht_{cid}", use_container_width=True):
                    _sync_current_chat()
                    _select_chat(cid)
                    st.rerun()
            with cols[1]:
                star = "\u2b50" if chat.get("pinned") else "\u2606"
                if st.button(star, key=f"stt_{cid}", help="Toggle pin"):
                    _toggle_pin(cid)
                    st.rerun()
            with cols[2]:
                with st.popover("\u22ee", key=f"m_{cid}"):
                    if st.button("\u270f\ufe0f Rename", key=f"ren_{cid}", use_container_width=True):
                        st.session_state.rename_chat_id = cid
                        st.rerun()
                    if st.button("\U0001f4cb Duplicate", key=f"dup_{cid}", use_container_width=True):
                        _duplicate_chat(cid)
                        st.rerun()
                    chat_json = json.dumps(chat, indent=2, ensure_ascii=False)
                    st.download_button("\U0001f4e5 Export", data=chat_json, file_name=f"{title}.json", mime="application/json", key=f"exp_{cid}", use_container_width=True)
                    st.markdown('<div class="chat-menu-sep"></div>', unsafe_allow_html=True)
                    if st.button("\U0001f5d1\ufe0f Delete", key=f"del_{cid}", use_container_width=True):
                        st.session_state.delete_chat_id = cid
                        st.rerun()

# --- sidebar ---
with st.sidebar:
    ui.sidebar_header()

    # + New Chat
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("+ New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
        _sync_current_chat()
        _new_chat()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Search
    st.text_input("\U0001f50d Search chats\u2026", key="chat_search", placeholder="Search chats\u2026", label_visibility="collapsed")

    # Scrollable chat list
    st.markdown('<div class="chat-list-scroll">', unsafe_allow_html=True)
    _render_chat_list()
    st.markdown("</div>", unsafe_allow_html=True)

    interview_st = "Running" if st.session_state.interview_started else "Not Started"
    if st.session_state.interview_finished:
        interview_st = "Completed"
    ui.dashboard(
        total_chats=len(st.session_state.messages),
        resume_status="Uploaded" if "resume_text" in st.session_state else "Not Uploaded",
        interview_status=interview_st,
        memory_status="Enabled",
        last_model=st.session_state.get("last_model"),
        last_latency=st.session_state.get("last_latency"),
        last_cost=st.session_state.get("last_cost"),
        last_complexity=st.session_state.get("last_complexity"),
    )

    st.markdown('<div class="sidebar-heading">Views</div>', unsafe_allow_html=True)

    cur = st.session_state.current_view
    for vid, vicon, vlabel in [
        ("chat", "\U0001f4ac", "Chat"),
        ("resume", "\U0001f4c4", "Resume Analyzer"),
        ("interview", "\U0001f3a4", "Mock Interview"),
        ("career", "\U0001f3af", "Career"),
    ]:
        cls = "nav-btn-active" if cur == vid else ""
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button(f"{vicon} {vlabel}", key=f"nv_{vid}", use_container_width=True):
            _sync_current_chat()
            st.session_state.current_view = vid
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("\U0001f5d1\ufe0f Clear Chat", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
            st.session_state.chats[st.session_state.current_chat_id]["messages"] = []
            st.session_state.chats[st.session_state.current_chat_id]["updated_at"] = datetime.now().isoformat()
            chat_store.save_chats(st.session_state.chats)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- keyboard shortcuts (client-side) ---
st.markdown(f'''
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
     onload="if(!window.__apmKS){{window.__apmKS=true;
document.addEventListener(\'keydown\',function(e){{
  if(e.ctrlKey&&e.key===\'n\'){{e.preventDefault();
    var nb=document.querySelector(\'.new-chat-btn button\');if(nb)nb.click();}}
  if(e.ctrlKey&&e.key===\'f\'){{e.preventDefault();
    var si=document.querySelector(\'[data-testid*=stTextInput] input\');
    if(si)setTimeout(function(){{si.focus();si.select();}},50);}}
}});
try{{window.__apmCC=\'{st.session_state.current_chat_id}\';}}catch(ex){{}}
}}"
     style="display:none">
''', unsafe_allow_html=True)

# =============================================================
# CHAT VIEW — Instagram DM Style
# =============================================================
if st.session_state.current_view == "chat":

    if len(st.session_state.messages) == 0:
        st.markdown('<div class="home-center">', unsafe_allow_html=True)
        ui.hero()
        st.markdown('</div>', unsafe_allow_html=True)

    now_ts = datetime.now().strftime("%I:%M %p")

    for m in st.session_state.messages:
        ts = m.get("timestamp", "")
        with st.chat_message(m["role"], avatar="🤖" if m["role"] == "assistant" else "🙂"):
            st.markdown(m["content"])
            if ts:
                st.markdown(f'<div class="msg-time">{ts}</div>', unsafe_allow_html=True)
            if m["role"] == "assistant":
                st.markdown(
                    '<div class="msg-actions">'
                    '<button class="msg-action-btn" title="Copy">\U0001f4cb</button>'
                    '<button class="msg-action-btn" title="Regenerate">\U0001f504</button>'
                    '<button class="msg-action-btn" title="Like">\U0001f44d</button>'
                    '<button class="msg-action-btn" title="Dislike">\U0001f44e</button>'
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="msg-actions">'
                    '<button class="msg-action-btn" title="Edit">\u270f\ufe0f</button>'
                    '<button class="msg-action-btn" title="Delete">\U0001f5d1\ufe0f</button>'
                    "</div>",
                    unsafe_allow_html=True,
                )

    prompt = st.chat_input("Message\u2026")

    if prompt:
        now = datetime.now().strftime("%I:%M %p")

        # Add user message with timestamp
        st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": now})

        # Auto-title from first user message
        chat = st.session_state.chats.get(st.session_state.current_chat_id)
        if chat and chat["title"] == "New Chat" and len(chat["messages"]) == 0:
            chat["title"] = _generate_chat_title(prompt)
            chat_store.save_chats(st.session_state.chats)

        _sync_current_chat()
        chat_store.save_chats(st.session_state.chats)

        # Show user message immediately
        with st.chat_message("user", avatar="🙂"):
            st.markdown(prompt)
            st.markdown(f'<div class="msg-time">{now}</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="msg-actions">'
                '<button class="msg-action-btn" title="Edit">\u270f\ufe0f</button>'
                '<button class="msg-action-btn" title="Delete">\U0001f5d1\ufe0f</button>'
                "</div>",
                unsafe_allow_html=True,
            )

        # Show typing indicator
        typing_ph = st.empty()
        with typing_ph:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(
                    '<div class="typing-indicator">'
                    "AI is typing"
                    '<span class="typing-dots">'
                    "<span>.</span><span>.</span><span>.</span>"
                    "</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )

        answer, info = ask_ai(prompt)
        for k in ["model", "latency", "cost", "routing", "complexity"]:
            st.session_state[f"last_{k}"] = info[k]

        # Replace typing indicator with actual response
        typing_ph.empty()
        with st.chat_message("assistant", avatar="🤖"):
            ph = st.empty()
            words = answer.split()
            partial = ""
            for j, w in enumerate(words):
                partial += w + " "
                if j < len(words) - 1:
                    ph.markdown(partial + '<span class="typing-cursor">\u258c</span>', unsafe_allow_html=True)
                else:
                    ph.markdown(partial)
                time.sleep(0.018)

            now = datetime.now().strftime("%I:%M %p")
            st.markdown(f'<div class="msg-time">{now}</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="msg-actions">'
                '<button class="msg-action-btn" title="Copy">\U0001f4cb</button>'
                '<button class="msg-action-btn" title="Regenerate">\U0001f504</button>'
                '<button class="msg-action-btn" title="Like">\U0001f44d</button>'
                '<button class="msg-action-btn" title="Dislike">\U0001f44e</button>'
                "</div>",
                unsafe_allow_html=True,
            )

        st.session_state.messages.append({"role": "assistant", "content": answer, "timestamp": now})
        _sync_current_chat()
        chat_store.save_chats(st.session_state.chats)
        st.rerun()

    st.markdown(
        '<p style="text-align:center;font-size:12px;color:var(--text-muted);margin-top:4px;">'
        "Powered by Groq, Hindsight, Cascadeflow</p>",
        unsafe_allow_html=True,
    )

# =============================================================
# RESUME VIEW
# =============================================================
elif st.session_state.current_view == "resume":

    ui.view_header(
        "📄", "Resume Analyzer",
        "Upload and analyze your resume for ATS scores, missing skills, and improvement suggestions."
    )

    # ── State: analysis complete ──
    if st.session_state.get("resume_analysis_complete"):
        ui.resume_card(st.session_state.resume_filename or "Resume")
        with st.expander("📊 AI Resume Analysis", expanded=True):
            st.markdown(st.session_state.resume_analysis)
        if st.button("🔄 Analyze Another Resume", use_container_width=True, type="primary"):
            for k in ["resume_text", "resume_filename", "resume_analysis", "resume_analysis_complete"]:
                st.session_state.pop(k, None)
            st.session_state.resume_upload_counter = st.session_state.get("resume_upload_counter", 0) + 1
            st.rerun()

    # ── State: analyzing ──
    elif st.session_state.get("resume_analyzing"):
        with st.status("🔍 Analyzing resume...", expanded=True) as status:
            st.write("📄 Extracting text from file...")
            text = st.session_state.get("resume_text")
            if text:
                st.write("✅ Text extracted")
                st.write("🧠 Running AI analysis...")
                analysis = analyze_resume(text)
                if analysis:
                    st.session_state.resume_analysis = analysis
                    st.write("✅ Analysis complete!")
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                else:
                    st.error("Analysis failed. Please try again.")
                    status.update(label="Analysis failed", state="error")
            else:
                st.error("No resume text found. Please upload a valid file.")
                status.update(label="Upload required", state="error")
            st.session_state.resume_analysis_complete = True
            del st.session_state.resume_analyzing
        st.rerun()

    # ── State: upload / file selected ──
    else:
        upload_counter = st.session_state.get("resume_upload_counter", 0)
        uploaded = st.file_uploader(
            "Resume file", type=["pdf", "docx", "txt"],
            key=f"resume_uploader_{upload_counter}",
            label_visibility="collapsed",
        )

        if uploaded:
            st.session_state.resume_filename = uploaded.name
            text = extract_resume_text(uploaded)
            if text:
                st.session_state.resume_text = text
            else:
                st.error("⚠️ Could not extract text. Please upload a valid PDF, DOCX, or TXT file.")

        has_text = "resume_text" in st.session_state

        if st.button(
            "🔍 Analyze Resume",
            disabled=not has_text,
            type="primary",
            use_container_width=True,
        ):
            if has_text:
                st.session_state.resume_analyzing = True
                st.rerun()

        if not has_text:
            st.markdown(
                '<p style="text-align:center;font-size:12px;color:var(--text-muted);margin-top:-4px;">'
                "Supported formats: PDF, DOCX, TXT</p>",
                unsafe_allow_html=True,
            )

# =============================================================
# INTERVIEW VIEW
# =============================================================
elif st.session_state.current_view == "interview":

    ui.view_header(
        "🎤", "Mock Interview",
        "Practice with AI-generated interview questions based on your resume."
    )

    if "resume_text" not in st.session_state:
        ui.glass_card()
        st.warning("⚠️ Please upload your resume first.")
        st.markdown(
            '<p style="text-align:center;color:var(--text-muted);font-size:13px;">'
            "Go to <strong>Resume Analyzer</strong> in the sidebar to upload.</p>",
            unsafe_allow_html=True,
        )
        ui.glass_card_close()
    else:
        if not st.session_state.interview_started:
            ui.glass_card("Get Started", "🎤")
            st.markdown(
                '<p style="color:var(--text-secondary);font-size:14px;margin-bottom:12px;">'
                "Ready to practice? Start a 5-question mock interview tailored to your resume.</p>",
                unsafe_allow_html=True,
            )
            if st.button("🎤 Start Mock Interview", use_container_width=True, type="primary"):
                with st.spinner("Preparing interview questions..."):
                    raw = generate_interview_questions(st.session_state["resume_text"])
                    st.session_state.interview_questions = [
                        q.strip() for q in raw.split("\n")
                        if q.strip() and q.strip()[0].isdigit()
                    ]
                st.session_state.interview_started = True
                st.session_state.current_question = 0
                st.session_state.feedback = ""
                st.session_state.answer_submitted = False
                st.session_state.interview_finished = False
                st.session_state.interview_results = []
                if "final_report" in st.session_state:
                    del st.session_state.final_report
                st.rerun()
            ui.glass_card_close()

        if st.session_state.interview_started:
            qs = [q for q in st.session_state.interview_questions if q.strip()]
            tq = len(qs)

            if st.session_state.current_question < tq:
                prog_pct = st.session_state.current_question / max(tq, 1) * 100
                q_num = st.session_state.current_question + 1

                st.markdown(
                    f'''
                    <div class="interview-question-card">
                        <div class="interview-q-header">
                            <span class="interview-q-badge">Question {q_num} of {tq}</span>
                            <span class="interview-q-difficulty">Difficulty: Medium</span>
                        </div>
                        <div class="interview-q-progress-track">
                            <div class="interview-q-progress-bar" style="width:{prog_pct}%"></div>
                        </div>
                        <div class="interview-q-text">{qs[st.session_state.current_question]}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

                submitted = st.session_state.get("answer_submitted", False)

                if submitted:
                    last = st.session_state.interview_results[-1] if st.session_state.interview_results else {}
                    answer_text = last.get("answer", "")

                    st.markdown(
                        f'''
                        <div class="interview-answer-card">
                            <div class="interview-answer-title">✍️ Your Answer</div>
                            <div class="interview-submitted-answer">{answer_text}</div>
                        </div>
                        ''',
                        unsafe_allow_html=True,
                    )

                    ui.feedback_card(st.session_state.get("feedback", ""))

                    is_last = q_num >= tq
                    btn_label = "\U0001f389 Finish Interview" if is_last else "\u27a1\ufe0f Next Question"
                    if st.button(btn_label, use_container_width=True, type="primary"):
                        if is_last:
                            st.session_state.current_question += 1
                        else:
                            st.session_state.current_question += 1
                            st.session_state.answer_submitted = False
                            st.session_state.feedback = ""
                        st.rerun()
                else:
                    st.markdown('<div class="interview-answer-card">', unsafe_allow_html=True)
                    st.markdown('<div class="interview-answer-title">\u270d\ufe0f Your Answer</div>', unsafe_allow_html=True)
                    ans = st.text_area(
                        "", key=f"ans_{st.session_state.current_question}",
                        height=150, placeholder="Write your answer here...",
                        label_visibility="collapsed",
                    )
                    if st.button("\u2705 Submit Answer", type="primary", use_container_width=True):
                        if ans.strip():
                            with st.spinner("\U0001f916 Evaluating your answer..."):
                                fb = evaluate_answer(
                                    qs[st.session_state.current_question], ans
                                )
                                save_interview_report(fb)
                                st.session_state.feedback = fb
                                st.session_state.answer_submitted = True
                            st.session_state.interview_results.append({
                                "question": qs[st.session_state.current_question],
                                "answer": ans,
                                "feedback": fb,
                            })
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.session_state.interview_finished = True
                st.balloons()
                ui.success_box("Interview Completed!", "Great job! Here's your performance summary.")

                if "final_report" not in st.session_state:
                    with st.spinner("📊 Generating final report..."):
                        st.session_state.final_report = generate_final_report(
                            st.session_state.interview_results
                        )

                with st.expander("🏆 Final Interview Report", expanded=True):
                    st.markdown(st.session_state.final_report)

                if st.session_state.career_report == "":
                    with st.spinner("🎯 Finding best career path..."):
                        st.session_state.career_report = recommend_career(
                            st.session_state["resume_text"],
                            st.session_state.final_report,
                        )

                with st.expander("🎯 Career Recommendation", expanded=True):
                    st.markdown(st.session_state.career_report)

                if st.button("🔄 Start New Interview", use_container_width=True, type="primary"):
                    st.session_state.interview_started = False
                    st.session_state.current_question = 0
                    st.session_state.feedback = ""
                    st.session_state.answer_submitted = False
                    st.session_state.interview_questions = []
                    st.session_state.interview_results = []
                    st.session_state.career_report = ""
                    if "final_report" in st.session_state:
                        del st.session_state.final_report
                    st.rerun()

# =============================================================
# CAREER VIEW
# =============================================================
elif st.session_state.current_view == "career":

    ui.view_header(
        "🎯", "Career Recommendation",
        "Personalized career path based on your resume and interview performance."
    )

    if st.session_state.career_report:
        ui.glass_card()
        st.markdown(st.session_state.career_report)
        ui.glass_card_close()
    elif "resume_text" in st.session_state:
        ui.glass_card("Generate Recommendation", "🎯")
        st.markdown(
            '<p style="color:var(--text-secondary);font-size:14px;margin-bottom:12px;">'
            "Complete a mock interview first to get your personalized career recommendation.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="text-align:center;color:var(--text-muted);font-size:13px;">'
            "Go to <strong>Mock Interview</strong> in the sidebar to start.</p>",
            unsafe_allow_html=True,
        )
        ui.glass_card_close()
    else:
        ui.glass_card()
        st.warning("⚠️ Upload your resume and complete a mock interview to see career recommendations.")
        ui.glass_card_close()
