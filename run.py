"""Run from the project directory with Python 3.10 or later. No pip install."""

import argparse
import json
import sys
from pathlib import Path

from atlas.core import run_case, verify_report
from atlas.server import make_server


def main():
    parser = argparse.ArgumentParser(description="Agent Failure Atlas — local synthetic investigations")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--export", type=Path, metavar="NEW_DIRECTORY", help="Write both reports; no server")
    group.add_argument("--verify", type=Path, metavar="REPORT_JSON", help="Check report self-consistency")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.export:
        try:
            args.export.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            parser.error("Export directory already exists; choose a new directory")
        for mode in ["vulnerable", "repaired"]:
            report = run_case(mode)
            (args.export / f"{mode}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(f"{mode}: {report['verdict']} / {report['state']['order_count']} order(s) / "
                  f"{report['state']['spent_minor']} minor units")
        return 0
    if args.verify:
        try:
            data = json.loads(args.verify.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "reports" in data:
                valid = (isinstance(data["reports"], dict)
                         and set(data["reports"]) == {"vulnerable", "repaired"}
                         and all(verify_report(r) for r in data["reports"].values()))
            else:
                valid = verify_report(data)
        except (ValueError, OSError):
            valid = False
        print("Self-consistent (not a provenance attestation)" if valid else "Verification failed")
        return 0 if valid else 1
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    try:
        server = make_server(args.port)
    except OSError as exc:
        parser.error(f"Cannot start local server: {exc}. Try --port 8766")
    print(f"Agent Failure Atlas → http://127.0.0.1:{args.port}", flush=True)
    print("Synthetic data · deterministic controller · Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
