"""Supabase database operations — table checks, profile/settings/CRUD for all entities."""

from datetime import datetime, timezone
from auth import get_supabase


REQUIRED_TABLES = [
    "profiles", "conversations", "messages",
    "user_settings", "uploaded_files", "interview_history", "interview_reports",
    "saved_jobs", "career_recommendations", "user_weaknesses", "learning_roadmaps",
    "user_memory",
]


def check_tables() -> tuple[bool, list]:
    """Check that all required Supabase tables exist. Returns (all_ok, list_of_missing_names)."""
    supabase = get_supabase()
    missing = []

    for tbl in REQUIRED_TABLES:
        print(f"Checking table: {tbl}")
        try:
            supabase.table(tbl).select("*").limit(1).execute()
            print(f"  ✓ OK")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            missing.append(tbl)

    return len(missing) == 0, missing


def ensure_profile(user_id: str, email: str = "") -> bool:
    """Create a profile row and default settings if they don't exist. Returns True if OK."""
    supabase = get_supabase()
    try:
        existing = supabase.table("profiles").select("user_id").eq("user_id", user_id).maybe_single().execute()
        if existing.data:
            return True
        now = datetime.now(timezone.utc).isoformat()
        supabase.table("profiles").insert({
            "user_id": user_id,
            "email": email,
            "full_name": "",
            "created_at": now,
            "updated_at": now,
        }).execute()
        supabase.table("user_settings").upsert({
            "user_id": user_id,
            "theme": "dark",
        }).execute()
        return True
    except Exception:
        return False


def get_profile(user_id: str) -> dict | None:
    """Fetch the user's profile row, or None if it doesn't exist."""
    supabase = get_supabase()
    try:
        result = supabase.table("profiles").select("*").eq("user_id", user_id).maybe_single().execute()
        return result.data
    except Exception:
        return None


def upsert_profile(user_id: str, data: dict):
    """Upsert profile fields (merged with existing data)."""
    supabase = get_supabase()
    record = {"user_id": user_id, "updated_at": datetime.now(timezone.utc).isoformat(), **data}
    try:
        supabase.table("profiles").upsert(record).execute()
    except Exception:
        pass


def get_or_create_settings(user_id: str) -> dict:
    """Return user settings, creating defaults if they don't exist."""
    supabase = get_supabase()
    try:
        result = supabase.table("user_settings").select("*").eq("user_id", user_id).maybe_single().execute()
        if result.data:
            return result.data
        default = {"user_id": user_id, "theme": "dark", "created_at": datetime.now(timezone.utc).isoformat()}
        supabase.table("user_settings").insert(default).execute()
        return default
    except Exception:
        return {"user_id": user_id, "theme": "dark"}


def update_settings(user_id: str, data: dict):
    """Update user settings row in Supabase."""
    supabase = get_supabase()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("user_settings").update(data).eq("user_id", user_id).execute()
    except Exception:
        pass


def save_interview_history(user_id: str, data: dict):
    """Save a raw interview history entry to Supabase."""
    supabase = get_supabase()
    record = {"user_id": user_id, **data, "created_at": datetime.now(timezone.utc).isoformat()}
    try:
        supabase.table("interview_history").insert(record).execute()
    except Exception:
        pass


