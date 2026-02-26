import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="researcher-ai",
        description="Local-first Edge Researcher AI",
    )
    subparsers = parser.add_subparsers(dest="command")

    ingest = subparsers.add_parser("ingest", help="Ingest study materials")
    ingest.add_argument("--input", required=True, help="Path to input file or folder")

    subparsers.add_parser("plan", help="Print next implementation steps")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        print(f"[TODO] ingest pipeline for: {args.input}")
        return

    if args.command == "plan":
        print("1) ingest 2) chunk 3) retrieve 4) notes 5) quiz")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
