"""Mock interview functions — question generation, answer evaluation, final report generation."""

import requests

from config import GROQ_API_KEY
from ai import _strip_reasoning


def generate_interview_questions(resume_text):
    """Generate 5 interview questions from a resume via Groq."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert technical interviewer.

Based on the resume below, generate EXACTLY 5 interview questions.

Rules:
- Return ONLY the questions.
- No introduction.
- No explanation.
- No conclusion.
- No headings.
- One question per line.
- Number them exactly like this:

1. Tell me about yourself.
2. Explain your Portfolio Website project.
3. What is the difference between HTML and CSS?
4. Explain JavaScript closures.
5. Why should we hire you?

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

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    result = response.json()

    if "choices" not in result:
        return f"Error: {result}"

    return _strip_reasoning(result["choices"][0]["message"]["content"])
def generate_interview_questions_with_memory(resume_text, memory_context):
    """Generate 5 interview questions using past interview memory context."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert technical interviewer.

Based on the resume below, generate EXACTLY 5 interview questions.

Rules:
- Return ONLY the questions.
- No introduction.
- No explanation.
- No conclusion.
- No headings.
- One question per line.
- Number them exactly like this:

1. Tell me about yourself.
2. Explain your Portfolio Website project.
3. What is the difference between HTML and CSS?
4. Explain JavaScript closures.
5. Why should we hire you?

IMPORTANT — The candidate has the following interview history. Tailor questions to revisit weak areas:

{memory_context}

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

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    result = response.json()

    if "choices" not in result:
        return f"Error: {result}"

    return _strip_reasoning(result["choices"][0]["message"]["content"])


def evaluate_answer(question, answer):
    """Evaluate a candidate's answer with score, strengths, weaknesses, and suggestions."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer.

Return ONLY in this format:

# ⭐ Score
8/10

# ✅ Strengths
- Point 1
- Point 2

# ❌ Weaknesses
- Point 1
- Point 2

# 💡 Suggestions
- Point 1
- Point 2
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

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    result = response.json()

    if "choices" not in result:
        return f"Error: {result}"

    return _strip_reasoning(result["choices"][0]["message"]["content"])


def evaluate_answer_with_memory(question, answer, memory_context):
    """Evaluate answer using past interview context to track improvement."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer.

Return ONLY in this format:

# ⭐ Score
8/10

# ✅ Strengths
- Point 1
- Point 2

# ❌ Weaknesses
- Point 1
- Point 2

# 💡 Suggestions
- Point 1
- Point 2

Previous interview context — note whether the candidate is improving on known weak areas:

{memory_context}
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

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    result = response.json()

    if "choices" not in result:
        return f"Error: {result}"

    return _strip_reasoning(result["choices"][0]["message"]["content"])


def generate_structured_report(interview_results):
    """Generate a structured JSON report (scores, strengths, weaknesses) from interview results via Groq."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert technical interviewer.

Below are the interview results of a candidate.

{interview_results}

Return ONLY a JSON object with these exact keys and no other text:

{{
  "overall_score": <0-10>,
  "technical_score": <0-10>,
  "communication_score": <0-10>,
  "confidence_score": <0-10>,
  "strengths": "<comma-separated list>",
  "weaknesses": "<comma-separated list>",
  "improvement_suggestions": "<comma-separated list>",
  "recommended_topics": "<comma-separated list>",
  "hiring_recommendation": "<Strong Hire / Hire / Hold / No Hire>"
}}

Use numbers between 0 and 10 for scores. Use plain text without markdown.
"""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if "choices" not in result:
            return None
        import json as _json
        text = _strip_reasoning(result["choices"][0]["message"]["content"])
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return _json.loads(text[start:end+1])
        return None
    except Exception:
        return None


def generate_final_report(interview_results):
    """Generate a professional markdown interview report with scores, strengths, and recommendations."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an expert technical interviewer.

Below are the interview results of a candidate.

{interview_results}

Generate a professional interview report in Markdown.

Include:

# 🏆 Overall Score (out of 10)

# 💬 Communication Skills

# 💻 Technical Knowledge

# 🧠 Problem Solving

# 💪 Strengths

# 📚 Areas to Improve

# 🎯 Recommended Technologies to Learn

# 🚀 Final Verdict

Keep the report professional and concise.
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

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    result = response.json()

    if "choices" not in result:
        return f"Error: {result}"

    return _strip_reasoning(result["choices"][0]["message"]["content"])