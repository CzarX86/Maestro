import json
from pathlib import Path

import pytest

from src.maestro.documentation_agent import DocumentationAgent, AUTO_DOC_BEGIN, AUTO_DOC_END


def write_tmp_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_documentation_agent_updates_docs(tmp_path: Path):
    # Arrange: create a fake project structure under tmp
    project = tmp_path
    (project / "docs").mkdir()
    (project / "handoff").mkdir()
    (project / "reports").mkdir()

    # Seed templates
    write_tmp_file(project / "docs" / "templates" / "README.template.md", "# Project\n")
    write_tmp_file(project / "docs" / "templates" / "USER_MANUAL.template.md", "# Manual\n")
    write_tmp_file(project / "docs" / "templates" / "USAGE.template.md", "# Usage\n")

    # Seed handoff plan/spec
    plan = {"title": "Test Plan", "steps": [{"id": "s1", "description": "Do X"}]}
    write_tmp_file(project / "handoff" / "plan.json", json.dumps(plan))
    spec = (
        "# Spec\n\n"
        "## Objetivo\nO objetivo é testar.\n\n"
        "## Escopo incluído\n- Item A\n- Item B\n\n"
        "## Escopo excluído\n- Fora X\n\n"
        "## Critérios de aceitação\n- [x] C1\n"
    )
    write_tmp_file(project / "handoff" / "spec.md", spec)

    # Seed qa.json
    qa = {
        "task_id": "demo-task",
        "passed": 10,
        "failed": 1,
        "coverage": 87.5,
        "lint_errors": 0,
        "type_errors": 0,
        "status": "soft-fail",
        "next_actions": ["Fix failing test"],
    }
    write_tmp_file(project / "reports" / "qa.json", json.dumps(qa))

    # Act
    agent = DocumentationAgent(project)
    outputs = agent.run(dry_run=True)

    # Assert: each output contains auto-doc block and key fields
    for dest, content in outputs.items():
        assert AUTO_DOC_BEGIN in content and AUTO_DOC_END in content
        assert "demo-task" in content
        assert "soft-fail" in content
        assert "Fix failing test" in content
        assert "Plano (Steps)" in content
        assert "Objetivo" in content


def test_agent_bootstraps_templates_from_existing_docs(tmp_path: Path):
    project = tmp_path
    (project / "docs").mkdir()
    (project / "handoff").mkdir()
    (project / "reports").mkdir()

    # Existing docs only (no templates)
    write_tmp_file(project / "README.md", "# Readme\n")
    write_tmp_file(project / "docs" / "USER_MANUAL.md", "# Manual\n")
    write_tmp_file(project / "docs" / "USAGE.md", "# Usage\n")

    # Minimal plan/spec/qa
    write_tmp_file(project / "handoff" / "plan.json", json.dumps({"title": "t", "steps": []}))
    write_tmp_file(project / "handoff" / "spec.md", "# Spec\n")
    write_tmp_file(project / "reports" / "qa.json", json.dumps({"task_id": "t", "passed": 0, "failed": 0, "coverage": 0, "lint_errors": 0, "type_errors": 0, "status": "pass", "next_actions": []}))

    agent = DocumentationAgent(project)
    agent.run(dry_run=False)

    # Templates should be created from existing docs
    assert (project / "docs" / "templates" / "README.template.md").exists()
    assert (project / "docs" / "templates" / "USER_MANUAL.template.md").exists()
    assert (project / "docs" / "templates" / "USAGE.template.md").exists()

    # And outputs updated with auto block
    assert AUTO_DOC_BEGIN in (project / "README.md").read_text(encoding="utf-8")
    assert AUTO_DOC_BEGIN in (project / "docs" / "USER_MANUAL.md").read_text(encoding="utf-8")
    assert AUTO_DOC_BEGIN in (project / "docs" / "USAGE.md").read_text(encoding="utf-8")

