#! /usr/bin/env python
import argparse
from cli.configure import configure

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--dry-run",
    action="store_true",
    help="Render templates using the existing config/secrets and print a diff "
    "against what's on disk, without writing any files or prompting.",
)
group.add_argument(
    "--apply",
    action="store_true",
    help="Re-render the real output files (e.g. secrets/pixelfed/.env) from the "
    "existing config/secrets, without prompting and without rewriting "
    "config/config.toml or secrets/config.toml. Run --dry-run first to preview.",
)
args = parser.parse_args()

configure(dry_run=args.dry_run, apply_only=args.apply)
