"""Retrieval-Augmented Generation (RAG) utilities and tool.

This module builds an in-memory RAG pipeline that:
- Loads PDF documents from `RAG_DATA_DIR` (default: "data").
- Splits documents into chunks using a token-aware splitter.
- Embeds chunks with OpenAI and stores vectors in an in-memory Qdrant store.
- Exposes a LangChain Tool `retrieve_information` that retrieves relevant
- context and generates a response constrained to that context.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated, List

import tiktoken
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langgraph.graph import START, StateGraph
from typing_extensions import TypedDict


def _tiktoken_len(text: str) -> int:
    """Return token length using tiktoken; used for chunk length measurement."""
    tokens = tiktoken.encoding_for_model("gpt-4o").encode(text)
    return len(tokens)


class _RAGState(TypedDict):
    """State schema for the simple two-step RAG graph: retrieve then generate."""
    question: str
    context: List[Document]
    response: str


def _build_rag_graph(data_dir: str):
    """Construct and compile a minimal RAG graph.

    Steps:
    1) Load PDFs from `data_dir` recursively (best-effort).
    2) Split documents into token-aware chunks.
    3) Create embeddings and an in-memory Qdrant vector store retriever.
    4) Define a chat prompt and generation model.
    5) Wire a two-node graph: retrieve -> generate.
    """
    # Load PDFs from data directory (recursive)
    try:
        directory_loader = DirectoryLoader(
            data_dir, glob="**/*.pdf", loader_cls=PyMuPDFLoader
        )
        documents = directory_loader.load()
    except Exception:
        documents = []

    # Split documents
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:
        # Fallback to legacy import path if available
        from langchain.text_splitter import (  # type: ignore
            RecursiveCharacterTextSplitter,
        )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=750, chunk_overlap=0, length_function=_tiktoken_len
    )
    chunks = text_splitter.split_documents(documents) if documents else []

    # Embeddings and vector store (in-memory Qdrant)
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    qdrant_vectorstore = Qdrant.from_documents(
        documents=chunks, embedding=embedding_model, location=":memory:"
    )
    retriever = qdrant_vectorstore.as_retriever()

    human_template = (
        "You are a rice pathology/IPM assistant. Write a concise, actionable answer using the provided contexts."
        "Answer using ONLY the text in CONTEXT. Do not use outside knowledge.\n"
        "If the answer is not in CONTEXT, respond exactly: I don't know\n"
        "Prioritize PDF evidence over web and arXiv. Cite PDFs as [filename.pdf, p. N]; "
        "cite web as [URL]; cite arXiv as (arXiv:ID). If a claim is only from web/arXiv, make that clear. "
        "If PDFs do not cover the query, say so briefly before using web/arXiv. Do not invent citations."
        "# CONTEXT:\n{context}\n\n# QUERY:\n{query}\n"
    )

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "Ground answers strictly in the provided CONTEXT and follow the citation rules."),
        ("human", human_template),
    ])
    generator_llm = ChatOpenAI(model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-nano"), temperature=0)

    def retrieve(state: _RAGState) -> _RAGState:
        retrieved_docs = retriever.invoke(state["question"]) if retriever else []
        return {"context": retrieved_docs}  # type: ignore

    def generate(state: _RAGState) -> _RAGState:
        generator_chain = chat_prompt | generator_llm | StrOutputParser()

        # Format CONTEXT with filename and page to steer correct inline citations
        docs = state.get("context", [])
        formatted_context_parts = []
        for d in docs:
            meta = getattr(d, "metadata", {}) or {}
            src = os.path.basename(meta.get("source", "")) or "unknown.pdf"
            page = meta.get("page")
            header = f"[{src}, p. {page}]" if page is not None else f"[{src}]"
            formatted_context_parts.append(f"{header}\n{d.page_content}")
        formatted_context = "\n\n".join(formatted_context_parts) if formatted_context_parts else ""

        response_text = generator_chain.invoke(
            {"query": state["question"], "context": formatted_context}
        )
        return {"response": response_text}  # type: ignore

    graph_builder = StateGraph(_RAGState)
    graph_builder = graph_builder.add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    return graph_builder.compile()


@lru_cache(maxsize=1)
def _get_rag_graph():
    """Return a cached compiled RAG graph built from RAG_DATA_DIR."""
    data_dir = os.environ.get("RAG_DATA_DIR", "data")
    return _build_rag_graph(data_dir)


@tool
def retrieve_information(
    query: Annotated[str, "query to ask the retrieve information tool"]
):
    """Retrieve rice disease and IPM information from the local PDF library using RAG"""
    graph = _get_rag_graph()
    result = graph.invoke({"question": query})
    # Prefer returning the response string if available
    if isinstance(result, dict) and "response" in result:
        return result["response"]
    return result

def test_rag_system():
    """Test function to debug RAG issues"""
    import os
    data_dir = os.environ.get("RAG_DATA_DIR", "data")
    print(f"RAG_DATA_DIR: {data_dir}")
    print(f"Directory exists: {os.path.exists(data_dir)}")
    
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
        print(f"PDF files found: {files}")
    
    try:
        # Test the RAG tool
        result = retrieve_information("What is rice blast?")
        print(f"RAG result: {result}")
    except Exception as e:
        print(f"RAG error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_system()