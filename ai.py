"""AI provider layer — Groq API calls, warmup, response sanitization, model routing."""

import requests
import streamlit as st
import time
from dotenv import load_dotenv

load_dotenv()


def warmup_ai() -> bool:
    """Warm up by making a minimal Groq API call directly.
    Eliminates fragile CascadeFlow / asyncio event-loop management.
    Logs every step to the terminal and stores errors in session state.
    """
    if st.session_state.get("ai_ready", False):
        print("[AI] Already ready, skipping warmup.")
        return True

    print("[AI] === WARMUP START ===")

    from config import GROQ_API_KEY
    api_key = GROQ_API_KEY

    if not api_key:
        msg = "GROQ_API_KEY is not set. Check your .env file."
        print(f"[AI] FAIL: {msg}")
        st.session_state._ai_error = msg
        return False

    print(f"[AI] API key loaded (len={len(api_key)})")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
        "temperature": 0.1,
    }

    last_error = ""
    for attempt in range(3):
        try:
            print(f"[AI] Warmup attempt {attempt + 1}/3 ...")
            start = time.time()
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            elapsed = time.time() - start
            print(f"[AI] HTTP {resp.status_code} in {elapsed:.2f}s")

            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")

            result = resp.json()
            if "choices" not in result:
                raise Exception(f"Unexpected response: {result}")

            print(f"[AI] Warmup SUCCESS (attempt {attempt + 1})")
            st.session_state.ai_ready = True
            st.session_state.pop("_ai_error", None)
            print("[AI] === WARMUP COMPLETE ===")
            return True

        except requests.exceptions.Timeout:
            last_error = f"Request timed out (10s)"
            print(f"[AI] Attempt {attempt + 1}: {last_error}")
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {e}"
            print(f"[AI] Attempt {attempt + 1}: {last_error}")
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            print(f"[AI] Attempt {attempt + 1}: {last_error}")

        if attempt < 2:
            backoff = 2 ** attempt  # 1s, 2s, 4s
            print(f"[AI] Retrying in {backoff}s ...")
            time.sleep(backoff)

    print(f"[AI] === WARMUP FAILED after 3 attempts ===")
    print(f"[AI] Last error: {last_error}")
    st.session_state._ai_error = last_error
    return False


def is_ready() -> bool:
    return st.session_state.get("ai_ready", False)


def get_warmup_error() -> str:
    return st.session_state.get("_ai_error", "")

from memory import (
    search_memory,
    save_career_goal,
    save_learning_progress,
    save_resume_analysis,
    save_ats_score,
    save_missing_skills,
    save_interview_report,
    build_interview_memory_context,
)
from router import route_model, estimate_cost
from config import GROQ_API_KEY
import database


