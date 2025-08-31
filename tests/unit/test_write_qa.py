
import pytest
import sys
import os
import json
from pathlib import Path
import shutil

# Add orchestrator to path to import the script
sys.path.append(str(Path(__file__).parent.parent.parent / "orchestrator"))

# Now import the functions from the script
from write_qa import (
    extract_coverage,
    extract_test_results,
    extract_lint_errors,
    extract_type_errors,
    determine_status,
    generate_next_actions,
    main as write_qa_main,
)

# --- Mock Data ---

MOCK_PYTEST_PASS_OUTPUT = """
============================= test session starts ==============================
...
collected 5 items

tests/smoke/test_orchestrator.py .....                                   [100%]

============================== 5 passed in 0.01s ===============================
---------- coverage: platform darwin, python 3.10.9-final-0 -----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/some_module.py           10      1    90%
---------------------------------------------
TOTAL                        10      1    90%
"""

MOCK_PYTEST_FAIL_OUTPUT = """
============================= test session starts ==============================
...
collected 5 items

tests/smoke/test_orchestrator.py ...F.                                   [ 80%]
tests/smoke/test_orchestrator.py::test_something FAILED                  [ 80%]
AssertionError: assert False
============================== 1 failed, 4 passed in 0.05s ===============================
---------- coverage: platform darwin, python 3.10.9-final-0 -----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/some_module.py           10      4    60%
---------------------------------------------
TOTAL                        10      4    60%
"""

MOCK_LINT_ERROR_OUTPUT = """
src/main.py:1:1: F401 'os' imported but unused
src/main.py:5:1: E302 expected 2 blank lines, found 1
Found 2 errors.
error: Found 2 errors.
"""

MOCK_TYPE_ERROR_OUTPUT = """
src/main.py:10: error: Incompatible types in assignment (expression has type "str", variable has type "int")
Found 1 error in 1 file (checked 1 source file)
"""

# --- Unit Tests for Helper Functions ---

def test_extract_coverage():
    assert extract_coverage(MOCK_PYTEST_PASS_OUTPUT) == 90.0
    assert extract_coverage(MOCK_PYTEST_FAIL_OUTPUT) == 60.0
    assert extract_coverage("No coverage info here") == 0.0
    assert extract_coverage("") == 0.0

def test_extract_test_results():
    pass_results = extract_test_results(MOCK_PYTEST_PASS_OUTPUT)
    assert pass_results["passed"] == 5
    assert pass_results["failed"] == 0

    fail_results = extract_test_results(MOCK_PYTEST_FAIL_OUTPUT)
    assert fail_results["passed"] == 4
    assert fail_results["failed"] == 1

    empty_results = extract_test_results("")
    assert empty_results["passed"] == 0
    assert empty_results["failed"] == 0

def test_extract_lint_errors():
    assert extract_lint_errors(MOCK_LINT_ERROR_OUTPUT) == 2
    assert extract_lint_errors("Looks good!") == 0
    assert extract_lint_errors("") == 0

def test_extract_type_errors():
    assert extract_type_errors(MOCK_TYPE_ERROR_OUTPUT) == 2
    assert extract_type_errors("Success: no issues found") == 0
    assert extract_type_errors("") == 0

def test_determine_status():
    assert determine_status("0", "0", "0") == "pass"
    assert determine_status("0", "0", "1") == "soft-fail"
    assert determine_status("1", "0", "1") == "fail"
    assert determine_status("1", "1", "1") == "fail"

def test_generate_next_actions():
    actions = generate_next_actions("1", "1", "1", "unused import", "incompatible types", "assertion error")
    assert "Corrigir erros de linting" in actions
    assert "Remover imports não utilizados" in actions
    assert "Corrigir erros de type checking" in actions
    assert "Corrigir incompatibilidades de tipo" in actions
    assert "Corrigir testes falhando" in actions
    assert "Verificar asserções dos testes" in actions
    assert len(actions) == 6

# --- Integration Test for main() ---

@pytest.fixture
def setup_test_environment(tmp_path):
    """Set up a temporary directory for testing main script."""
    original_cwd = Path.cwd()
    # Create a temporary structure similar to the real project
    test_dir = tmp_path / "maestro_test"
    (test_dir / "reports").mkdir(parents=True)
    (test_dir / "orchestrator").mkdir()
    os.chdir(test_dir)
    
    # Copy the script to the temp orchestrator
    shutil.copy(original_cwd / "orchestrator" / "write_qa.py", test_dir / "orchestrator" / "write_qa.py")

    yield test_dir

    # Teardown
    os.chdir(original_cwd)


def test_main_function_pass_scenario(setup_test_environment):
    """Test the main function with a successful scenario."""
    task_id = "test_pass"
    
    # Mock sys.argv
    sys.argv = [
        "write_qa.py",
        "--task", task_id,
        "--lint_rc", "0",
        "--lint_out", "Success",
        "--types_rc", "0",
        "--types_out", "Success",
        "--tests_rc", "0",
        "--tests_out", MOCK_PYTEST_PASS_OUTPUT,
    ]

    write_qa_main()

    # Verify output file
    report_path = Path("reports") / "qa.json"
    assert report_path.exists()

    with open(report_path, "r") as f:
        report = json.load(f)

    assert report["task_id"] == task_id
    assert report["status"] == "pass"
    assert report["passed"] == 5
    assert report["failed"] == 0
    assert report["coverage"] == 90.0
    assert report["lint_errors"] == 0
    assert report["type_errors"] == 0
    assert len(report["next_actions"]) == 0

def test_main_function_fail_scenario(setup_test_environment):
    """Test the main function with a failure scenario."""
    task_id = "test_fail"
    
    # Mock sys.argv
    sys.argv = [
        "write_qa.py",
        "--task", task_id,
        "--lint_rc", "1",
        "--lint_out", MOCK_LINT_ERROR_OUTPUT,
        "--types_rc", "1",
        "--types_out", MOCK_TYPE_ERROR_OUTPUT,
        "--tests_rc", "1",
        "--tests_out", MOCK_PYTEST_FAIL_OUTPUT,
    ]

    write_qa_main()

    # Verify output file
    report_path = Path("reports") / "qa.json"
    assert report_path.exists()

    with open(report_path, "r") as f:
        report = json.load(f)

    assert report["task_id"] == task_id
    assert report["status"] == "fail"
    assert report["passed"] == 4
    assert report["failed"] == 1
    assert report["coverage"] == 60.0
    assert report["lint_errors"] == 2
    assert report["type_errors"] == 2
    assert len(report["next_actions"]) > 0
    assert "Corrigir erros de linting" in report["next_actions"]
    assert "Corrigir erros de type checking" in report["next_actions"]
    assert "Corrigir testes falhando" in report["next_actions"]

