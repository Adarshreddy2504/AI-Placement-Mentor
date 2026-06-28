# Project Summary

## Goal
Build a multi-feature AI Placement Mentor app (Streamlit + Supabase) with chat, resume analysis, mock interviews, and career recommendations.

## What's Done

### Core Infrastructure
- [x] **Auth system** (`auth.py`) — Supabase-based signup/login/logout with session persistence
- [x] **Supabase integration** (`database.py`) — `check_tables()`, `ensure_profile()`, all DB functions wrapped in try/except with `_is_missing_table()` helper
- [x] **Chat persistence** (`chat.py`) — CRUD for chats/messages via Supabase, graceful fallback when tables don't exist
- [x] **AI provider** (`ai.py`) — LiteLLM with fallback routing, `warmup_ai()`/`is_ready()`, model info tracking
- [x] **DB health gate** in `app.py` — checks tables on startup, shows setup message if missing
- [x] **Profile auto-creation** — `ensure_profile()` called on every page load

### Chat Feature
- [x] Chat sidebar with search, pin, rename, duplicate, delete
- [x] Chat messages loaded from Supabase (not local file)
- [x] Auto-create chat on first user message (not on page load)
- [x] `current_chat_id = None` for new users (empty state)
- [x] `_sync_current_chat()` guards against `None` chat_id
- [x] `_delete_chat()` shows empty state instead of auto-creating new chat

### Chat Streaming
- [x] **Markdown streaming** — single `st.chat_message` + single `st.empty()` placeholder; typing indicator → progressive `st.markdown()` rendering
- [x] Cursor blink (`▌`) during streaming, removed on completion
- [x] Role markers (`role-user`/`role-assistant`) for CSS targeting

### Chat Message Layout (CSS)
- [x] Rewrote from broken `[data-testid="stChatMessageAvatarUser"]` to `:has(.role-user)` / `:has(.role-assistant)` selectors
- [x] Bubble selector changed from `> div:first-child` to `> .stMarkdown`
- [x] All gradients, colors, radius preserved

### Timestamps
- [x] `_make_timestamp()` helper using `datetime.now(timezone.utc).astimezone()` with `"%b %d, %I:%M %p"` format
- [x] Replaced all inline `datetime.now().strftime(...)` calls

### UI Components (`ui.py`)
- [x] `show_auth_ui()` — login/signup tabbed form
- [x] `show_db_setup_message()` — instructions for running setup SQL
- [x] `hero()` — landing page for empty chat state

### Resume Analysis
- [x] Resume upload (PDF/DOCX/TXT)
- [x] AI-powered skill extraction and feedback

### Mock Interview
- [x] Interview question generation (C# focused)
- [x] Answer evaluation with feedback
- [x] Session management (start/end/reset)

### Career Recommendation
- [x] AI-powered career path suggestions

### Mobile
- [x] Sidebar auto-close on outside tap (JS in top bar)

## What's Changed This Session

### Performance Optimization
- [x] **Timing instrumentation** — `_t()` / `_t_report()` markers throughout `app.py` print a per-run timing report to terminal
- [x] **Cached DB health check** — `check_tables()` result stored in `_db_ok` after first success; re-checks only if a DB operation fails
- [x] **Cached profile ensure** — `ensure_profile()` result stored in `_profile_ensured` after first success
- [x] **Cached CSS injection** — 1675‑line `styles.css` injected only once via `_css_injected` guard
- [x] **Cached JS injection** — top‑bar JS iframe injected only once via `_js_booted` guard
- [x] **Cached keyboard shortcuts** — audio‑image CSS‑hack injected only once via `_ks_injected` guard

### Chat Architecture
- [x] **Auto‑create first chat** — new users get a chat created in init, never see `current_chat_id = None`
- [x] **Delete‑last‑chat redirect** — `_delete_chat()` calls `_new_chat()` when removing the last chat

### Reasoning/Planning Filtering
- [x] **Expanded `_strip_reasoning()` in `ai.py`** — from 6 regex patterns to a 6‑stage pipeline:
  1. XML/HTML blocks (`<thinking>...</thinking>`, `<reasoning>...</reasoning>`, etc.)
  2. BBcode blocks (`[Thinking]...[/Thinking]`)
  3. Fenced code blocks (`` ```thinking ... ``` ``)
  4. Inline markdown markers (`**Thinking:**`, `*Thought:*`, etc.) through blank line — headings (`## Reasoning`) stripped but `## Analysis` preserved as legit answer section
  5. Preamble reasoning sentences at start of text (10 patterns: "let me", "i need to", "before we", "from previous conversation", "first,", "okay,", "alright,", "the user", "to answer this", "as an ai") — stripped repeatedly until real content reached, with "Let me know" excluded
  6. Clean up of excessive blank lines
- [x] **System prompt updated** in `ask_ai()` — removed "Use previous conversation" (triggered conversation restating); added "Respond directly and concisely. Never include reasoning, thinking, planning, analysis, or self-talk. Only output the final answer."
- [x] **No CascadeFlow wrapper** in use — chat goes through direct Groq `requests.post()` calls; the `_strip_reasoning()` filter is the single chokepoint applied to `content` field before streaming/saving

### Persistent User Memory (Cross-Chat)
- [x] **New `user_memory` table** — `sql_schema.sql` + `database.py` — key-value store per `user_id` with upsert support
- [x] **`memory.py` rewritten** — removed Hindsight dependency; all functions now keyed by `user_id`; data stored in Supabase `user_memory` table
- [x] **`_build_user_context(user_id)`** in `ai.py` — builds comprehensive context from 5 sources: `user_memory` entries, interview reports (latest 3), tracked weaknesses, learning roadmap (latest), career recommendation (latest)
- [x] **`ask_ai(prompt, user_id)`** — accepts `user_id`, passes it to context builder and memory save functions
- [x] **`analyze_resume(text, user_id)`** — accepts `user_id`, saves resume summary/ATS/missing skills to user-scoped memory
- [x] **`app.py` call sites updated** — `ask_ai(last_user, user_id)`, `analyze_resume(text, user_id)`, `save_interview_report(user_id, fb)`
- [x] **Chat history remains isolated** — each chat stores only its own messages in `messages` table; only the AI's system prompt context is shared via `user_memory`

## Key Constraints
- Must run on free Streamlit Community Cloud (no persistent file writes)
- Supabase free tier (no direct table creation from app)
- Dark/light theme support
- Auth required for all pages

## Relevant Files
- `app.py` — main Streamlit app
- `auth.py` — Supabase auth
- `chat.py` — chat CRUD
- `database.py` — DB utilities
- `ai.py` — AI provider wrapper
- `ui.py` — reusable UI components
- `styles.css` — custom styling
- `memory.py` — interview report generation
- `interview.py` — interview logic
- `career.py` — career recommendations

## Next Steps
- Test end-to-end flow on Streamlit Cloud — verify no stale reruns, keyboard shortcuts still work, message rendering is correct
- Remove any remaining dead code (e.g. `_split_markdown_blocks` in app.py if unused, old `st.chat_message` imports)
- Consider batched chat title generation (currently does a separate API call per new chat)
- Run the updated `sql_schema.sql` in the Supabase SQL Editor to create the `user_memory` table
