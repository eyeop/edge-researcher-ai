import argparse
import json

from researcher_ai.chunking.pipeline import chunk_ingested_records
from researcher_ai.ingest.pipeline import ingest_materials
from researcher_ai.notes.generator import generate_notes
from researcher_ai.quiz.generator import generate_quiz
from researcher_ai.retrieval.index import build_index, search_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="researcher-ai",
        description="Local-first Edge Researcher AI",
    )
    subparsers = parser.add_subparsers(dest="command")

    ingest = subparsers.add_parser("ingest", help="Ingest study materials")
    ingest.add_argument("--input", required=True, help="Path to input file or folder")
    ingest.add_argument(
        "--output",
        default="data/processed/ingested.jsonl",
        help="Path for JSONL ingest output",
    )
    ingest.add_argument(
        "--min-chars",
        type=int,
        default=20,
        help="Skip extracted text shorter than this threshold",
    )

    chunk = subparsers.add_parser(
        "chunk", help="Chunk ingested records and produce coverage report"
    )
    chunk.add_argument(
        "--input",
        default="data/processed/ingested.jsonl",
        help="Path to ingested JSONL",
    )
    chunk.add_argument(
        "--output",
        default="data/processed/chunks.jsonl",
        help="Path for chunk JSONL output",
    )
    chunk.add_argument(
        "--coverage-output",
        default="data/processed/coverage.json",
        help="Path for coverage report JSON",
    )
    chunk.add_argument(
        "--max-chars",
        type=int,
        default=700,
        help="Maximum chunk size in characters",
    )
    chunk.add_argument(
        "--overlap-chars",
        type=int,
        default=120,
        help="Overlap characters between consecutive chunks",
    )
    chunk.add_argument(
        "--min-chars",
        type=int,
        default=40,
        help="Minimum characters for a valid chunk",
    )

    index = subparsers.add_parser("index", help="Build retrieval index from chunks")
    index.add_argument(
        "--input",
        default="data/processed/chunks.jsonl",
        help="Path to chunk JSONL",
    )
    index.add_argument(
        "--index-output",
        default="data/processed/retrieval_vectors.npy",
        help="Path for vector index (.npy)",
    )
    index.add_argument(
        "--meta-output",
        default="data/processed/retrieval_meta.jsonl",
        help="Path for retrieval metadata JSONL",
    )
    index.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name",
    )

    search = subparsers.add_parser("search", help="Search indexed chunks by query")
    search.add_argument("--query", required=True, help="Search question")
    search.add_argument(
        "--index-input",
        default="data/processed/retrieval_vectors.npy",
        help="Path to vector index (.npy)",
    )
    search.add_argument(
        "--meta-input",
        default="data/processed/retrieval_meta.jsonl",
        help="Path to retrieval metadata JSONL",
    )
    search.add_argument("--top-k", type=int, default=5, help="Top K results")
    search.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name",
    )

    notes = subparsers.add_parser(
        "notes", help="Generate grounded study notes from retrieval results"
    )
    notes.add_argument("--query", required=True, help="Study topic or question")
    notes.add_argument(
        "--index-input",
        default="data/processed/retrieval_vectors.npy",
        help="Path to vector index (.npy)",
    )
    notes.add_argument(
        "--meta-input",
        default="data/processed/retrieval_meta.jsonl",
        help="Path to retrieval metadata JSONL",
    )
    notes.add_argument(
        "--output",
        default="data/processed/notes.json",
        help="Path to notes JSON output",
    )
    notes.add_argument("--top-k", type=int, default=6, help="Top K evidence chunks")
    notes.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name",
    )

    quiz = subparsers.add_parser(
        "quiz", help="Generate quiz questions with answer key and citations"
    )
    quiz.add_argument("--query", required=True, help="Study topic or question")
    quiz.add_argument(
        "--index-input",
        default="data/processed/retrieval_vectors.npy",
        help="Path to vector index (.npy)",
    )
    quiz.add_argument(
        "--meta-input",
        default="data/processed/retrieval_meta.jsonl",
        help="Path to retrieval metadata JSONL",
    )
    quiz.add_argument(
        "--output",
        default="data/processed/quiz.json",
        help="Path to quiz JSON output",
    )
    quiz.add_argument(
        "--count",
        type=int,
        default=6,
        help="Number of questions to generate",
    )
    quiz.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model name",
    )

    subparsers.add_parser("plan", help="Print next implementation steps")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        summary = ingest_materials(
            input_path=args.input,
            output_path=args.output,
            min_chars=args.min_chars,
        )
        print(
            f"Ingest complete. records={summary['records']} "
            f"skipped_files={summary['skipped_files']} output={summary['output']}"
        )
        return

    if args.command == "plan":
        print("1) ingest 2) chunk 3) retrieve 4) notes 5) quiz")
        return

    if args.command == "chunk":
        summary = chunk_ingested_records(
            ingest_path=args.input,
            chunk_output_path=args.output,
            coverage_output_path=args.coverage_output,
            max_chars=args.max_chars,
            overlap_chars=args.overlap_chars,
            min_chunk_chars=args.min_chars,
        )
        print(
            f"Chunking complete. chunks={summary['chunks']} "
            f"covered={summary['covered_records']} "
            f"uncovered={summary['uncovered_records']} "
            f"coverage={summary['coverage_output']}"
        )
        return

    if args.command == "index":
        summary = build_index(
            chunks_path=args.input,
            index_path=args.index_output,
            meta_path=args.meta_output,
            model_name=args.model,
        )
        print(
            f"Index complete. vectors={summary['vectors']} dim={summary['dim']} "
            f"index={summary['index_path']} meta={summary['meta_path']}"
        )
        return

    if args.command == "search":
        rows = search_index(
            query=args.query,
            index_path=args.index_input,
            meta_path=args.meta_input,
            top_k=args.top_k,
            model_name=args.model,
        )
        for row in rows:
            print(json.dumps(row, ensure_ascii=True))
        return

    if args.command == "notes":
        summary = generate_notes(
            query=args.query,
            index_path=args.index_input,
            meta_path=args.meta_input,
            output_path=args.output,
            top_k=args.top_k,
            model_name=args.model,
        )
        print(
            f"Notes complete. output={summary['output']} "
            f"citations={summary['citations']}"
        )
        return

    if args.command == "quiz":
        summary = generate_quiz(
            query=args.query,
            index_path=args.index_input,
            meta_path=args.meta_input,
            output_path=args.output,
            question_count=args.count,
            model_name=args.model,
        )
        print(
            f"Quiz complete. output={summary['output']} "
            f"questions={summary['questions']} citations={summary['citations']}"
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
