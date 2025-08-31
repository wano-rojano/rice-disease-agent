"""Toolbelt assembly for agents.

Collects third-party tools and local tools (like RAG) into a single list that
graphs can bind to their language models.
"""
from __future__ import annotations

from typing import List

from langchain_tavily import TavilySearch
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from app.rag import retrieve_information


def get_tool_belt() -> List:
    """Return the list of tools available to agents (RAG, Tavily, Pubmed, Arxiv)."""
    tavily_tool = TavilySearch(max_results=5)
    return [
        retrieve_information,
        tavily_tool,
        PubmedQueryRun(),
        ArxivQueryRun()
    ]
