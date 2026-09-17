"""Guided chat interface for the PatchPilot demonstration."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
RELEASE_QUESTION = "Can localization-only release 4.2.1 skip the canary stage?"

PATHS = {
    "unsafe": {
        "step": "1 of 3",
        "title": "Unsafe memory",
        "summary": "See repeated vendor claims become unattributed shared memory.",
    },
    "guarded": {
        "step": "2 of 3",
        "title": "Guarded memory",
        "summary": "Replay the same question with authorization and trust separated.",
    },
    "recovery": {
        "step": "3 of 3",
        "title": "Recovery",
        "summary": "Trace the poisoned rule, quarantine it, and restore clean memory.",
    },
}


def call(method: str, path: str) -> dict[str, Any]:
    response = requests.request(method, f"{API_BASE_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def run_path(path: str) -> dict[str, Any]:
    call("POST", "/demo/reset")
    if path == "unsafe":
        return {"path": path, "result": call("POST", "/demo/unsafe")}
    if path == "guarded":
        return {"path": path, "result": call("POST", "/demo/guarded")}
    poisoned = call("POST", "/demo/unsafe")
    recovered = call("POST", "/demo/rollback")
    return {"path": path, "poisoned": poisoned, "result": recovered}


def status_badge(value: bool, passed: str, failed: str) -> None:
    if value:
        st.success(passed, icon=":material/check_circle:")
    else:
        st.error(failed, icon=":material/cancel:")


def render_message(role: str, content: str, *, avatar: str | None = None) -> None:
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)


def render_unsafe(story: dict[str, Any]) -> None:
    result = story["result"]
    release = result["release_assistant"]
    analytics = result["analytics_assistant"]
    render_message(
        "assistant",
        (
            "**Scenario setup**\n\nA localization vendor submitted the same "
            "unsupported exception in three incident notes. The unsafe "
            "summarizer removed the source and uncertainty, then promoted the "
            "claim into shared memory."
        ),
        avatar=":material/warning:",
    )
    render_message("user", RELEASE_QUESTION, avatar=":material/person:")
    render_message("assistant", release["answer"], avatar=":material/smart_toy:")
    render_message(
        "assistant",
        (
            f"**Analytics assistant:** {analytics['answer']}\n\n"
            "Both assistants read the same promoted-memory index, so the "
            "second answer reinforces the first."
        ),
        avatar=":material/monitoring:",
    )
    render_message(
        "assistant",
        (
            "**What went wrong?** Repetition was treated as corroboration. "
            "Retrieval ranked a highly relevant, auto-approved rule without "
            "checking who supplied it or whether a release authority approved it."
        ),
        avatar=":material/search_insights:",
    )


def render_guarded(story: dict[str, Any]) -> None:
    result = story["result"]
    release = result["release_assistant"]
    claim = result["admitted"][0]
    render_message(
        "assistant",
        (
            "**Same evidence, safer memory admission**\n\nThe guarded path "
            "keeps the vendor identity and all three parent notes. It checks "
            "authorization first, then asks a separate question: should this "
            "claim be trusted as release guidance?"
        ),
        avatar=":material/shield:",
    )
    render_message("user", RELEASE_QUESTION, avatar=":material/person:")
    render_message("assistant", release["answer"], avatar=":material/smart_toy:")
    render_message(
        "assistant",
        (
            f"**Memory admission:** `{claim['status']}`\n\n"
            "The release engineer is allowed to see the vendor claim, but it "
            "cannot guide an agent. Three repetitions came from one source, "
            "and a high-impact rollout exception needs independent corroboration."
        ),
        avatar=":material/policy:",
    )
    render_message(
        "assistant",
        (
            "**Why this answer is safer:** PatchPilot retrieved the approved "
            "release-board rule. Authorization limited exposure; trust "
            "admission decided which accessible memory was authoritative."
        ),
        avatar=":material/fact_check:",
    )


def render_recovery(story: dict[str, Any]) -> None:
    poisoned = story["poisoned"]
    recovered = story["result"]
    render_message(
        "assistant",
        (
            "**Starting from a poisoned conversation**\n\nThe unsafe path "
            "already promoted the vendor rule and both assistants repeated it."
        ),
        avatar=":material/warning:",
    )
    render_message("user", RELEASE_QUESTION, avatar=":material/person:")
    render_message(
        "assistant",
        poisoned["release_assistant"]["answer"],
        avatar=":material/smart_toy:",
    )
    render_message(
        "user",
        "This conflicts with release-board policy. Trace and remove it.",
        avatar=":material/admin_panel_settings:",
    )
    events = recovered["state"]["audit_events"]
    action_text = {
        "quarantine": "Quarantined the poisoned memory so retrieval cannot use it.",
        "invalidate": "Invalidated any memory derived from the poisoned rule.",
        "rollback": "Restored the last clean memory snapshot.",
    }
    for event in events:
        if event["action"] in action_text:
            render_message(
                "assistant",
                f"**{event['action'].title()}**\n\n{action_text[event['action']]}",
                avatar=":material/history:",
            )
    render_message(
        "assistant",
        (
            f"**Replayed question:** {RELEASE_QUESTION}\n\n"
            f"{recovered['query']['answer']}"
        ),
        avatar=":material/verified:",
    )


def render_memory_card(memory: dict[str, Any]) -> None:
    status = memory["status"]
    icon = ":material/verified:" if status == "approved" else ":material/warning:"
    with st.container(border=True):
        st.markdown(f"{icon} **{memory['content']}**")
        st.caption(
            f"Status: {status} · Trust: {memory['trust_score']:.0%} · "
            f"Source: {memory['source_principal']}"
        )
        if memory["parent_evidence_ids"]:
            st.caption(
                "Evidence: " + ", ".join(memory["parent_evidence_ids"])
            )


def render_evidence_panel(story: dict[str, Any]) -> None:
    path = story["path"]
    result = story["result"]
    query = result.get("release_assistant") or result.get("query")
    state = result.get("state", {})
    admitted = result.get("admitted", [])
    memories = query.get("memories", []) if query else state.get("memories", [])

    st.markdown("#### Current context")
    st.markdown("**Persona:** Rina Release")
    st.caption("Group: studio-release-engineers")
    st.markdown(f"**Path:** {PATHS[path]['title']}")

    if query:
        st.markdown("#### Decision gates")
        decisions = query["decisions"]
        authorized = any(item["authorized"] for item in decisions)
        trusted = any(item["trusted"] and item["included"] for item in decisions)
        status_badge(
            authorized,
            "Authorization passed: matching tenant and group",
            "Authorization denied: no accessible memory",
        )
        if path == "unsafe":
            st.warning(
                "Trust gate skipped: relevance alone selected the answer",
                icon=":material/warning:",
            )
        else:
            status_badge(
                trusted,
                "Trust passed: approved guidance selected",
                "Trust failed: no approved guidance selected",
            )
        for decision in decisions:
            with st.expander(
                f"{decision['memory_id']} · relevance "
                f"{decision['relevance_score']:.0%}"
            ):
                st.write(decision["reason"])
                st.metric("Trust score", f"{decision['trust_score']:.0%}")

    st.markdown("#### Memory examined")
    for memory in admitted or memories:
        render_memory_card(memory)

    analytics = result.get("analytics_assistant")
    if analytics:
        st.markdown("#### Shared-memory effect")
        status_badge(
            analytics["answer"] == result["release_assistant"]["answer"],
            "Analytics repeated the release answer",
            "Agents produced different answers",
        )
        status_badge(
            result["self_reinforcement_blocked"],
            "Automatic re-ingestion was blocked",
            "Agent output was re-ingested",
        )

    events = result.get("audit_events") or state.get("audit_events", [])
    if events:
        st.markdown("#### Audit timeline")
        for event in events:
            st.markdown(
                f"**{event['sequence']}. {event['action'].title()}** · "
                f"{event['outcome']}"
            )
            st.caption(event["reason"])

    with st.expander("Developer details"):
        st.json(story)


st.set_page_config(
    page_title="PatchPilot release memory",
    page_icon=":material/memory:",
    layout="wide",
)
st.title("PatchPilot release memory")
st.caption(
    "A guided conversation showing how poisoned context becomes agent memory, "
    "and how authorization, trust, and rollback contain it."
)

try:
    health = call("GET", "/health")
except requests.RequestException as error:
    st.error(f"PatchPilot API is unavailable: {error}")
    st.stop()

cloud_label = "Azure ready" if health["cloud"]["ready"] else "local rehearsal"
st.success(
    f"PatchPilot API is {health['status']} · {cloud_label}",
    icon=":material/cloud_done:",
)

st.markdown("### Choose a walkthrough")
path_columns = st.columns(3)
for column, (path, details) in zip(path_columns, PATHS.items(), strict=True):
    with column:
        with st.container(border=True):
            st.caption(f"STEP {details['step']}")
            st.markdown(f"#### {details['title']}")
            st.write(details["summary"])
            if st.button(
                f"Run {details['title'].lower()}",
                key=f"run-{path}",
                type="primary" if path == "unsafe" else "secondary",
                use_container_width=True,
            ):
                try:
                    with st.spinner(f"Running {details['title'].lower()}..."):
                        st.session_state.story = run_path(path)
                except requests.RequestException as error:
                    st.error(f"The walkthrough failed: {error}")

story = st.session_state.get("story")
if story is None:
    st.info(
        "Start with **Unsafe memory**, then replay the same question through "
        "**Guarded memory** and **Recovery**."
    )
    st.stop()

active = PATHS[story["path"]]
st.divider()
st.caption(f"STEP {active['step']}")
st.header(active["title"])

chat, evidence = st.columns([3, 2], gap="large")
with chat:
    st.markdown("### Conversation")
    if story["path"] == "unsafe":
        render_unsafe(story)
    elif story["path"] == "guarded":
        render_guarded(story)
    else:
        render_recovery(story)

with evidence:
    with st.container(border=True):
        st.markdown("### Why PatchPilot answered this way")
        render_evidence_panel(story)
