"""Streamlit frontend entrypoint."""

import streamlit as st

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

with st.form("user_query_form"):
    query = st.text_area(settings.app.prompt_label, height=150)
    submit = st.form_submit_button("Send")

if submit and query:
    request = UserQuery(query=query)
    monitor.track_event("frontend.prompt", payload=request.model_dump())
    st.info("Sending query to backend...")

    try:
        response = llm_client.generate(prompt=request.query)
        monitor.track_event("frontend.response", payload={"response": response})
        st.success(response)
    except Exception as exc:
        monitor.track_event("frontend.error", payload={"error": str(exc)})
        st.error(
            "Unable to generate a response. Check the backend or GCP Vertex configuration."
        )
