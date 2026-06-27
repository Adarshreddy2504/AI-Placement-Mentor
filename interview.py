import requests

from config import GROQ_API_KEY


def generate_interview_questions(resume_text):

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

    return result["choices"][0]["message"]["content"]
def evaluate_answer(question, answer):

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

    return result["choices"][0]["message"]["content"]
def generate_final_report(interview_results):

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

    return result["choices"][0]["message"]["content"]