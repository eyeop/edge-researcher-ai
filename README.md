# Edge Researcher AI (Local + Efficient)

A local-first edge AI study assistant that ingests PDFs/images/text, preserves key points with citations, expands topics from fundamentals to deep understanding, and generates tests.

## What "Edge + Efficient" Means
- `Local AI`: your files stay on your machine (privacy + offline use).
- `Edge AI`: inference runs on personal hardware (your 3060 Ti or M4 Pro), not cloud servers.
- `Efficient AI`: small/quantized models, lower memory, faster latency, and lower power.

For this project, we keep a strict pipeline:
1. `Ingest` data with traceable citations
2. `Chunk` text for retrieval
3. `Retrieve` relevant evidence
4. `Generate` notes (ground-up + deep-dive)
5. `Create` quizzes with answer keys and citations

## Week-1 MVP Scope
- Ingest PDF/image/text materials
- Extract text (OCR when needed)
- Chunk and index content locally
- Generate structured notes with source citations
- Expand explanations in two modes: ground-up and deep-dive
- Generate quizzes with answer keys and citations

## Why Edge AI
- Privacy-preserving (local inference)
- Fast iteration on personal hardware
- Efficient model/runtime with quantization

## Hardware Plan
- Development: Desktop (RTX 3060 Ti)
- Final demo: MacBook Pro (M4 Pro)

## Project Structure
- `src/researcher_ai/ingest`: loaders + OCR pipeline
- `src/researcher_ai/chunking`: text segmentation and coverage checks
- `src/researcher_ai/retrieval`: embeddings + FAISS index
- `src/researcher_ai/notes`: note organization + expansion
- `src/researcher_ai/quiz`: question generation
- `tests/`: unit and pipeline tests

## Quick Start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m researcher_ai --help
```

Install file extraction dependencies:
```bash
pip install pymupdf pillow pytesseract
```

Run ingestion:
```bash
researcher-ai ingest --input data/raw --output data/processed/ingested.jsonl
```

Output format is JSONL with citation fields such as `lecture1.pdf:p3:i1`.
This is important because every later summary and quiz can point back to exact source evidence.

## Next Steps
1. Implement ingest pipeline (PDF/image/text)
2. Add chunking + citation-preserving schema
3. Add retrieval and local LLM generation
4. Add quiz generation and evaluation
