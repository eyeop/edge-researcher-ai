from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from researcher_ai.chunking.pipeline import chunk_ingested_records
from researcher_ai.ingest.pipeline import ingest_materials
from researcher_ai.notes.generator import generate_notes
from researcher_ai.quiz.generator import generate_quiz
from researcher_ai.retrieval.index import build_index


st.set_page_config(page_title="Edge Researcher AI", page_icon=":books:", layout="wide")
st.title("Edge Researcher AI")
st.caption("Local-first study assistant: ingest, chunk, index, notes, and quiz.")

st.subheader("Paths")
raw_path = st.text_input("Raw input folder", value="data/raw")
ingested_path = st.text_input("Ingest output", value="data/processed/ingested.jsonl")
chunks_path = st.text_input("Chunk output", value="data/processed/chunks.jsonl")
coverage_path = st.text_input("Coverage output", value="data/processed/coverage.json")
vectors_path = st.text_input("Index output (.npy)", value="data/processed/retrieval_vectors.npy")
meta_path = st.text_input("Meta output (.jsonl)", value="data/processed/retrieval_meta.jsonl")
notes_path = st.text_input("Notes output", value="data/processed/notes.json")
quiz_path = st.text_input("Quiz output", value="data/processed/quiz.json")

st.subheader("Step 1-3: Build Local Knowledge Base")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Run Ingest", use_container_width=True):
        try:
            summary = ingest_materials(raw_path, ingested_path, min_chars=20)
            st.success(f"Ingest done: {summary}")
        except Exception as exc:  # pragma: no cover
            st.error(str(exc))

with col2:
    if st.button("Run Chunk", use_container_width=True):
        try:
            summary = chunk_ingested_records(
                ingest_path=ingested_path,
                chunk_output_path=chunks_path,
                coverage_output_path=coverage_path,
                max_chars=700,
                overlap_chars=120,
                min_chunk_chars=40,
            )
            st.success(f"Chunk done: {summary}")
        except Exception as exc:  # pragma: no cover
            st.error(str(exc))

with col3:
    if st.button("Run Index", use_container_width=True):
        try:
            summary = build_index(
                chunks_path=chunks_path,
                index_path=vectors_path,
                meta_path=meta_path,
            )
            st.success(f"Index done: {summary}")
        except Exception as exc:  # pragma: no cover
            st.error(str(exc))

st.subheader("Step 4-5: Generate Notes and Quiz")
query = st.text_input(
    "Study question/topic",
    value="Explain edge AI fundamentals and technical tradeoffs.",
)
top_k = st.slider("Evidence chunks (top_k)", min_value=3, max_value=12, value=6)
quiz_count = st.slider("Quiz question count", min_value=3, max_value=12, value=6)
col4, col5 = st.columns(2)

with col4:
    if st.button("Generate Notes", use_container_width=True):
        try:
            summary = generate_notes(
                query=query,
                index_path=vectors_path,
                meta_path=meta_path,
                output_path=notes_path,
                top_k=top_k,
            )
            st.success(f"Notes done: {summary}")
        except Exception as exc:  # pragma: no cover
            st.error(str(exc))

with col5:
    if st.button("Generate Quiz", use_container_width=True):
        try:
            summary = generate_quiz(
                query=query,
                index_path=vectors_path,
                meta_path=meta_path,
                output_path=quiz_path,
                question_count=quiz_count,
            )
            st.success(f"Quiz done: {summary}")
        except Exception as exc:  # pragma: no cover
            st.error(str(exc))

st.subheader("Preview Outputs")
preview_file = st.selectbox(
    "Choose output file",
    options=[coverage_path, notes_path, quiz_path],
)

if st.button("Load Preview"):
    target = Path(preview_file).expanduser().resolve()
    if not target.exists():
        st.warning(f"File not found: {target}")
    else:
        content = target.read_text(encoding="utf-8")
        try:
            st.json(json.loads(content))
        except json.JSONDecodeError:
            st.code(content, language="json")
