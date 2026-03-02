"""CLI entry point for coop-claude."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .models import Role
from .bus import SharedBus
from .station import Station
from .relay import CoopRelay, RelayClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coop-claude",
        description="Multiplayer Claude Code sessions",
    )
    sub = parser.add_subparsers(dest="command")

    # ── start ─────────────────────────────────────────────────────
    sp = sub.add_parser("start", help="Start a co-op session (host)")
    sp.add_argument("--name", "-n", required=True, help="Your name")
    sp.add_argument("--role", "-r", default="architect",
                    choices=[r.value for r in Role])
    sp.add_argument("--project", "-d", default=".",
                    help="Project directory")
    sp.add_argument("--partner", default="Partner",
                    help="Partner's display name")
    sp.add_argument("--serve", "-s", action="store_true",
                    help="Enable TCP relay for remote partner")
    sp.add_argument("--port", type=int, default=7723)

    # ── join ──────────────────────────────────────────────────────
    jp = sub.add_parser("join", help="Join a co-op session")
    jp.add_argument("--name", "-n", required=True)
    jp.add_argument("--role", "-r", default="ux",
                    choices=[r.value for r in Role])
    jp.add_argument("--project", "-d", default=".")
    jp.add_argument("--partner", default="Partner")
    jp.add_argument("--host", default=None,
                    help="Relay host (omit for same-machine)")
    jp.add_argument("--port", type=int, default=7723)

    # ── status ────────────────────────────────────────────────────
    sub.add_parser("status", help="Show session status")

    # ── stop ──────────────────────────────────────────────────────
    sub.add_parser("stop", help="End the session")

    return parser


async def async_main(args):
    bus = SharedBus()

    if args.command == "start":
        project = str(Path(args.project).resolve())
        station = Station(
            human_name=args.name,
            role=Role(args.role),
            partner_name=args.partner,
            project_path=project,
            bus=bus,
        )
        tasks = [asyncio.create_task(station.start())]
        if args.serve:
            relay = CoopRelay(bus, port=args.port)
            tasks.append(asyncio.create_task(relay.start()))
        await asyncio.gather(*tasks, return_exceptions=True)

    elif args.command == "join":
        project = str(Path(args.project).resolve())
        station = Station(
            human_name=args.name,
            role=Role(args.role),
            partner_name=args.partner,
            project_path=project,
            bus=bus,
        )
        tasks = [asyncio.create_task(station.start())]
        if args.host:
            client = RelayClient(bus, host=args.host, port=args.port)
            tasks.append(asyncio.create_task(client.connect()))
        await asyncio.gather(*tasks, return_exceptions=True)

    elif args.command == "status":
        tasks = bus.list_tasks()
        log = bus.log_path
        print(f"Session dir: {bus.base_dir}")
        print(f"Tasks: {len(tasks)}")
        if log.exists():
            line_count = sum(1 for _ in open(log))
            print(f"Log: {line_count} lines")

    elif args.command == "stop":
        archive = bus.archive_session()
        import shutil
        shutil.rmtree(bus.base_dir, ignore_errors=True)
        print(f"Session ended. Log: {archive}")


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
