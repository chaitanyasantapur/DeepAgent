"""Streamlit chat UI for the deep agent.

Run:  uv run streamlit run app.py

Sidebar layout follows the earlier LangGraph chatbot (Configuration -> LLM,
model, API key, temperature, then use-case options), driven by uiconfig.ini.
Every agent feature is a checkbox; changing anything rebuilds the agent while
keeping conversation threads (shared MemorySaver checkpointer).
"""

import os
import uuid
from datetime import datetime

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from tavily import TavilyClient

import common
import deepagent as d
from subagents import SYNC_SUBAGENTS, async_subagents
from uiconfig import Config

config = Config()
st.set_page_config(layout="wide", page_title=config.PAGE_TITLE, page_icon="🤖")

PLACEHOLDER_PREFIX = "your_"


def env_key(name: str) -> str:
    """Return the key from .env unless it is empty or still a placeholder."""
    value = os.getenv(name, "")
    return "" if not value or value.startswith(PLACEHOLDER_PREFIX) else value


# ---------------------------------------------------------------------------
# Header (same two-column header as the earlier chatbot)
# ---------------------------------------------------------------------------
col1, col2 = st.columns([0.5, 9.5])
with col1:
    st.markdown("# 🤖")
with col2:
    st.title(config.PAGE_TITLE)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "threads" not in st.session_state:
    st.session_state.threads = []
if "thread_id" not in st.session_state:
    tid = f"chat-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4]}"
    st.session_state.threads.append(tid)
    st.session_state.thread_id = tid

# ---------------------------------------------------------------------------
# Sidebar: Configuration
# ---------------------------------------------------------------------------
controls: dict = {}
with st.sidebar:
    st.subheader("Configuration")

    controls["llm"] = st.selectbox("Select LLM", config.LLM_OPTIONS)
    provider = controls["llm"].lower()

    st.markdown(f"### {controls['llm']} Models")
    controls["model"] = st.selectbox("Select Model", config.model_options(controls["llm"]), key=f"model_{provider}")
    info = config.model_info(controls["model"])
    if info:
        st.caption(f"📌 {info}")

    key_name = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
    typed_key = st.text_input("API Key", type="password", key=f"key_{provider}", help=f"Leave blank to use {key_name} from .env")
    controls["api_key"] = typed_key or env_key(key_name)
    if not controls["api_key"]:
        url = "https://console.groq.com/keys" if provider == "groq" else "https://platform.openai.com/api-keys"
        st.warning(f"⚠️ Enter your {controls['llm']} API key to proceed.\n\n🔗 Get API key: {url}")
    elif not typed_key:
        st.caption("🔑 Using key from .env")
    if provider == "groq":
        st.caption("Groq free tier allows 8k tokens/min per request; the full deep agent needs more. Turn features off below or use a paid tier.")

    controls["temperature"] = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

    st.divider()
    st.subheader("Agent options")
    controls["answer_style"] = st.radio("Answer style", config.ANSWER_STYLE_OPTIONS, horizontal=True)

    st.markdown("**Features**")
    controls["skills"] = st.checkbox("Skills library (python, aws, web-research, report-writer)", value=True)
    controls["memory"] = st.checkbox("AGENTS.md memory", value=True)
    controls["web_search"] = st.checkbox("Web search (Tavily)", value=True)
    if controls["web_search"]:
        typed_tavily = st.text_input("Tavily API Key", type="password", key="tavily_key", help="Leave blank to use TAVILY_API_KEY from .env")
        controls["tavily_key"] = typed_tavily or env_key("TAVILY_API_KEY")
        if not controls["tavily_key"]:
            st.info("ℹ️ Enter your Tavily API key to enable web search.\n\n🔗 Get API key: https://tavily.com")
    controls["code_interpreter"] = st.checkbox("Code interpreter (QuickJS `eval` tool)", value=True)
    controls["sync_subagents"] = st.checkbox("Sync subagents (researcher, coder, critic)", value=True)
    controls["async_subagents"] = st.checkbox("Async subagents (LangGraph server)", value=bool(os.getenv("LANGGRAPH_SERVER_URL")))
    if controls["async_subagents"]:
        controls["server_url"] = st.text_input("LangGraph server URL", value=os.getenv("LANGGRAPH_SERVER_URL", config.DEFAULT_LANGGRAPH_SERVER_URL))
        st.caption("Start it with `uv run langgraph dev --no-browser --port 2024`")
    controls["report_required"] = st.checkbox("Write a report after every answer", value=True)
    controls["show_tools"] = st.checkbox("Show tool activity", value=True)

    st.divider()
    st.subheader("Conversation")
    choice = st.selectbox("Thread", st.session_state.threads, index=st.session_state.threads.index(st.session_state.thread_id))
    if choice != st.session_state.thread_id:
        st.session_state.thread_id = choice
        st.rerun()
    if st.button("➕ New thread", use_container_width=True):
        tid = f"chat-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:4]}"
        st.session_state.threads.append(tid)
        st.session_state.thread_id = tid
        st.rerun()

