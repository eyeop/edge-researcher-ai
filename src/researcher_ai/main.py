import argparse

from researcher_ai.chunking.pipeline import chunk_ingested_records
from researcher_ai.ingest.pipeline import ingest_materials


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

    parser.print_help()


if __name__ == "__main__":
    main()
