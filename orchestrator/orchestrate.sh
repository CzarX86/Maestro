#!/usr/bin/env bash
set -euo pipefail

# Configurações
TASK="${1:?use: orchestrate.sh <task_id>}"
ISSUE="issues/${TASK}.md"
TIMEZONE="America/Sao_Paulo"

# Função para timestamps
ts() { 
    TZ=$TIMEZONE date +"%Y-%m-%dT%H:%M:%S%z"
}

# Função para logging
log() {
    echo "[$1] $(ts) $2" | tee -a "logs/${TASK}.${1,,}.log"
}

# Função para verificar se arquivo existe
check_file() {
    if [[ ! -f "$1" ]]; then
        log "ERROR" "Arquivo não encontrado: $1"
        exit 1
    fi
}

# Função para validar ambiente
validate_env() {
    log "INIT" "Validando ambiente para task=$TASK"
    
    # Verificar se issue existe
    check_file "$ISSUE"
    
    # Verificar se CLIs estão disponíveis
    command -v gemini >/dev/null 2>&1 || { log "ERROR" "gemini CLI não encontrado"; exit 1; }
    command -v codex >/dev/null 2>&1 || { log "ERROR" "codex CLI não encontrado"; exit 1; }
    command -v cursor >/dev/null 2>&1 || { log "ERROR" "cursor CLI não encontrado"; exit 1; }
    
    # Verificar se secrets estão configurados
    if [[ -f "secrets/.env" ]]; then
        log "INIT" "Secrets encontrados"
    else
        log "WARN" "secrets/.env não encontrado - usando configuração padrão"
    fi
    
    log "INIT" "Ambiente validado com sucesso"
}

# Função para executar com timeout
run_with_timeout() {
    local timeout=$1
    local stage=$2
    shift 2
    
    log "$stage" "Iniciando com timeout=${timeout}s"
    local start_time=$(date +%s)
    
    if timeout "$timeout" "$@"; then
        local end_time=$(date +%s)
        local elapsed=$((end_time - start_time))
        log "$stage" "Concluído em ${elapsed}s"
    else
        local end_time=$(date +%s)
        local elapsed=$((end_time - start_time))
        log "$stage" "Falhou após ${elapsed}s"
        return 1
    fi
}

# Função para aplicar diff com validação
apply_diff() {
    local diff_file="diffs/${TASK}.diff"
    
    if [[ -f "$diff_file" ]]; then
        log "INTEGRATE" "Aplicando diff: $diff_file"
        
        # Validar se diff está dentro dos limites
        local diff_size=$(wc -l < "$diff_file")
        local max_diff=1000  # Limite configurável
        
        if [[ $diff_size -gt $max_diff ]]; then
            log "ERROR" "Diff muito grande: ${diff_size} linhas (limite: ${max_diff})"
            return 1
        fi
        
        # Aplicar diff
        if cursor apply --from-diff "$diff_file"; then
            log "INTEGRATE" "Diff aplicado com sucesso"
        else
            log "ERROR" "Falha ao aplicar diff"
            return 1
        fi
    else
        log "INTEGRATE" "Nenhum diff encontrado - pulando aplicação"
    fi
}

# Função para executar testes locais
run_smoke_tests() {
    log "INTEGRATE" "Executando testes de fumaça"
    
    # Build local
    if cursor run "pip install -e ."; then
        log "INTEGRATE" "Build local bem-sucedido"
    else
        log "ERROR" "Build local falhou"
        return 1
    fi
    
    # Testes de fumaça
    if cursor run "pytest -q tests/smoke || true"; then
        log "INTEGRATE" "Testes de fumaça concluídos"
    else
        log "WARN" "Testes de fumaça falharam - continuando"
    fi
}

# Função para executar testes canônicos
run_canonical_tests() {
    log "TEST" "Executando suíte canônica de testes"
    
    # Linting
    log "TEST" "Executando linting"
    set +e
    ruff_out=$(ruff check . 2>&1); ruff_rc=$?
    set -e
    
    # Type checking
    log "TEST" "Executando type checking"
    set +e
    mypy_out=$(mypy src 2>&1); mypy_rc=$?
    set -e
    
    # Unit/Integration tests
    log "TEST" "Executando testes unitários/integração"
    set +e
    pytest_out=$(pytest -q --maxfail=1 --disable-warnings --cov=src --cov-report=term 2>&1); pytest_rc=$?
    set -e
    
    # Salvar outputs para análise
    echo "$ruff_out" > "logs/${TASK}.lint.out"
    echo "$mypy_out" > "logs/${TASK}.types.out"
    echo "$pytest_out" > "logs/${TASK}.tests.out"
    
    # Retornar códigos de saída
    echo "$ruff_rc $mypy_rc $pytest_rc"
}

# Função para gerar relatório QA
generate_qa_report() {
    log "REPORT" "Gerando relatório QA"
    
    python3 orchestrator/write_qa.py \
        --task "$TASK" \
        --lint_rc "$1" --lint_out "$(tail -n 50 logs/${TASK}.lint.out)" \
        --types_rc "$2" --types_out "$(tail -n 50 logs/${TASK}.types.out)" \
        --tests_rc "$3" --tests_out "$(tail -n 80 logs/${TASK}.tests.out)"
}

# Função para gate manual
manual_gate() {
    local qa_file="reports/qa.json"
    
    if [[ ! -f "$qa_file" ]]; then
        log "ERROR" "Relatório QA não encontrado"
        return 1
    fi
    
    # Ler status do QA
    local status=$(python3 -c "import json; print(json.load(open('$qa_file'))['status'])")
    
    if [[ "$status" == "pass" ]]; then
        log "GATE" "Status PASS - pronto para merge manual"
        echo "✅ Task $TASK passou em todos os critérios"
        echo "📋 Revisar reports/qa.json antes do merge"
        echo "🔒 Merge requer aprovação manual"
    else
        log "GATE" "Status FAIL - verificar next_actions"
        echo "❌ Task $TASK falhou - verificar reports/qa.json"
        echo "📋 Próximas ações:"
        python3 -c "import json; print('\n'.join(json.load(open('$qa_file'))['next_actions']))"
        return 1
    fi
}

# Main execution
main() {
    log "START" "Iniciando orquestração para task=$TASK"
    
    # Etapa 1: INIT
    validate_env
    
    # Etapa 2: PLAN
    log "PLAN" "Iniciando planejamento"
    run_with_timeout 120 "PLAN" gemini plan --in "$ISSUE" --out-json handoff/plan.json --out-spec handoff/spec.md
    
    # Validar plan.json gerado
    check_file "handoff/plan.json"
    check_file "handoff/spec.md"
    
    # Etapa 3: CODE
    log "CODE" "Iniciando geração de código"
    run_with_timeout 300 "CODE" codex code --plan handoff/plan.json --spec handoff/spec.md --out .
    
    # Etapa 4: INTEGRATE
    log "INTEGRATE" "Iniciando integração"
    apply_diff
    run_smoke_tests
    
    # Etapa 5: TEST
    log "TEST" "Iniciando testes canônicos"
    test_results=$(run_canonical_tests)
    read -r lint_rc types_rc tests_rc <<< "$test_results"
    
    # Etapa 6: REPORT
    generate_qa_report "$lint_rc" "$types_rc" "$tests_rc"
    
    # Etapa 7: GATE
    manual_gate
    
    log "END" "Orquestração concluída para task=$TASK"
}

# Executar main
main "$@"
