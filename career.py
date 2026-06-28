"""Career recommendation functions — Groq API calls for career advice and learning roadmap generation."""

import requests

from config import GROQ_API_KEY
from ai import _strip_reasoning


def recommend_career(resume_text, interview_report):
    """Recommend a career path based on resume and interview report via Groq."""
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an experienced career mentor.

Based on the resume and interview report below, recommend the best career path.

Resume:
{resume_text}

Interview Report:
{interview_report}

Generate the response in Markdown.

Include:

# 🎯 Best Career Match

# 📈 Match Percentage

# 💰 Expected Fresher Salary (India)

# 🏢 Suggested Companies

# 💪 Strengths

# 📚 Skills to Improve

# 🚀 Next Steps
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


def generate_learning_roadmap(weaknesses_text: str, skills_text: str = "") -> str:
    """Generate a personalized learning roadmap (weekly plan, resources, milestones) via Groq."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""
You are a learning and development coach. Create a personalized learning roadmap based on the following weaknesses and skills.

Weaknesses / Areas to Improve:
{weaknesses_text}

Current Skills:
{skills_text if skills_text else "Not specified"}

Generate the response in Markdown. Include:

# 🎯 Learning Roadmap

## 📊 Priority Areas
List the top 3-5 areas to focus on, ordered by impact.

## 📅 Weekly Plan
A week-by-week plan for 4-8 weeks with specific learning goals, resources, and practice exercises.

## 📚 Recommended Resources
For each area, suggest: online courses (Coursera/Udemy/YouTube), books, practice platforms (LeetCode/HackerRank), and documentation.

## ✅ Milestones
Define 3-5 clear milestones with measurable outcomes.

## 💡 Daily Habits
Suggested daily practice routines (15-30 min blocks).
"""
    data = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    if "choices" not in result:
        return f"Error: {result}"
    return _strip_reasoning(result["choices"][0]["message"]["content"])


def recommend_career_standalone(skills: str, experience_level: str, interests: str) -> str:
    """Get a career recommendation from skills/experience/interests alone (no resume needed)."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""
You are an experienced career mentor. Based on the following details, recommend the best career path.

Skills: {skills}
Experience Level: {experience_level}
Interests: {interests}

Generate the response in Markdown.

Include:

# 🎯 Best Career Match

# 📈 Match Percentage

# 💰 Expected Fresher Salary (India)

# 🏢 Suggested Companies

# 💪 Strengths

# 📚 Skills to Improve

# 🚀 Next Steps
"""
    data = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    if "choices" not in result:
        return f"Error: {result}"
    return _strip_reasoning(result["choices"][0]["message"]["content"])