def _strip_reasoning(text: str) -> str:
    """Remove reasoning/thinking/planning sections from model responses.
    Strips known tag formats, preamble sentences, and self-talk patterns.
    """
    import re

    # ── 1. XML/HTML reasoning blocks ──
    text = re.sub(
        r'<(?:thinking|thought|reasoning|analysis|plan)[^>]*>.*?</(?:thinking|thought|reasoning|analysis|plan)>',
        '', text, flags=re.DOTALL | re.IGNORECASE
    )

    # ── 2. BBcode reasoning blocks ──
    text = re.sub(
        r'\[(?:thinking|thought|reasoning|analysis|plan)\].*?\[/(?:thinking|thought|reasoning|analysis|plan)\]',
        '', text, flags=re.DOTALL | re.IGNORECASE
    )

    # ── 3. Fenced reasoning blocks (```thinking ... ```) ──
    text = re.sub(
        r'```(?:thinking|thought|reasoning|analysis|plan)\s*\n.*?```',
        '', text, flags=re.DOTALL | re.IGNORECASE
    )

    # ── 4. Markdown-formatted reasoning markers through blank line ──
    # Strip **Thinking:** / **Thought:** / **Reasoning:** / **Analysis:** markers.
    # For headings (##), only strip thinking/thought/reasoning — NOT "analysis"
    # (which is often a legitimate answer section header).
    text = re.sub(
        r'(?:\*{1,2}(?:thinking|thought|reasoning|analysis)\*{0,2}:|'
        r'#{1,6}\s*(?:thinking|thought|reasoning)).*?(?:\n\n|$)',
        '', text, flags=re.DOTALL | re.IGNORECASE
    )

    # ── 5. Preamble reasoning sentences at start of text ──
    # Each pattern matches a SINGLE sentence that begins with self-talk / planning.
    # Uses [^.!?\n]*[.!?\n]? to match exactly one sentence (not everything to end-of-line),
    # so answer content on the same line survives.
    _S = r'(?:[^.!?\n]*[.!?\n]?)?'  # match one sentence (optional content + optional ending)
    preambles = [
        # "Let me think/analyze/consider/check..."
        rf'^let me (?:think|reason|analyze|consider|check|verify|review|examine|assess|evaluate|determine|figure|plan|prepare|look|see|explain|elaborate|start|begin)\b{_S}',
        # "I need to check/verify/look..."
        rf'^i need to (?:check|verify|look|analyze|consider|understand|review|examine|assess|evaluate|determine|figure|think|reason|plan)\b{_S}',
        # "I should/will/must/can/want (also/just) [any verb]..." — catch ALL self-talk verbs
        rf"^i (?:should|'?ll|need to|want to|have to|must|can)\s+(?:also|then|now|first|just)?\s*\w+{_S}",
        # "I think/believe/feel/suppose/assume/guess/wonder..."
        rf'^i (?:think|believe|feel|suppose|assume|guess|wonder|imagine)\b{_S}',
        # "Before we proceed/continue/move/go..."
        rf'^before we (?:proceed|continue|move|go|answer|respond|dive|jump)\b{_S}',
        # "From previous/prior conversation/chat/message/context..."
        rf'^from (?:previous|prior) (?:conversation|chat|message|context|history)\b{_S}',
        # "First, let me / I'll / I need to / I should / I will / I want to..."
        rf"^first,? (?:let me|i'?ll|i need to|i should|i will|i want to)\b{_S}",
        # "Okay / So / Now / Well / Actually, the / let me / this / that / here / what / I / you / we / first / next..."
        rf"^(?:okay|so|now|well|actually),?\s+(?:the|this|that|let me|here|what|i|you|we|first|next)\b{_S}",
        # "Alright, let me / I'll..."
        rf"^alright,?\s*(?:let me|i'?ll)\b{_S}",
        # "The user is/wants/asked/needs/has/would like/is asking..."
        rf'^the user (?:is|wants|asked|needs|has|would like|is asking)\b{_S}',
        # "To answer/address/respond to this/the/your/that..."
        rf'^to (?:answer|address|respond to) (?:this|the|your|that)\b{_S}',
        # "As an AI/assistant/LLM..."
        rf'^as an (?:ai|assistant|llm)\b{_S}',
        # "Next, let me / I'll / explain / describe / mention / note / say / we..."
        rf"^next,?\s+(?:let me|i'?ll|i|explain|describe|mention|note|say|we)\b{_S}",
        # "Check if/whether/the/for/your/user/their..."
        rf'^check\s+(?:if|whether|the|for|your|user|their)\b{_S}',
        # "Wait... / Wait, let me / Wait, I..."
        rf'^wait,?\s*(?:let me|i|the|\.\.\.)?{_S}',
        # "Here's my/the/what/how..."
        rf"^here's (?:my|the|what|how)\b{_S}",
    ]

    while True:
        matched = False
        for pat in preambles:
            m = re.match(pat, text, re.IGNORECASE)
            if m:
                text = text[m.end():].lstrip()
                matched = True
                break  # restart scanning from the first pattern
        if not matched:
            break

    # ── 6. Strip memory-update / system announcements (silent memory) ──
    text = re.sub(
        r'(?im)^(?:✅\s*)?'
        r'(?:'
        r'no\s+(?:information|data|context|memory|entries)(?:\s+\w+){0,5}\s+(?:exists|found|available|stored)|'
        r'nothing\s+(?:in|found|stored)\s+(?:memory|context)|'
        r'(?:retrieved|fetched|loaded|gathered|found|collected)(?:\s+\w+){0,6}\s+(?:memory|memories|context|information|data)|'
        r'(?:searching|checking|consulting|querying|looking\s+up|accessing|reading)\s+(?:memory|memories|context|storage)|'
        r'(?:memory|memories|context)\b.{0,20}?(?:updated|saved|stored|recorded|found|retrieved|checked|searched|accessed|queried)|'
        r'(?:saved|stored|written|updated|added)(?:\s+\w+){0,3}\s+(?:to|in)\s+(?:memory|memories|context)|'
        r'updated\s+(?:user|name|memory|goal|preference|skill|profile|detail|info)|'
        r'added\s+to\s+(?:long[-\s]term\s+)?(?:[\w-]+\s+)*?memory\b'
        r').*?(?:\n|$)',
        '', text
    )

    # ── 7. Remove leftover double spacing ──
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def sanitize_messages_for_groq(messages):
    """Strip every field except 'role' and 'content' for Groq API compatibility."""
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def _build_user_context(user_id: str) -> str:
    """Build a comprehensive context string from all persistent user data sources.
    Includes: user_memory entries, interview reports, weaknesses, roadmaps, and career recommendations.
    """
    parts = []

    # 1. User memory (career goals, learning progress, resume summary, etc.)
    mem_rows = database.get_user_memory(user_id)
    if mem_rows:
        lines = ["=== PERSISTENT USER MEMORY ==="]
        for r in mem_rows:
            k = r.get("key", "")
            v = r.get("value", "")
            label = k.replace("_", " ").title()
            lines.append(f"- {label}: {v}")
        parts.append("\n".join(lines))

    # 2. Interview performance (latest 3)
    reports = database.get_interview_reports(user_id)
    if reports:
        lines = ["=== PAST INTERVIEW PERFORMANCE ==="]
        for i, r in enumerate(reports[:3], 1):
            score = r.get("overall_score", "?")
            tech = r.get("technical_score", "?")
            comm = r.get("communication_score", "?")
            conf = r.get("confidence_score", "?")
            weak = (r.get("weaknesses") or "")[:200]
            lines.append(f"Interview {i}: Overall={score}/10, Tech={tech}/10, Comm={comm}/10, Conf={conf}/10")
            if weak:
                lines.append(f"  Weaknesses: {weak}")
        parts.append("\n".join(lines))

    # 3. Tracked weaknesses
    weaknesses = database.get_user_weaknesses(user_id)
    active = [w for w in weaknesses if w["status"] in ("active", "improving")]
    if active:
        lines = ["=== TRACKED WEAKNESSES ==="]
        for w in active:
            lines.append(f"- {w['weakness_text']} ({w['status']}, detected {w.get('detected_count', 1)}x)")
        parts.append("\n".join(lines))

    # 4. Latest learning roadmap
    roadmaps = database.get_learning_roadmaps(user_id)
    if roadmaps:
        latest = roadmaps[0].get("roadmap_markdown", "")
        parts.append(f"=== LATEST LEARNING ROADMAP (summary) ===\n{latest[:500]}")

    # 5. Latest career recommendation
    careers = database.get_career_recommendations(user_id)
    if careers:
        latest = careers[0].get("recommendation_markdown", "")
        parts.append(f"=== LATEST CAREER RECOMMENDATION ===\n{latest[:500]}")

    return "\n\n".join(parts)


