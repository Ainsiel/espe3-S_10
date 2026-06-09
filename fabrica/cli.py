"""CLI de fabrica ARNES/SDD."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .evals import EvalRunner
from .harness import HarnessRunner
from .orchestrator import OrchestratorGraph
from .qa_audit import FactoryAuditor
from .storage import FactoryStorage


def init_factory(storage: FactoryStorage) -> None:
    storage.ensure_layout()
    storage.ensure_canonical_design_docs()
    harness = HarnessRunner(storage)
    harness.snapshot_registries()
    work_order = storage.default_work_order()
    storage.write_json("work_order.json", work_order)


def run_factory(storage: FactoryStorage) -> dict:
    storage.ensure_layout()
    storage.ensure_canonical_design_docs()
    storage.reset_run_outputs()
    harness = HarnessRunner(storage)
    harness.snapshot_registries()
    project_work_order = storage.project_path / "work_order.json"
    if project_work_order.exists():
        work_order = storage.read_json(project_work_order, default=None)
    else:
        work_order = storage.read_json("work_order.json", default=None) or storage.default_work_order()
        storage.write_json("work_order.json", work_order)
    result = OrchestratorGraph(harness).run(work_order, str(storage.project_path))
    state = storage.read_json("state.json", default={}) or {}
    state["orchestrator_result"] = result
    storage.write_json("state.json", state)
    return result


def verify_factory(storage: FactoryStorage) -> dict:
    storage.ensure_layout()
    report = FactoryAuditor(storage).audit()
    eval_report = EvalRunner(storage.root).run()
    storage.write_json("reports/eval-report.json", eval_report)
    report["evals"] = {
        "reproducibility_practical_percentage": eval_report["reproducibility_practical_percentage"],
        "evals_total": eval_report["evals_total"],
        "evals_passed": eval_report["evals_passed"],
    }
    if eval_report["status"] != "complete":
        report["status"] = "error"
        report["decision"] = "needs_fix"
    storage.write_json("reports/checklist-audit.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fabrica")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--project", default="project", help="Carpeta de proyecto independiente")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("run")
    sub.add_parser("verify")
    sub.add_parser("eval")
    args = parser.parse_args(argv)
    storage = FactoryStorage(Path(args.root), project=args.project)
    if args.command == "init":
        init_factory(storage)
        print("initialized")
    elif args.command == "run":
        result = run_factory(storage)
        print(result["status"])
    elif args.command == "verify":
        report = verify_factory(storage)
        print(report["status"])
    elif args.command == "eval":
        storage.ensure_layout()
        report = EvalRunner(storage.root).run()
        storage.write_json("reports/eval-report.json", report)
        print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
