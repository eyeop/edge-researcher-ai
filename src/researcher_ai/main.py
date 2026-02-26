import argparse

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

    parser.print_help()


if __name__ == "__main__":
    main()