# ---------------------------------------------------------------------------
# Build (or reuse) the agent for the current configuration
# ---------------------------------------------------------------------------
if controls.get("web_search") and controls.get("tavily_key"):
    common.tavily_client = TavilyClient(api_key=controls["tavily_key"])

signature = (
    provider, controls["model"], controls["api_key"], controls["temperature"], controls["answer_style"],
    controls["skills"], controls["memory"], controls["web_search"], controls["code_interpreter"],
    controls["sync_subagents"], controls.get("server_url") if controls["async_subagents"] else None,
    controls["report_required"],
)
if st.session_state.get("agent_signature") != signature:
    model = d.build_model(provider, controls["model"], controls["temperature"], controls["api_key"] or None)
    st.session_state.agent = d.build_agent(
        model,
        skills=controls["skills"],
        memory=controls["memory"],
        code_interpreter=controls["code_interpreter"],
        web_search=controls["web_search"],
        sync_subagents=controls["sync_subagents"],
        async_server_url=signature[10],
        report_required=controls["report_required"],
        answer_style=controls["answer_style"],
    )
    st.session_state.agent_signature = signature
agent = st.session_state.agent


def thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def thread_state(thread_id: str) -> dict:
    return agent.get_state(thread_config(thread_id)).values or {}


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b if isinstance(b, str) else b.get("text", "") for b in content if isinstance(b, (str, dict)) and (isinstance(b, str) or b.get("type") == "text"))
    return str(content)


def summarize_tool_call(call: dict) -> str:
    name, args = call.get("name", "?"), call.get("args", {}) or {}
    if name in {"task", "start_async_task"}:
        return f"{name} -> {args.get('subagent_type')}: {str(args.get('description', ''))[:120]}"
    if name in {"check_async_task", "update_async_task", "cancel_async_task"}:
        return f"{name} ({str(args.get('task_id', ''))[:8]}…)"
    if name == "eval":
        return f"eval: {str(args.get('code', ''))[:120]}"
    if name == "internet_search":
        return f"internet_search: {args.get('query', '')}"
    if name in {"read_file", "write_file", "edit_file"}:
        return f"{name}: {args.get('file_path', '')}"
    return f"{name}: {str(args)[:120]}"


