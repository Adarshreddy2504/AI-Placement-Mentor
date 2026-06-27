import requests
import streamlit as st
import asyncio
from dotenv import load_dotenv
from cascadeflow import get_development_agent

load_dotenv()

cascade_agent = get_development_agent()

from memory import (
    search_memory,
    save_career_goal,
    save_learning_progress,
    save_resume_analysis,
    save_ats_score,
    save_missing_skills,
    save_interview_report
)
from router import choose_model
from config import GROQ_API_KEY


def ask_ai(prompt):

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    memory_context = search_memory(
    f"""
Current User Question:

{prompt}

Find any relevant long-term memories that help answer this question.
"""
)
    print("========== MEMORY ==========")
    print(memory_context)
    print("============================")
    model = choose_model(prompt)

    system_prompt = f"""
You are an AI Placement Mentor.

Rules:
- Answer in Markdown.
- Use headings.
- Use bullet points.
- Wrap code inside triple backticks.
- Explain code after it.
- Mention time complexity for coding questions.
- Mention space complexity for coding questions.
- Use previous conversation.
"""

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

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt + f"""

            ===========================
LONG-TERM MEMORY
===========================

{memory_context}

IMPORTANT:

The information above comes from the user's persistent memory.

Rules:

1. If the answer exists in memory, answer from memory.

2. Memory is more important than assumptions.

3. If memory doesn't contain the answer, answer normally.

4. Never ignore relevant memory.

5. Do not invent facts.
            """
            }
        ] + st.session_state.messages
    }

    cascade_result = asyncio.run(
    cascade_agent.run(
        query=prompt,
        messages=data["messages"],
        temperature=0.7,
        max_tokens=1024
    )
)

    answer = cascade_result.content
    model = cascade_result.model_used
    career_words = [
    "want to become",
    "my goal is",
    "career goal",
    "dream job"
]

    if any(word in prompt.lower() for word in career_words):
        save_career_goal(prompt)
    learning_words = [
    "completed",
    "finished",
    "learned",
    "studied"
]

    if any(word in prompt.lower() for word in learning_words):
        save_learning_progress(prompt)
    return (
    answer,
    {
        "model": cascade_result.model_used,
        "latency": cascade_result.latency_ms,
        "cost": cascade_result.total_cost,
        "complexity": cascade_result.complexity,
        "routing": cascade_result.routing_strategy
    }
)
def analyze_resume(resume_text):
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

    analysis = result["choices"][0]["message"]["content"]

    save_resume_analysis(analysis)

# -----------------------
# Save ATS Score
# -----------------------

    for line in analysis.split("\n"):

        if "ATS" in line.upper():

            save_ats_score(line)

            break

# -----------------------
# Save Missing Skills
# -----------------------

    if "Missing Skills" in analysis:

        section = analysis.split("Missing Skills")[-1]

        save_missing_skills(section[:500])

    return analysis