def ask_ai(prompt, user_id: str = ""):
    """Send a chat prompt to Groq with memory context and model routing; return (answer, info_dict)."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    memory_context = _build_user_context(user_id) if user_id else ""
    print("========== USER CONTEXT ==========")
    print(memory_context)
    print("============================")
    model, complexity, routing_reason = route_model(prompt)

    system_prompt = f"""
You are an AI Placement Mentor.

Respond directly to the user's message.
Do not include internal reasoning, thinking, analysis, or planning.
Never explain your thought process.
Output only the final answer.
Never mention memory, stored information, context, or conversation history.

Format your response in Markdown.
Use headings and bullet points when helpful.
Wrap code inside triple backticks.
Explain code after it.
Mention time and space complexity for coding questions."""

    if "resume_text" in st.session_state:
        system_prompt += f"""

The user has uploaded the following resume:

{st.session_state['resume_text']}

Use this resume whenever the user asks about:
- Resume
- Skills
- Career
- Jobs
- Interview questions
- Learning roadmap
- ATS score
"""

    context_section = ""
    if memory_context:
        context_section = f"""

=== USER CONTEXT ===

{memory_context}"""

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt + context_section
            }
        ] + sanitize_messages_for_groq(st.session_state.messages)
    }

    start = time.time()
    for attempt in range(2):
        try:
            response = requests.post(url, headers=headers, json=data)
            elapsed_ms = (time.time() - start) * 1000
            result = response.json()
            if "choices" not in result:
                raise Exception(f"Groq API error: {result}")
            st.session_state.ai_ready = True
            answer = _strip_reasoning(result["choices"][0]["message"]["content"])
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            cost = estimate_cost(model, prompt_tokens, completion_tokens)
            break
        except Exception as e:
            if attempt == 0:
                time.sleep(0.5)
                continue
            return (
                f"⚠️ **AI request failed:** `{type(e).__name__}: {e}`",
                {"model": "unknown", "latency": 0, "cost": 0, "complexity": "unknown", "routing": "unknown"},
            )

    career_words = [
    "want to become",
    "my goal is",
    "career goal",
    "dream job"
]

    if user_id and any(word in prompt.lower() for word in career_words):
        save_career_goal(user_id, prompt)
    learning_words = [
    "completed",
    "finished",
    "learned",
    "studied"
]

    if user_id and any(word in prompt.lower() for word in learning_words):
        save_learning_progress(user_id, prompt)
    return (
    answer,
    {
        "model": model,
        "latency": elapsed_ms,
        "cost": cost,
        "complexity": complexity,
        "routing": routing_reason,
    }
)
def analyze_resume(resume_text, user_id: str = ""):
    """Analyze a resume via Groq — ATS score, strengths/weaknesses, missing skills, suggested projects, interview questions, learning roadmap."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert resume reviewer.

Analyze the following resume and provide:

1. ATS Score (out of 100)
2. Strengths
3. Weaknesses
4. Missing Skills
5. Suggested Projects
6. Interview Questions
7. Learning Roadmap

Resume:

{resume_text}
"""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    if "choices" not in result:
        return f"Error: {result}"

    analysis = _strip_reasoning(result["choices"][0]["message"]["content"])

    if user_id:
        save_resume_analysis(user_id, analysis)

    # -----------------------
    # Save ATS Score
    # -----------------------

        for line in analysis.split("\n"):
            if "ATS" in line.upper():
                save_ats_score(user_id, line)
                break

    # -----------------------
    # Save Missing Skills
    # -----------------------

        if "Missing Skills" in analysis:
            section = analysis.split("Missing Skills")[-1]
            save_missing_skills(user_id, section[:500])

    return analysis