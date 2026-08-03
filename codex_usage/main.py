from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

from .client import CodexClientError, find_codex, read_usage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codex usage indicator for Linux")
    parser.add_argument("--check", action="store_true", help="check CLI and account connectivity")
    parser.add_argument("--self-test", action="store_true", help="run automated tests")
    parser.add_argument("--service", action="store_true", help="run the Plasma data service")
    args = parser.parse_args(argv)

    if args.self_test:
        tests_dir = Path(__file__).resolve().parent.parent / "tests"
        suite = unittest.defaultTestLoader.discover(str(tests_dir))
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1

    if args.check:
        try:
            executable = find_codex()
            snapshots = read_usage()
        except CodexClientError as error:
            print(f"Codex Usage check failed: {error}", file=sys.stderr)
            return 1
        print(f"Codex CLI: {executable}")
        print(f"Usage connection: working ({len(snapshots)} windows available)")
        return 0

    if args.service:
        from .service import run_service

        return run_service()

    try:
        from .tray import UsageTray
    except (ImportError, ValueError) as error:
        print(f"Could not load the Linux tray libraries: {error}", file=sys.stderr)
        return 1
    UsageTray().run()
    return 0
