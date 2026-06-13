import argparse
import json
import logging

from .db.client import get_client, insert_entity
from .pipeline.run import run as run_pipeline


def add_source(args: argparse.Namespace) -> None:
    client = get_client()
    payload = {
        "name": args.name,
        "url": args.url,
        "source_type": args.type,
        "topic": args.topic,
        "tags": args.tags or [],
    }
    res = client.table("sources").insert(payload).execute()
    print(json.dumps(res.data[0], indent=2, default=str))


def add_entity(args: argparse.Namespace) -> None:
    client = get_client()
    metadata = {}
    if args.filing_forms:
        metadata["filing_forms"] = args.filing_forms
    row = insert_entity(
        client,
        name=args.name,
        entity_type=args.type,
        query_template=args.query_template,
        cik=args.cik,
        tags=args.tags or [],
        metadata=metadata,
    )
    print(json.dumps(row, indent=2, default=str))


def run_now(args: argparse.Namespace) -> None:
    run_id = run_pipeline(trigger="manual")
    print(f"Run completed: {run_id}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="research-orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add-source", help="Register a new source to monitor")
    add_p.add_argument("name")
    add_p.add_argument("url")
    add_p.add_argument("--type", default="html", choices=["html", "rss", "api", "sitemap"])
    add_p.add_argument("--topic", help="Topic used for the 'what's new' web search")
    add_p.add_argument("--tags", nargs="*")
    add_p.set_defaults(func=add_source)

    entity_p = sub.add_parser("add-entity", help="Register an entity to track (company, officer, partner, competitor, topic)")
    entity_p.add_argument("name")
    entity_p.add_argument("--type", required=True, choices=["company", "officer", "partner", "competitor", "topic"])
    entity_p.add_argument("--query-template", help="e.g. '{name} Workday partnership' (defaults to '{name} Workday')")
    entity_p.add_argument("--cik", help="SEC CIK, for company entities tracked via EDGAR")
    entity_p.add_argument("--tags", nargs="*")
    entity_p.add_argument("--filing-forms", nargs="*", help="SEC form types to track, e.g. 8-K 4 (company entities only)")
    entity_p.set_defaults(func=add_entity)

    run_p = sub.add_parser("run", help="Run the harvester for all active sources")
    run_p.set_defaults(func=run_now)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
