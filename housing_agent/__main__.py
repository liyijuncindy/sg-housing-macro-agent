"""Command-line entry point."""
import argparse
import json
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Auditable Singapore housing macroeconomic research agent")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Download, evaluate, select and report in one workflow")
    run.add_argument("--as-of", required=True, help="YYYY-MM-DD; latest-vintage observation cutoff, not a historical information set")
    run.add_argument("--output", required=True, type=Path, help="New run directory; existing paths will not be overwritten")
    run.add_argument("--mode", choices=["rules", "llm"], default="rules", help="rules is a deterministic baseline; llm makes live model calls")
    run.add_argument("--limit", type=int, default=5, help="Maximum indicators, selected from eligible candidates")
    run.add_argument("--provider", choices=["openai", "soclaas"], help="LLM provider; overrides LLM_PROVIDER (default: openai)")
    run.add_argument("--model", help="Tool-capable model for the chosen provider; overrides OPENAI_MODEL or SOCLAAS_MODEL")
    run.add_argument("--timeout", type=float, default=20, help="Per-source HTTP timeout in seconds")
    run.add_argument("--source-run", type=Path, help="Explicitly reuse verified official data from a saved run; LLM calls remain live")
    run.add_argument("--source-policy", choices=["auto", "singstat"], default="auto", help="auto tries SingStat first for every candidate, rechecks transient failures, then uses reviewed MOM/MAS backups; singstat never uses backups")
    rep = sub.add_parser("replay", help="Verify and regenerate a saved report without network access")
    rep.add_argument("run_dir", type=Path)
    rep.add_argument("--output", type=Path, required=True)
    pool = sub.add_parser("indicator-pool", help="Export the full indicator table from a verified saved run, without data or model calls")
    pool.add_argument("run_dir", type=Path)
    pool.add_argument("--output", type=Path, required=True, help="New directory outside the immutable source run")
    disc = sub.add_parser("discover", help="Search official SingStat table metadata and preserve responses")
    disc.add_argument("query")
    disc.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            from .pipeline import run_workflow
            result = run_workflow(args.as_of, args.output, args.mode, args.limit, args.model, args.timeout, provider=args.provider, source_run=args.source_run, source_policy=args.source_policy)
            print(json.dumps({key: result.get(key) for key in ("status", "selected_ids", "mode", "provider", "model", "actual_models", "usage", "elapsed_seconds", "agent_elapsed_seconds")}, indent=2))
        elif args.command == "replay":
            from .pipeline import replay
            print(json.dumps(replay(args.run_dir, args.output), indent=2))
        elif args.command == "indicator-pool":
            from .pipeline import export_indicator_pool
            print(json.dumps(export_indicator_pool(args.run_dir, args.output), ensure_ascii=False, indent=2))
        else:
            from .sources import SingStatClient
            from .storage import write_json
            args.output.mkdir(parents=True, exist_ok=False)
            client = SingStatClient(args.output)
            try:
                records = client.discover(args.query)
                write_json(args.output / "discovery.json", records)
                print(json.dumps(records, ensure_ascii=False, indent=2))
            finally:
                client.save_records()
        return 0
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
