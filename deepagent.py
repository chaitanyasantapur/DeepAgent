from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tavily import TavilyClient

from deepagents import create_deep_agent

load_dotenv()

# Reads TAVILY_API_KEY from the environment (.env)
tavily_client = TavilyClient()


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search and return the results."""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


system_prompt = """You are an expert researcher. Your job is to conduct thorough research
and then write a polished, well-structured report.

You have access to an internet_search tool. Use it to look up current information
before answering. Cite the sources you used at the end of your report."""

# Groq model (key already in .env). To use OpenAI instead:
#   from langchain_openai import ChatOpenAI
#   model = ChatOpenAI(model="gpt-4.1")
model = ChatGroq(model="openai/gpt-oss-120b")

agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt=system_prompt,
)

if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "what is deep agents"}]}
    )
    print(result["messages"][-1].content)
