import streamlit as st
from supabase import create_client

from src.models import LeadData


def _get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


def save_lead(lead: LeadData) -> str:
    """Insert lead into Supabase leads table. Returns the new lead's UUID."""
    client = _get_client()
    payload = lead.model_dump()
    # EmailStr serialises to str, but Supabase expects plain str — no conversion needed.
    result = client.table("leads").insert(payload).execute()
    return result.data[0]["id"]
