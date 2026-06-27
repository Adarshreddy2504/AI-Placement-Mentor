import requests

from config import GROQ_API_KEY


def recommend_career(resume_text, interview_report):

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

    return result["choices"][0]["message"]["content"]