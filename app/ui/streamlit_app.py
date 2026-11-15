"""Streamlit chat UI. Talks to the API only; it never touches the database or the model.

uv run streamlit run app/ui/streamlit_app.py
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

import streamlit as st

API_URL = os.environ.get("ETRM_API_URL", "http://127.0.0.1:8000")
if urllib.parse.urlparse(API_URL).scheme not in ("http", "https"):
    raise ValueError("ETRM_API_URL must be an http(s) URL")


def _post(path: str, body: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(  # noqa: S310 - fixed http(s) API URL from config
        API_URL + path, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    # Scheme is validated as http(s) at import time above.
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310  # nosec B310
        result: dict[str, Any] = json.loads(resp.read())
        return result


st.set_page_config(page_title="ETRM knowledge assistant", page_icon="⚡")
st.title("ETRM knowledge assistant")

if "session" not in st.session_state:
    st.info("Simulated login for the POC: choose the client you are signed in as.")
    choice = st.selectbox(
        "Client",
        ["clan_a", "clan_b", "clan_c"],
        format_func=lambda c: {"clan_a": "Clan A", "clan_b": "Clan B", "clan_c": "Clan C"}[c],
    )
    if st.button("Sign in"):
        st.session_state.session = _post("/login", {"client_id": choice})
        st.session_state.messages = []
        st.rerun()
    st.stop()

session = st.session_state.session
st.warning(session["disclosure"], icon="🤖")  # FR5 / EU AI Act Art. 50(1): always visible
st.caption(f"Signed in as {session['client_name']}")
if st.sidebar.button("Sign out"):
    del st.session_state.session
    st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        for c in m.get("citations", []):
            st.caption(f"Source: {c['title']} ({c['doc_id']})")
        if m.get("trace_id"):
            st.caption(f"Trace ID (quote it when reporting a problem): {m['trace_id']}")

if question := st.chat_input("Ask about your trading operations"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    with st.chat_message("assistant"), st.spinner("Searching your documents..."):
        resp = _post("/chat", {"question": question, "history": history}, session["token"])
        st.markdown(resp["answer"])
        for c in resp["citations"]:
            st.caption(f"Source: {c['title']} ({c['doc_id']})")
        st.caption(f"Trace ID (quote it when reporting a problem): {resp['trace_id']}")
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": resp["answer"],
            "citations": resp["citations"],
            "trace_id": resp["trace_id"],
        }
    )
