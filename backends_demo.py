"""Deep agent backends demo: StateBackend, FilesystemBackend, StoreBackend.

Each backend controls where the agent's built-in file tools (ls, read_file,
write_file, edit_file, glob, grep) store their data.

  StateBackend       -> files live in the LangGraph state (ephemeral, per thread)
  FilesystemBackend  -> files live on the real disk under a root directory
  StoreBackend       -> files live in a LangGraph BaseStore (persists across threads)
"""

from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend

load_dotenv()

model = ChatGroq(model="openai/gpt-oss-120b")


def ask(agent, text, thread_id="1"):
    result = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    print(result["messages"][-1].content)
    return result


# --------------------------------------------------------------------------
# 1. StateBackend (default) - files are kept in agent state, checkpointed per
#    thread. They disappear when the thread ends.
# --------------------------------------------------------------------------
print("=" * 70, "\n1. StateBackend\n", "=" * 70)

state_agent = create_deep_agent(
    model=model,
    backend=StateBackend(),
    checkpointer=MemorySaver(),          # needed so state survives between turns
    system_prompt="You are a note taker. Use write_file / read_file to manage notes.",
)

ask(state_agent, "Write a file /notes.md containing 'Deep agents rock'.", thread_id="state-1")
ask(state_agent, "Read /notes.md back to me.", thread_id="state-1")
result = ask(state_agent, "List the files you have.", thread_id="state-1")
print("\nFiles held in state:", list(result.get("files", {}).keys()))


# --------------------------------------------------------------------------
# 2. FilesystemBackend - files are real files on disk under root_dir.
#    virtual_mode=True sandboxes the agent to root_dir; /notes.md maps to
#    <root_dir>/notes.md.
# --------------------------------------------------------------------------
print("\n", "=" * 70, "\n2. FilesystemBackend\n", "=" * 70)

workspace = Path("workspace")
workspace.mkdir(exist_ok=True)

fs_agent = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
    system_prompt="You are a note taker. Use write_file / read_file to manage notes.",
)

ask(fs_agent, "Write a file /hello.txt containing 'Hello from the filesystem backend'.")
print("\nOn disk:", [p.name for p in workspace.iterdir()])
print("Content:", (workspace / "hello.txt").read_text())


# --------------------------------------------------------------------------
# 3. StoreBackend - files live in a LangGraph store, scoped by a namespace,
#    and persist across threads / conversations. Swap InMemoryStore for a
#    Postgres/Redis store in production.
# --------------------------------------------------------------------------
print("\n", "=" * 70, "\n3. StoreBackend\n", "=" * 70)

store = InMemoryStore()

store_agent = create_deep_agent(
    model=model,
    backend=StoreBackend(store=store, namespace=lambda runtime: ("memories",)),
    store=store,
    checkpointer=MemorySaver(),
    system_prompt="You are a note taker. Use write_file / read_file to manage notes.",
)

ask(store_agent, "Write a file /memory.md containing 'User likes cricket'.", thread_id="store-1")
# A brand new thread can still read it because the store is shared
ask(store_agent, "Read /memory.md and tell me what it says.", thread_id="store-2")
print("\nKeys in store namespace ('memories',):", [item.key for item in store.search(("memories",))])


# --------------------------------------------------------------------------
# 4. Bonus: CompositeBackend - route paths to different backends.
#    /memories/... -> StoreBackend (long-term), everything else -> StateBackend
# --------------------------------------------------------------------------
print("\n", "=" * 70, "\n4. CompositeBackend (state + store)\n", "=" * 70)

composite_agent = create_deep_agent(
    model=model,
    backend=CompositeBackend(
        default=StateBackend(),
        routes={"/memories/": StoreBackend(store=store, namespace=lambda rt: ("memories",))},
    ),
    store=store,
    checkpointer=MemorySaver(),
    system_prompt="You are a note taker. Scratch files go anywhere; long-term facts go under /memories/.",
)

ask(composite_agent, "Save '/scratch.txt' with 'temp' and '/memories/prefs.md' with 'prefers uv'.", thread_id="c-1")
print("\nStore now has:", [item.key for item in store.search(("memories",))])
