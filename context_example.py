"""Context example: AGENTS.md loaded on invocation + a detailed input prompt.

Two ways context reaches the agent here:

1. `memory=["/AGENTS.md"]` - the file is read from the backend and injected
   into the system prompt as an <agent_memory> block every time the agent is
   invoked. The `system_prompt` below tells the agent to treat that block as
   its operating instructions.
2. The user message itself - a detailed prompt with the task, background,
   and constraints.
"""

from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from deepagent import internet_search  # reuse the Tavily tool

load_dotenv()

# Root the backend at this folder so "/AGENTS.md" maps to ./AGENTS.md
backend = FilesystemBackend(root_dir=Path(__file__).parent, virtual_mode=True)

system_prompt = """You are a research assistant for this project.

Your system prompt ends with an <agent_memory> block loaded from AGENTS.md.
It describes the project, the user, how you should behave, and how deep
agents are built. Treat it as your operating instructions, and use its
architecture notes when asked how you work."""

agent = create_deep_agent(
    model=ChatGroq(model="openai/gpt-oss-120b"),
    tools=[internet_search],
    system_prompt=system_prompt,
    backend=backend,
    memory=["/AGENTS.md"],
)

# Detailed input prompt: task + background + constraints, all in the message.
prompt = """
Task: Give me a short briefing on what LangChain "deep agents" are.

Background: I am evaluating them for internal tooling at work. I already know
LangGraph and plain tool-calling agents, so skip the basics of those.

What I need:
- What a deep agent adds on top of a normal tool-calling agent
- The built-in tools it ships with
- One sentence on when I should NOT use it

Constraints: follow the answer style described in your memory.
"""

result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
print(result["messages"][-1].content)
