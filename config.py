"""Environment variable loading — GROQ_API_KEY from .env file."""

from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")