def save_interview_report_record(user_id: str, data: dict) -> bool:
    """Save a structured interview report (scores, strengths, weaknesses) to interview_reports table."""
    supabase = get_supabase()
    record = {
        "user_id": user_id,
        "session_id": data.get("session_id", ""),
        "overall_score": data.get("overall_score", 0),
        "technical_score": data.get("technical_score", 0),
        "communication_score": data.get("communication_score", 0),
        "confidence_score": data.get("confidence_score", 0),
        "strengths": data.get("strengths", ""),
        "weaknesses": data.get("weaknesses", ""),
        "improvement_suggestions": data.get("improvement_suggestions", ""),
        "recommended_topics": data.get("recommended_topics", ""),
        "hiring_recommendation": data.get("hiring_recommendation", ""),
        "report_text": data.get("report_text", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("interview_reports").insert(record).execute()
        return True
    except Exception:
        return False


def get_interview_reports(user_id: str) -> list:
    """Fetch all interview reports for a user, most recent first."""
    supabase = get_supabase()
    try:
        result = supabase.table("interview_reports").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def save_career_recommendation(user_id: str, data: dict) -> bool:
    """Save a career recommendation (skills, experience, interests, markdown) to Supabase."""
    supabase = get_supabase()
    record = {
        "user_id": user_id,
        "skills": data.get("skills", ""),
        "experience_level": data.get("experience_level", ""),
        "interests": data.get("interests", ""),
        "recommendation_markdown": data.get("recommendation_markdown", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("career_recommendations").insert(record).execute()
        return True
    except Exception:
        return False


def get_career_recommendations(user_id: str) -> list:
    """Fetch all career recommendations for a user, most recent first."""
    supabase = get_supabase()
    try:
        result = supabase.table("career_recommendations").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def save_weakness(user_id: str, data: dict) -> bool:
    """Save a detected weakness to the user_weaknesses table."""
    supabase = get_supabase()
    record = {
        "user_id": user_id,
        "weakness_text": data.get("weakness_text", ""),
        "category": data.get("category", ""),
        "status": data.get("status", "active"),
        "detected_count": data.get("detected_count", 1),
        "last_detected_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        supabase.table("user_weaknesses").insert(record).execute()
        return True
    except Exception:
        return False


def upsert_weakness(user_id: str, weakness_text: str, category: str = "General") -> bool:
    """Upsert a weakness: increment detected_count if it already exists, otherwise insert new."""
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    try:
        existing = supabase.table("user_weaknesses")\
            .select("id, detected_count, status")\
            .eq("user_id", user_id)\
            .eq("weakness_text", weakness_text)\
            .maybe_single()\
            .execute()
        if existing.data:
            new_count = (existing.data.get("detected_count") or 0) + 1
            supabase.table("user_weaknesses").update({
                "detected_count": new_count,
                "last_detected_at": now,
            }).eq("id", existing.data["id"]).execute()
            print(f"[WEAKNESS DB] Updated existing #{existing.data['id']}: count={new_count}")
            return True
        supabase.table("user_weaknesses").insert({
            "user_id": user_id,
            "weakness_text": weakness_text,
            "category": category,
            "status": "active",
            "detected_count": 1,
            "last_detected_at": now,
        }).execute()
        print(f"[WEAKNESS DB] Inserted new: '{weakness_text[:50]}' -> {category}")
        return True
    except Exception as e:
        print(f"[WEAKNESS DB ERROR] upsert_weakness: {e}")
        return False


def get_user_weaknesses(user_id: str) -> list:
    """Fetch all tracked weaknesses for a user, most recent first."""
    supabase = get_supabase()
    try:
        result = supabase.table("user_weaknesses").select("*").eq("user_id", user_id).order("last_detected_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def update_weakness_status(weakness_id: int, status: str) -> bool:
    """Update the status (active/improving/resolved) of a weakness entry."""
    supabase = get_supabase()
    try:
        supabase.table("user_weaknesses").update({"status": status}).eq("id", weakness_id).execute()
        return True
    except Exception:
        return False


def save_learning_roadmap(user_id: str, data: dict) -> bool:
    """Save a generated learning roadmap to Supabase."""
    supabase = get_supabase()
    record = {
        "user_id": user_id,
        "weaknesses_input": data.get("weaknesses_input", ""),
        "roadmap_markdown": data.get("roadmap_markdown", ""),
    }
    try:
        supabase.table("learning_roadmaps").insert(record).execute()
        return True
    except Exception:
        return False


def get_learning_roadmaps(user_id: str) -> list:
    """Fetch all saved learning roadmaps for a user, most recent first."""
    supabase = get_supabase()
    try:
        result = supabase.table("learning_roadmaps").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def get_interview_history(user_id: str) -> list:
    """Fetch raw interview history entries for a user, most recent first."""
    supabase = get_supabase()
    try:
        result = supabase.table("interview_history").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


# ── user_memory (persistent key-value per user) ──


def get_user_memory(user_id: str) -> list:
    """Fetch all persistent memory entries for a user, most recent first."""
    supabase = get_supabase()
    try:
        result = supabase.table("user_memory").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def get_user_memory_by_key(user_id: str, key: str) -> str | None:
    """Fetch the value of a single memory key, or None."""
    supabase = get_supabase()
    try:
        result = supabase.table("user_memory").select("value").eq("user_id", user_id).eq("key", key).maybe_single().execute()
        return result.data["value"] if result.data else None
    except Exception:
        return None


def upsert_user_memory(user_id: str, key: str, value: str) -> bool:
    """Insert or update a persistent memory entry for a user.
    Uses the (user_id, key) unique constraint to upsert.
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("user_memory").upsert({
            "user_id": user_id,
            "key": key,
            "value": value,
            "updated_at": now,
        }, on_conflict=["user_id", "key"]).execute()
        return True
    except Exception as e:
        print(f"[MEMORY DB ERROR] upsert_user_memory: {e}")
        return False
