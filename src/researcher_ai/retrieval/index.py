from __future__ import annotations

import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_index(
    chunks_path: str,
    index_path: str,
    meta_path: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    source = Path(chunks_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Chunks file does not exist: {source}")

    rows = _load_jsonl(source)
    if not rows:
        raise ValueError("No chunk rows found. Run chunk command first.")

    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Retrieval requires numpy. Install with: pip install numpy") from exc

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Retrieval requires sentence-transformers. Install with: "
            "pip install sentence-transformers"
        ) from exc

    model = SentenceTransformer(model_name)
    texts = [row["text"] for row in rows]
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    vectors = vectors.astype(np.float32)

    idx_dest = Path(index_path).expanduser().resolve()
    idx_dest.parent.mkdir(parents=True, exist_ok=True)
    np.save(idx_dest, vectors)

    meta_dest = Path(meta_path).expanduser().resolve()
    meta_dest.parent.mkdir(parents=True, exist_ok=True)
    with meta_dest.open("w", encoding="utf-8") as f:
        for row in rows:
            keep = {
                "chunk_id": row["chunk_id"],
                "citation": row["citation"],
                "source_path": row["source_path"],
                "page": row["page"],
                "text": row["text"],
            }
            f.write(json.dumps(keep, ensure_ascii=True) + "\n")

    return {
        "chunks_path": str(source),
        "index_path": str(idx_dest),
        "meta_path": str(meta_dest),
        "vectors": int(vectors.shape[0]),
        "dim": int(vectors.shape[1]),
        "model": model_name,
    }


def search_index(
    query: str,
    index_path: str,
    meta_path: str,
    top_k: int = 5,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    diversify_citations: bool = True,
) -> list[dict]:
    if not query.strip():
        raise ValueError("Query must not be empty")

    idx_path = Path(index_path).expanduser().resolve()
    meta = Path(meta_path).expanduser().resolve()
    if not idx_path.exists() or not meta.exists():
        raise FileNotFoundError("Index or metadata not found. Run index command first.")

    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Retrieval requires numpy. Install with: pip install numpy") from exc

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Retrieval requires sentence-transformers. Install with: "
            "pip install sentence-transformers"
        ) from exc

    vectors = np.load(idx_path).astype(np.float32)
    rows = _load_jsonl(meta)
    if len(rows) != len(vectors):
        raise ValueError("Index and metadata size mismatch.")

    model = SentenceTransformer(model_name)
    qvec = model.encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0].astype(np.float32)

    scores = vectors @ qvec
    results: list[dict] = []
    sorted_indices = np.argsort(-scores)
    used_citations: set[str] = set()
    for idx in sorted_indices:
        row = rows[int(idx)]
        if diversify_citations and row["citation"] in used_citations:
            continue
        used_citations.add(row["citation"])
        results.append(
            {
                "rank": len(results) + 1,
                "score": float(scores[int(idx)]),
                "citation": row["citation"],
                "chunk_id": row["chunk_id"],
                "source_path": row["source_path"],
                "page": row["page"],
                "text": row["text"],
            }
        )
        if len(results) >= max(top_k, 1):
            break
    return results
