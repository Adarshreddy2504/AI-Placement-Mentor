"""Supabase authentication — sign up, sign in, sign out, session management, cached client."""

import streamlit as st
from supabase import create_client, Client
from typing import Optional


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def sign_up(email: str, password: str) -> tuple[bool, str]:
    """Register a new user via Supabase Auth. Returns (success, error_message)."""
    supabase = get_supabase()
    try:
        result = supabase.auth.sign_up({"email": email, "password": password})
        user = result.user
        session = result.session
        if user:
            st.session_state.supabase_user = {
                "id": user.id,
                "email": user.email,
            }
            if session:
                st.session_state.supabase_session = {
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                }
            return True, ""
        return False, "Signup failed. Please try again."
    except Exception as e:
        msg = str(e)
        if "already registered" in msg.lower():
            return False, "This email is already registered. Please sign in."
        if "password" in msg.lower():
            return False, "Password must be at least 6 characters long."
        return False, msg


def sign_in(email: str, password: str) -> tuple[bool, str]:
    """Sign in via Supabase Auth. Returns (success, error_message)."""
    supabase = get_supabase()
    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = result.user
        session = result.session
        if user and session:
            st.session_state.supabase_user = {
                "id": user.id,
                "email": user.email,
            }
            st.session_state.supabase_session = {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
            }
            return True, ""
        return False, "Invalid email or password."
    except Exception as e:
        msg = str(e)
        if "invalid login credentials" in msg.lower():
            return False, "Invalid email or password."
        return False, msg


def sign_out():
    """Sign out from Supabase and clear all auth-related session state."""
    supabase = get_supabase()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("supabase_user", None)
    st.session_state.pop("supabase_session", None)
    st.session_state.pop("chats", None)
    st.session_state.pop("current_chat_id", None)
    st.session_state.pop("messages", None)


def get_current_user() -> Optional[dict]:
    """Return the current authenticated user dict from session state, or None."""
    return st.session_state.get("supabase_user")


def get_current_session() -> Optional[dict]:
    """Return the current Supabase session dict (access/refresh tokens) or None."""


def is_authenticated() -> bool:
    """Check whether a user is currently signed in."""
    return "supabase_user" in st.session_state
