import json

import streamlit as st
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from aegis.graph.builder import build_graph
from aegis.kb.retriever import KBRetriever
from aegis.llm.router import LLMRouter

DB = "checkpoints.db"

st.set_page_config(page_title="Aegis Review Gate", page_icon="🛡️", layout="wide")
st.title("🛡️ Aegis — Human Review Gate")


@st.cache_resource
def resources():
    return LLMRouter(), KBRetriever()


def make_app():
    router, retriever = resources()
    saver = SqliteSaver.from_conn_string(DB)
    return build_graph(router, retriever=retriever, checkpointer=saver, hitl=True)


with st.sidebar:
    st.header("New ticket")
    default_tid = f"t-{abs(hash(st.session_state.get('seed', ''))) % 10000}"
    tid = st.text_input("Ticket ID", value=default_tid)
    subject = st.text_input("Subject")
    body = st.text_area("Body", height=140)
    if st.button("Process ticket", type="primary", disabled=not (tid and subject and body)):
        app = make_app()
        config = {"configurable": {"thread_id": tid}}
        result = app.invoke({"ticket_id": tid, "subject": subject, "body": body}, config=config)
        state = app.get_state(config)
        if state.next:
            iv = state.tasks[0].interrupts[0].value
            st.session_state.review = {"tid": tid, "payload": iv}
            st.session_state.done = None
        else:
            st.session_state.done = result
            st.session_state.review = None

review = st.session_state.get("review")
done = st.session_state.get("done")

if review:
    p = review["payload"]
    st.subheader(f"⏸ Escalated ticket `{p['ticket_id']}` needs human sign-off")
    c1, c2, c3 = st.columns(3)
    c1.metric("Category", p["category"])
    c2.metric("Priority", p["priority"])
    c3.metric("Status", "awaiting review")
    st.warning(f"**Escalation reason:** {p['escalation_reason']}")
    st.info(f"**Recommended first action:** {p['recommended_action']}")
    st.markdown("**Agent draft reply**")
    st.text_area("draft", value=p["draft_reply"], height=160, key="draft_view", disabled=True)

    edited = st.text_area(
        "Or edit the reply before sending (choose Edit below)", key="edited_reply"
    )
    b1, b2, b3 = st.columns(3)
    decision = None
    if b1.button("✅ Approve"):
        decision = {"action": "approve"}
    elif b3.button("❌ Reject"):
        decision = {"action": "reject"}
    elif b2.button("✏️ Send edited") and edited.strip():
        decision = {"action": "edit", "reply": edited}

    if decision:
        app = make_app()
        config = {"configurable": {"thread_id": review["tid"]}}
        st.session_state.done = app.invoke(Command(resume=decision), config=config)
        st.session_state.review = None
        st.rerun()

elif done:
    status = done.get("approval_status", "auto")
    icon = {"approved": "✅", "edited": "✏️", "rejected": "🚫"}.get(status, "ℹ️")
    suffix = status or "completed without escalation"
    st.subheader(f"{icon} Ticket `{done.get('ticket_id')}` — {suffix}")
    if done.get("final_reply"):
        st.success("**Final reply**")
        st.write(done["final_reply"])
    else:
        st.warning("No reply sent — human will handle this ticket directly.")
    with st.expander("Full pipeline state"):
        st.json(json.dumps({k: v for k, v in done.items()}, default=str))

else:
    st.info("Process a ticket from the sidebar. Escalated tickets pause here for approval.")
