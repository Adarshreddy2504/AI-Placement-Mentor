from hindsight_client import Hindsight
from dotenv import load_dotenv
import os

load_dotenv()

client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

BANK_ID = "default"


# -----------------------------
# Generic Functions
# -----------------------------

def save_memory(content):
    try:
        client.retain(
            bank_id=BANK_ID,
            content=content
        )
    except Exception as e:
        print(e)


def search_memory(query):
    try:
        results = client.recall(
            bank_id=BANK_ID,
            query=query
        )

        if not results.results:
            return ""

        memory = ""

        for item in results.results:
            memory += item.text + "\n"

        return memory

    except Exception as e:
        print(e)
        return ""


# -----------------------------
# Structured Memory Functions
# -----------------------------

def save_career_goal(goal):

    save_memory(f"""
Career Goal

User wants to become:
{goal}
""")


def save_resume_summary(summary):

    save_memory(f"""
Resume Summary

{summary}
""")


def save_interview_result(report):

    save_memory(f"""
Interview Report

{report}
""")


def save_learning_progress(progress):

    save_memory(f"""
Learning Progress

{progress}
""")
def save_resume_analysis(analysis):

    save_memory(f"""
Resume Analysis

{analysis}
""")


def save_ats_score(score):

    save_memory(f"""
ATS Score

{score}
""")


def save_missing_skills(skills):

    save_memory(f"""
Missing Skills

{skills}
""")


def save_interview_report(report):

    save_memory(f"""
Interview Report

{report}
""")