"""Reads uiconfig.ini for the Streamlit sidebar (same pattern as the earlier LangGraph chatbot)."""

import os
from configparser import ConfigParser


class Config:
    def __init__(self, config_file: str | None = None):
        self.config = ConfigParser()
        self.config.read(config_file or os.path.join(os.path.dirname(__file__), "uiconfig.ini"))

    def _list(self, key: str) -> list[str]:
        return [o.strip() for o in self.config["DEFAULT"].get(key, "").split(",") if o.strip()]

    @property
    def PAGE_TITLE(self) -> str:
        return self.config["DEFAULT"].get("PAGE_TITLE")

    @property
    def LLM_OPTIONS(self) -> list[str]:
        return self._list("LLM_OPTIONS")

    @property
    def ANSWER_STYLE_OPTIONS(self) -> list[str]:
        return self._list("ANSWER_STYLE_OPTIONS")

    @property
    def DEFAULT_LANGGRAPH_SERVER_URL(self) -> str:
        return self.config["DEFAULT"].get("DEFAULT_LANGGRAPH_SERVER_URL")

    def model_options(self, llm: str) -> list[str]:
        return self._list(f"{llm.upper()}_MODEL_OPTIONS")

    def model_info(self, model: str) -> str:
        return self.config["MODEL_INFO"].get(model.lower(), "")
