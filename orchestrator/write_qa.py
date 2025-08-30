#!/usr/bin/env python3
"""
Script para gerar relatórios QA do orquestrador.
Consolida métricas de linting, type checking e testes em um único arquivo JSON.
"""

import argparse
import json
import time
import datetime
import sys
import re
from pathlib import Path


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Gerar relatório QA")
    parser.add_argument("--task", required=True, help="ID da task")
    parser.add_argument("--lint_rc", required=True, help="Código de retorno do linting")
    parser.add_argument("--lint_out", default="", help="Output do linting")
    parser.add_argument("--types_rc", required=True, help="Código de retorno do type checking")
    parser.add_argument("--types_out", default="", help="Output do type checking")
    parser.add_argument("--tests_rc", required=True, help="Código de retorno dos testes")
    parser.add_argument("--tests_out", default="", help="Output dos testes")
    return parser.parse_args()


def extract_coverage(output):
    """Extrai cobertura de testes do output do pytest."""
    if not output:
        return 0.0
    
    # Padrão para cobertura do pytest
    coverage_pattern = r"TOTAL\s+\d+\s+\d+\s+(\d+)%"
    match = re.search(coverage_pattern, output)
    
    if match:
        return float(match.group(1))
    return 0.0


def extract_test_results(output):
    """Extrai resultados de testes do output do pytest."""
    if not output:
        return {"passed": 0, "failed": 0, "tests_run": []}
    
    # Padrões para resultados de testes
    passed_pattern = r"(\d+) passed"
    failed_pattern = r"(\d+) failed"
    
    passed_match = re.search(passed_pattern, output)
    failed_match = re.search(failed_pattern, output)
    
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    
    # Lista de testes executados (simplificado)
    tests_run = []
    if passed > 0:
        tests_run.append({"name": "unit_tests", "status": "pass"})
    if failed > 0:
        tests_run.append({"name": "unit_tests", "status": "fail"})
    
    return {
        "passed": passed,
        "failed": failed,
        "tests_run": tests_run
    }


def extract_lint_errors(output):
    """Extrai número de erros de linting."""
    if not output:
        return 0
    
    # Contar linhas que indicam erros
    error_lines = [line for line in output.split('\n') if 'error' in line.lower()]
    return len(error_lines)


def extract_type_errors(output):
    """Extrai número de erros de type checking."""
    if not output:
        return 0
    
    # Contar linhas que indicam erros de tipo
    error_lines = [line for line in output.split('\n') if 'error' in line.lower()]
    return len(error_lines)


def determine_status(lint_rc, types_rc, tests_rc):
    """Determina status geral baseado nos códigos de retorno."""
    if lint_rc == "0" and types_rc == "0" and tests_rc == "0":
        return "pass"
    elif lint_rc == "0" and types_rc == "0":
        return "soft-fail"  # Testes falharam mas lint/types ok
    else:
        return "fail"


def generate_next_actions(lint_rc, types_rc, tests_rc, lint_out, types_out, tests_out):
    """Gera lista de próximas ações baseada nos resultados."""
    actions = []
    
    if lint_rc != "0":
        actions.append("Corrigir erros de linting")
        if "unused import" in lint_out:
            actions.append("Remover imports não utilizados")
        if "line too long" in lint_out:
            actions.append("Quebrar linhas muito longas")
    
    if types_rc != "0":
        actions.append("Corrigir erros de type checking")
        if "missing type annotation" in types_out:
            actions.append("Adicionar anotações de tipo")
        if "incompatible types" in types_out:
            actions.append("Corrigir incompatibilidades de tipo")
    
    if tests_rc != "0":
        actions.append("Corrigir testes falhando")
        if "assertion error" in tests_out:
            actions.append("Verificar asserções dos testes")
        if "import error" in tests_out:
            actions.append("Verificar imports dos testes")
    
    return actions


def calculate_perf_metrics(start_time, end_time):
    """Calcula métricas de performance."""
    elapsed_sec = (end_time - start_time).total_seconds()
    
    return {
        "elapsed_sec_total": elapsed_sec,
        "timestamp_start": start_time.isoformat() + "Z",
        "timestamp_end": end_time.isoformat() + "Z"
    }


def main():
    """Função principal."""
    args = parse_arguments()
    
    # Timestamps
    start_time = datetime.datetime.utcnow()
    end_time = start_time
    
    # Extrair métricas dos outputs
    coverage = extract_coverage(args.tests_out)
    test_results = extract_test_results(args.tests_out)
    lint_errors = extract_lint_errors(args.lint_out)
    type_errors = extract_type_errors(args.types_out)
    
    # Determinar status
    status = determine_status(args.lint_rc, args.types_rc, args.tests_rc)
    
    # Gerar próximas ações
    next_actions = generate_next_actions(
        args.lint_rc, args.types_rc, args.tests_rc,
        args.lint_out, args.types_out, args.tests_out
    )
    
    # Calcular métricas de performance
    perf_metrics = calculate_perf_metrics(start_time, end_time)
    
    # Construir relatório QA
    qa_report = {
        "task_id": args.task,
        "tests_run": test_results["tests_run"],
        "passed": test_results["passed"],
        "failed": test_results["failed"],
        "coverage": coverage,
        "lint_errors": lint_errors,
        "type_errors": type_errors,
        "security_findings": 0,  # Placeholder para futuras implementações
        "perf_metrics": perf_metrics,
        "status": status,
        "next_actions": next_actions,
        "artifacts": [
            "handoff/plan.json",
            "handoff/spec.md",
            f"logs/{args.task}.lint.out",
            f"logs/{args.task}.types.out",
            f"logs/{args.task}.tests.out"
        ],
        "timestamp_start": perf_metrics["timestamp_start"],
        "timestamp_end": perf_metrics["timestamp_end"],
        "elapsed_sec": perf_metrics["elapsed_sec_total"]
    }
    
    # Salvar relatório
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    qa_file = reports_dir / "qa.json"
    with open(qa_file, "w", encoding="utf-8") as f:
        json.dump(qa_report, f, indent=2, ensure_ascii=False)
    
    # Output para stdout (para compatibilidade com shell scripts)
    print(json.dumps(qa_report, indent=2))
    
    # Log de conclusão
    print(f"📊 Relatório QA salvo em: {qa_file}", file=sys.stderr)
    print(f"📈 Status: {status}", file=sys.stderr)
    print(f"⏱️  Tempo total: {perf_metrics['elapsed_sec_total']:.2f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
