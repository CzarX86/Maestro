"""
Documentation Agent for Maestro

Generates and updates project documentation (README.md, USER_MANUAL.md, USAGE.md)
based on QA reports (reports/qa.json), handoff plan/spec, and templates. The
agent maintains an auto-generated section delimited by markers to preserve
manual content while keeping live status up to date.

Usage:
  python -m src.maestro.documentation_agent [--project-root .] [--dry-run]

Environment:
  DASHBOARD_URL: optional WebSocket URL to broadcast updates (e.g. ws://localhost:8765)
"""

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import websockets  # type: ignore
except Exception:  # pragma: no cover - optional dependency available in repo
    websockets = None  # type: ignore


logger = logging.getLogger(__name__)


AUTO_DOC_BEGIN = "<!-- BEGIN AUTO-DOC: DocumentationAgent -->"
AUTO_DOC_END = "<!-- END AUTO-DOC -->"


@dataclass
class QAReport:
    task_id: str
    passed: int
    failed: int
    coverage: float
    lint_errors: int
    type_errors: int
    status: str
    next_actions: List[str]
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None

    @classmethod
    def load(cls, path: Path) -> "QAReport":
        if not path.exists():
            raise FileNotFoundError(f"QA report not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            task_id=data.get("task_id", "unknown"),
            passed=int(data.get("passed", 0)),
            failed=int(data.get("failed", 0)),
            coverage=float(data.get("coverage", 0.0)),
            lint_errors=int(data.get("lint_errors", 0)),
            type_errors=int(data.get("type_errors", 0)),
            status=str(data.get("status", "fail")),
            next_actions=list(data.get("next_actions", [])),
            timestamp_start=data.get("timestamp_start"),
            timestamp_end=data.get("timestamp_end"),
        )


