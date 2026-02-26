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

Run chunking + coverage check:
```bash
researcher-ai chunk \
  --input data/processed/ingested.jsonl \
  --output data/processed/chunks.jsonl \
  --coverage-output data/processed/coverage.json
```

Why this step matters:
- Retrieval models work better on medium-sized chunks than full pages.
- Coverage report verifies whether any ingested citation failed to produce a usable chunk.
- `uncovered_citations` in `coverage.json` gives exact items to inspect/fix.

Build retrieval index:
```bash
researcher-ai index \
  --input data/processed/chunks.jsonl \
  --index-output data/processed/retrieval_vectors.npy \
  --meta-output data/processed/retrieval_meta.jsonl
```

Search top relevant chunks:
```bash
researcher-ai search \
  --query "What is edge ai and why efficiency matters?" \
  --index-input data/processed/retrieval_vectors.npy \
  --meta-input data/processed/retrieval_meta.jsonl \
  --top-k 5
```

Why retrieval comes before generation:
- Notes and quizzes should be evidence-based, not hallucinated.
- Retrieval gives traceable citations for each generated claim.

Generate grounded notes:
```bash
researcher-ai notes \
  --query "Explain edge ai from basics and also technical depth" \
  --index-input data/processed/retrieval_vectors.npy \
  --meta-input data/processed/retrieval_meta.jsonl \
  --output data/processed/notes.json
```

`notes.json` includes:
- `key_points`: condensed important statements
- `ground_up`: beginner-friendly explanation snippets
- `deep_dive`: technical detail snippets
- `structured_notes`: fundamentals, core methods, exam focus, mistakes, checklist
- `citations`: exact evidence pointers

Generate quiz set:
```bash
researcher-ai quiz \
  --query "Test me on edge ai fundamentals and tradeoffs" \
  --index-input data/processed/retrieval_vectors.npy \
  --meta-input data/processed/retrieval_meta.jsonl \
  --output data/processed/quiz.json \
  --count 6
```

`quiz.json` includes:
- `mcq`, `short_answer`, and `explain_why` questions
- answer key and source citations per question

Generate presentation-ready outputs:
```bash
researcher-ai present \
  --notes-input data/processed/notes.json \
  --quiz-input data/processed/quiz.json \
  --notes-output data/processed/presentation_notes.json \
  --quiz-output data/processed/presentation_quiz.json
```

`presentation_notes.json` and `presentation_quiz.json` are cleaner, shorter versions for demos.

Run local GUI (Streamlit):
```bash
streamlit run app_streamlit.py
```

GUI flow:
1. Set paths (defaults already match project structure).
2. Click `Run Ingest`, `Run Chunk`, `Run Index`.
3. Enter study query and click `Generate Notes` and `Generate Quiz`.
4. Preview `coverage.json`, `notes.json`, and `quiz.json` in-app.

## Next Steps
1. Implement ingest pipeline (PDF/image/text)
2. Implement chunking + coverage report
3. Add retrieval indexing and search
4. Add note generation and quiz evaluation
5. Add Streamlit GUI for upload, run, and review
6. Add result quality metrics and final demo script