# ---------------------------------------------------------------------------
# Sidebar: status panels (below configuration)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.divider()
    with st.expander("Active capabilities", expanded=False):
        st.markdown(f"**Model:** {controls['llm']} · `{controls['model']}` · T={controls['temperature']}")
        if controls["skills"]:
            for skill in sorted(p for p in d.SKILLS_DIR.iterdir() if (p / "SKILL.md").exists()):
                st.markdown(f"- 🧩 **{skill.name}** — {', '.join(sorted(f.name for f in skill.iterdir() if f.is_file()))}")
            if st.button("🔄 Reload skills in this thread", use_container_width=True):
                agent.update_state(thread_config(st.session_state.thread_id), {"skills_metadata": None})
                st.toast("Skills will be re-read on the next turn")
        if controls["sync_subagents"]:
            st.markdown("**Sync subagents:** " + ", ".join(f"`{s['name']}` ({s.get('mode', 'isolated')})" for s in SYNC_SUBAGENTS))
        specs = async_subagents(controls.get("server_url")) if controls["async_subagents"] else []
        if specs:
            st.markdown("**Async subagents:** " + ", ".join(f"`{s['name']}`" for s in specs))
        tasks = thread_state(st.session_state.thread_id).get("async_tasks") or []
        for t in (tasks if isinstance(tasks, list) else list(tasks.values())):
            st.markdown(f"- ⏳ `{t['task_id'][:8]}…` {t['agent_name']} · **{t['status']}**")
        tools = (["internet_search"] if controls["web_search"] else []) + (["eval"] if controls["code_interpreter"] else []) + ["ls", "read_file", "write_file", "edit_file", "glob", "grep"]
        st.markdown("**Tools:** " + ", ".join(f"`{t}`" for t in tools))

    with st.expander("Reports", expanded=False):
        reports = sorted(d.REPORTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if reports:
            picked = st.selectbox("Report file", reports, format_func=lambda p: p.name)
            content = picked.read_text(encoding="utf-8")
            st.download_button("⬇️ Download", content, file_name=picked.name, mime="text/markdown", use_container_width=True)
            st.markdown(content)
        else:
            st.caption("No reports yet.")

# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


def render_history(messages: list) -> None:
    pending: list[str] = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(text_of(msg.content))
        elif isinstance(msg, AIMessage):
            if msg.tool_calls:
                pending.extend(summarize_tool_call(c) for c in msg.tool_calls)
            body = text_of(msg.content).strip()
            if body:
                with st.chat_message("assistant"):
                    if pending and controls["show_tools"]:
                        with st.expander(f"Tool activity ({len(pending)})"):
                            for line in pending:
                                st.code(line, language=None)
                    pending = []
                    st.markdown(body)
        elif isinstance(msg, ToolMessage):
            continue


def run_turn(thread_id: str, user_text: str) -> None:
    cfg = thread_config(thread_id)
    before = {p for p in thread_state(thread_id).get("files", {}) if p.startswith(d.REPORTS_PATH)}
    payload = {
        "messages": [{"role": "user", "content": user_text}],
        "files": d.load_context_files(skills=controls["skills"], memory=controls["memory"]),
    }
    with st.chat_message("assistant"):
        status = st.status("Thinking...", expanded=controls["show_tools"])
        answer_box = st.empty()
        final_text, n_tools = "", 0
        try:
            for update in agent.stream(payload, config=cfg, stream_mode="updates"):
                for data in update.values():
                    if not isinstance(data, dict):
                        continue
                    for msg in data.get("messages", []) or []:
                        if isinstance(msg, AIMessage):
                            for call in msg.tool_calls or []:
                                n_tools += 1
                                if controls["show_tools"]:
                                    status.write(f"🔧 {summarize_tool_call(call)}")
                            if text_of(msg.content).strip():
                                final_text = text_of(msg.content)
                        elif isinstance(msg, ToolMessage) and controls["show_tools"]:
                            status.write(f"↩️ {msg.name}: {text_of(msg.content).strip().replace(chr(10), ' ')[:200]}")
            status.update(label=f"Done ({n_tools} tool calls)", state="complete", expanded=False)
        except Exception as exc:
            status.update(label="Error", state="error", expanded=True)
            st.error(f"{type(exc).__name__}: {exc}")
            return
        if not final_text:
            final_text = text_of(thread_state(thread_id)["messages"][-1].content)
        answer_box.markdown(final_text)

    saved = d.save_reports(thread_state(thread_id).get("files", {}), before)
    if saved:
        st.toast(f"Report saved: {', '.join(p.name for p in saved)}", icon="📄")
    elif controls["report_required"]:
        st.toast("No report was written this turn", icon="⚠️")


history = thread_state(st.session_state.thread_id).get("messages", [])
if not history:
    st.info("Start a conversation. Try: *What is the latest stable Python version, and write me a one-line reverse-string function.*")
render_history(history)

if not controls["api_key"]:
    st.chat_input("Enter an API key in the sidebar to start", disabled=True)
elif prompt := st.chat_input("Ask the deep agent..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    run_turn(st.session_state.thread_id, prompt)
    st.rerun()