def read_section_from_spec(spec_text: str, header: str) -> str:
    """Extracts a markdown section body by header title (## Header)."""
    # Match '## Header' until next '## ' or end of file
    pattern = rf"^##\s+{re.escape(header)}\n(.*?)(?=\n##\s+|\Z)"
    m = re.search(pattern, spec_text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def bullet_list(items: List[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {it}" for it in items)


def plan_steps_from_json(plan: Dict) -> List[str]:
    steps = []
    for s in plan.get("steps", []):
        sid = s.get("id", "step")
        desc = s.get("description", "")
        steps.append(f"{sid}: {desc}")
    return steps


def emoji_for_status(status: str) -> str:
    s = status.lower()
    if s == "pass":
        return "🟢"
    if s == "soft-fail":
        return "🟡"
    return "🔴"


class DocumentationAgent:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.docs_dir = self.root / "docs"
        self.templates_dir = self.docs_dir / "templates"
        self.readme_path = self.root / "README.md"
        self.user_manual_path = self.docs_dir / "USER_MANUAL.md"
        self.usage_path = self.docs_dir / "USAGE.md"
        self.qa_path = self.root / "reports" / "qa.json"
        self.plan_path = self.root / "handoff" / "plan.json"
        self.spec_path = self.root / "handoff" / "spec.md"

    def ensure_templates(self) -> None:
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        # If templates are missing, bootstrap by copying current docs
        mapping = {
            self.readme_path: self.templates_dir / "README.template.md",
            self.user_manual_path: self.templates_dir / "USER_MANUAL.template.md",
            self.usage_path: self.templates_dir / "USAGE.template.md",
        }
        for src, dst in mapping.items():
            if src.exists() and not dst.exists():
                try:
                    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                    logger.info(f"Template created from {src} -> {dst}")
                except Exception as e:
                    logger.warning(f"Failed to initialize template {dst}: {e}")

    def backup_file(self, path: Path) -> None:
        try:
            if not path.exists():
                return
            backups_dir = self.docs_dir / "backups"
            backups_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            backup = backups_dir / f"{path.name}.{ts}.bak"
            backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info(f"Backup created: {backup}")
        except Exception as e:
            logger.warning(f"Could not backup {path}: {e}")

    def load_optional_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def build_auto_doc_block(self, qa: QAReport) -> str:
        now = datetime.utcnow().isoformat() + "Z"
        spec_text = self.load_optional_text(self.spec_path)
        plan_text = self.load_optional_text(self.plan_path)

        # Parse plan/spec
        plan_json: Dict = {}
        if plan_text.strip():
            try:
                plan_json = json.loads(plan_text)
            except Exception:
                plan_json = {}

        objetivo = read_section_from_spec(spec_text, "Objetivo")
        escopo_in = read_section_from_spec(spec_text, "Escopo incluído")
        escopo_out = read_section_from_spec(spec_text, "Escopo excluído")
        criterios = read_section_from_spec(spec_text, "Critérios de aceitação")

        plan_steps = plan_steps_from_json(plan_json)

        lines = [
            AUTO_DOC_BEGIN,
            "",
            f"## 📚 Documentation Status {emoji_for_status(qa.status)}",
            "",
            f"- Task: `{qa.task_id}`",
            f"- Status: `{qa.status}`",
            f"- Tests: `{qa.passed}` passed, `{qa.failed}` failed",
            f"- Coverage: `{qa.coverage}%`",
            f"- Lint errors: `{qa.lint_errors}` | Type errors: `{qa.type_errors}`",
            f"- Last updated: `{now}`",
            "",
            "### Next Actions",
            bullet_list(qa.next_actions),
        ]

        if objetivo:
            lines += ["", "### Objetivo (Spec)", objetivo]
        if escopo_in:
            lines += ["", "### Escopo incluído (Spec)", escopo_in]
        if escopo_out:
            lines += ["", "### Escopo excluído (Spec)", escopo_out]
        if criterios:
            lines += ["", "### Critérios de aceitação (Spec)", criterios]
        if plan_steps:
            lines += ["", "### Plano (Steps)", bullet_list(plan_steps)]

        lines += ["", AUTO_DOC_END, ""]
        return "\n".join(lines)

    def upsert_auto_block(self, base_text: str, block: str) -> str:
        if AUTO_DOC_BEGIN in base_text and AUTO_DOC_END in base_text:
            # Replace content between markers
            pattern = re.compile(
                re.escape(AUTO_DOC_BEGIN) + r"[\s\S]*?" + re.escape(AUTO_DOC_END),
                re.MULTILINE,
            )
            return pattern.sub(block, base_text)
        # Append block
        sep = "\n\n" if base_text and not base_text.endswith("\n") else "\n"
        return base_text + sep + block

    async def _maybe_broadcast(self, qa: QAReport) -> None:
        url = os.environ.get("DASHBOARD_URL")
        if not url or not websockets:  # pragma: no cover - optional path
            return
        try:
            async with websockets.connect(url) as ws:  # type: ignore
                payload = {
                    "type": "doc_update",
                    "task": qa.task_id,
                    "status": qa.status,
                    "passed": qa.passed,
                    "failed": qa.failed,
                    "coverage": qa.coverage,
                    "lint_errors": qa.lint_errors,
                    "type_errors": qa.type_errors,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                await ws.send(json.dumps(payload))
        except Exception as e:  # pragma: no cover - network dependent
            logger.warning(f"Dashboard broadcast failed: {e}")

    def run(self, dry_run: bool = False) -> Dict[str, str]:
        """Process templates and update documentation.

        Returns a mapping of output file to generated content.
        """
        self.ensure_templates()

        qa = QAReport.load(self.qa_path)
        block = self.build_auto_doc_block(qa)

        outputs: Dict[str, str] = {}
        files = [
            (self.templates_dir / "README.template.md", self.readme_path),
            (self.templates_dir / "USER_MANUAL.template.md", self.user_manual_path),
            (self.templates_dir / "USAGE.template.md", self.usage_path),
        ]

        for template_path, dest_path in files:
            base = template_path.read_text(encoding="utf-8") if template_path.exists() else ""
            updated = self.upsert_auto_block(base, block)
            outputs[str(dest_path)] = updated
            if not dry_run:
                self.backup_file(dest_path)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_text(updated, encoding="utf-8")
                logger.info(f"Updated: {dest_path}")

        # Best-effort dashboard notify
        try:
            import asyncio

            asyncio.run(self._maybe_broadcast(qa))
        except Exception:
            pass

        return outputs


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Maestro Documentation Agent")
    p.add_argument("--project-root", default=".", help="Project root directory")
    p.add_argument("--dry-run", action="store_true", help="Do not write files")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    agent = DocumentationAgent(Path(args.project_root))
    try:
        agent.run(dry_run=args.dry_run)
        return 0
    except FileNotFoundError as e:
        logger.error(str(e))
        return 2
    except Exception as e:
        logger.error(f"Documentation agent failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

