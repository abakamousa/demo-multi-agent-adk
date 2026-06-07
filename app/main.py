"""Streamlit frontend entrypoint."""

import streamlit as st
from typing import Any

from app.service.vertex_llm import VertexLLMClient
from app.utils.monitoring import LangfuseMonitor
from app.utils.pydantic import UserQuery
from utils.config import load_settings

settings = load_settings()

monitor = LangfuseMonitor()
llm_client = VertexLLMClient(
    project=settings.vertex_ai.project,
    region=settings.vertex_ai.region,
    backend_url=str(settings.app.backend_url),
)

st.set_page_config(
    page_title=settings.app.title,
    page_icon=settings.app.page_icon,
    layout=settings.app.layout,
)
st.title(settings.app.title)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

history: list[dict[str, Any]] = st.session_state.chat_history

for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.button("Clear history"):
    st.session_state.chat_history = []
    st.rerun()

with st.form("user_query_form"):
    query = st.text_area(settings.app.prompt_label, height=150)
    submit = st.form_submit_button("Send")

if submit and query:
    request = UserQuery(query=query)
    history.append({"role": "user", "content": request.query})
    monitor.track_event("frontend.prompt", payload=request.model_dump())
    st.info(f"Sending query to backend at {settings.app.backend_url}...")

    try:
        response = llm_client.generate(prompt=request.query, user_id=request.user_id)
        monitor.track_event("frontend.response", payload={"response": response})
        history.append({"role": "assistant", "content": response})
        st.rerun()
    except Exception as exc:
        monitor.track_event("frontend.error", payload={"error": str(exc)})
        history.append({"role": "assistant", "content": f"Error: {exc}"})
        st.error(f"Unable to generate a response: {exc}")
