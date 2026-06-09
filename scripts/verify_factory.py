#!/usr/bin/env python3
"""Verificacion local de fabrica: unittest + checklist + evals."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fabrica.cli import init_factory, run_factory, verify_factory
from fabrica.storage import FactoryStorage


def main() -> int:
    root = ROOT
    storage = FactoryStorage(root)
    init_factory(storage)
    run_result = run_factory(storage)
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    storage.write_json(
        "test_report.json",
        {
            "status": "pass" if tests.returncode == 0 else "fail",
            "command": "python -m unittest discover -s tests",
            "returncode": tests.returncode,
            "stdout": tests.stdout,
            "stderr": tests.stderr,
        },
    )
    audit = verify_factory(storage)
    ok = run_result["status"] == "complete" and tests.returncode == 0 and audit["status"] == "complete"
    print("factory_verify_status=" + ("complete" if ok else "error"))
    print("run_status=" + run_result["status"])
    print("tests_returncode=" + str(tests.returncode))
    print("audit_status=" + audit["status"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
