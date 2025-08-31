#!/usr/bin/env bash
set -euo pipefail

# Enhanced orchestrator with dashboard integration
# This script runs the orchestrator and sends real-time updates to the dashboard

TASK="${1:?use: orchestrate_with_dashboard.sh <task_id>}"
ISSUE="issues/${TASK}.md"
TIMEZONE="America/Sao_Paulo"
DASHBOARD_URL="${DASHBOARD_URL:-ws://localhost:8765}"

# Function for timestamps
ts() { 
    TZ=$TIMEZONE date +"%Y-%m-%dT%H:%M:%S%z"
}

# Function for logging
log() {
    echo "[$1] $(ts) $2" | tee -a "logs/${TASK}.${1,,}.log"
}

# Function to send dashboard update
send_dashboard_update() {
    local stage="$1"
    local status="$2"
    local progress="${3:-}"
    local error="${4:-}"
    
    # Send update via Python script if dashboard is available
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import asyncio
import json
import websockets
import sys

async def send_update():
    try:
        async with websockets.connect('$DASHBOARD_URL') as websocket:
            message = {
                'type': 'stage_update',
                'stage': '$stage',
                'status': '$status',
                'progress': '$progress',
                'error': '$error',
                'task': '$TASK'
            }
            await websocket.send(json.dumps(message))
    except Exception as e:
        pass  # Fail silently if dashboard is not available

asyncio.run(send_update())
" 2>/dev/null || true
    fi
}

# Function to check if dashboard is available
check_dashboard() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import asyncio
import websockets

async def check():
    try:
        async with websockets.connect('$DASHBOARD_URL', timeout=2) as websocket:
            return True
    except:
        return False

result = asyncio.run(check())
print('available' if result else 'unavailable')
" 2>/dev/null || echo "unavailable"
}

# Function to validate environment
validate_env() {
    log "INIT" "Validando ambiente para task=$TASK"
    
    # Check if issue exists
    if [[ ! -f "$ISSUE" ]]; then
        log "ERROR" "Issue não encontrado: $ISSUE"
        exit 1
    fi
    
    # Check if CLIs are available
    command -v gemini >/dev/null 2>&1 || { log "ERROR" "gemini CLI não encontrado"; exit 1; }
    command -v codex >/dev/null 2>&1 || { log "ERROR" "codex CLI não encontrado"; exit 1; }
    command -v cursor >/dev/null 2>&1 || { log "ERROR" "cursor CLI não encontrado"; exit 1; }
    
    # Check dashboard availability
    if [[ "$(check_dashboard)" == "available" ]]; then
        log "INIT" "Dashboard disponível em $DASHBOARD_URL"
        DASHBOARD_AVAILABLE=true
    else
        log "WARN" "Dashboard não disponível - continuando sem integração"
        DASHBOARD_AVAILABLE=false
    fi
    
    log "INIT" "Ambiente validado com sucesso"
}

# Function to run with timeout and dashboard updates
run_stage_with_dashboard() {
    local stage="$1"
    local command="$2"
    local timeout="${3:-300}"
    
    log "$stage" "Iniciando etapa $stage para task=$TASK"
    
    # Send dashboard update - stage starting
    if [[ "$DASHBOARD_AVAILABLE" == "true" ]]; then
        send_dashboard_update "$stage" "running" "0%"
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Run the command with timeout
    local start_time=$(date +%s)
    local exit_code=0
    
    if timeout "$timeout" bash -c "$command" > "logs/${TASK}.${stage}.out" 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Send dashboard update based on result
    if [[ "$DASHBOARD_AVAILABLE" == "true" ]]; then
        if [[ $exit_code -eq 0 ]]; then
            send_dashboard_update "$stage" "completed" "100%"
        else
            local error_msg="Stage failed with exit code $exit_code"
            send_dashboard_update "$stage" "failed" "" "$error_msg"
        fi
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log "$stage" "Etapa $stage concluída em ${duration}s"
    else
        log "ERROR" "Etapa $stage falhou com código $exit_code"
        if [[ -f "logs/${TASK}.${stage}.out" ]]; then
            log "ERROR" "Output da etapa $stage:"
            cat "logs/${TASK}.${stage}.out" | head -20 | while read -r line; do
                log "ERROR" "  $line"
            done
        fi
        exit $exit_code
    fi
}

# Function to send pipeline start notification
notify_pipeline_start() {
    if [[ "$DASHBOARD_AVAILABLE" == "true" ]]; then
        python3 -c "
import asyncio
import json
import websockets

async def notify():
    try:
        async with websockets.connect('$DASHBOARD_URL') as websocket:
            message = {
                'type': 'pipeline_start',
                'task': '$TASK',
                'timestamp': '$(ts)'
            }
            await websocket.send(json.dumps(message))
    except:
        pass

asyncio.run(notify())
" 2>/dev/null || true
    fi
}

# Function to send pipeline completion notification
notify_pipeline_complete() {
    local success="$1"
    
    if [[ "$DASHBOARD_AVAILABLE" == "true" ]]; then
        python3 -c "
import asyncio
import json
import websockets

async def notify():
    try:
        async with websockets.connect('$DASHBOARD_URL') as websocket:
            message = {
                'type': 'pipeline_complete',
                'task': '$TASK',
                'success': '$success',
                'timestamp': '$(ts)'
            }
            await websocket.send(json.dumps(message))
    except:
        pass

asyncio.run(notify())
" 2>/dev/null || true
    fi
}

# Main execution
main() {
    log "START" "Iniciando orquestrador com dashboard para task=$TASK"
    
    # Validate environment
    validate_env
    
    # Notify pipeline start
    notify_pipeline_start
    
    # Stage 1: Planning
    run_stage_with_dashboard "planner" "
        gemini plan \
            --in '$ISSUE' \
            --out-json handoff/plan.json \
            --out-spec handoff/spec.md
    " 120
    
    # Validate planning outputs
    if [[ ! -f "handoff/plan.json" ]] || [[ ! -f "handoff/spec.md" ]]; then
        log "ERROR" "Planejamento não gerou arquivos esperados"
        exit 1
    fi
    
    # Stage 2: Code Generation
    run_stage_with_dashboard "coder" "
        codex code \
            --plan handoff/plan.json \
            --spec handoff/spec.md \
            --out .
    " 300
    
    # Stage 3: Integration
    run_stage_with_dashboard "integrator" "
        if [[ -f 'diffs/${TASK}.diff' ]]; then
            echo 'Aplicando diff: diffs/${TASK}.diff'
            cursor apply --from-diff 'diffs/${TASK}.diff'
        fi
        echo 'Executando build local...'
        cursor run 'pip install -e .' || echo 'Build local falhou - continuando'
        echo 'Executando testes de fumaça...'
        cursor run 'pytest -q tests/smoke || true'
    " 180
    
    # Stage 4: Testing
    run_stage_with_dashboard "tester" "
        echo 'Executando linting...'
        ruff check . > logs/${TASK}.lint.out 2>&1 || true
        echo 'Executando type checking...'
        mypy src > logs/${TASK}.types.out 2>&1 || true
        echo 'Executando testes unitários/integração...'
        pytest -q --maxfail=1 --disable-warnings --cov=src --cov-report=term > logs/${TASK}.tests.out 2>&1 || true
    " 600
    
    # Stage 5: Reporting
    run_stage_with_dashboard "reporter" "
        python3 orchestrator/write_qa.py \
            --task '$TASK' \
            --lint_rc \$(if [[ -f logs/${TASK}.lint.out ]]; then grep -q 'error' logs/${TASK}.lint.out && echo '1' || echo '0'; else echo '0'; fi) \
            --lint_out \"\$(if [[ -f logs/${TASK}.lint.out ]]; then tail -n 50 logs/${TASK}.lint.out; fi)\" \
            --types_rc \$(if [[ -f logs/${TASK}.types.out ]]; then grep -q 'error' logs/${TASK}.types.out && echo '1' || echo '0'; else echo '0'; fi) \
            --types_out \"\$(if [[ -f logs/${TASK}.types.out ]]; then tail -n 50 logs/${TASK}.types.out; fi)\" \
            --tests_rc \$(if [[ -f logs/${TASK}.tests.out ]]; then grep -q 'FAILED' logs/${TASK}.tests.out && echo '1' || echo '0'; else echo '0'; fi) \
            --tests_out \"\$(if [[ -f logs/${TASK}.tests.out ]]; then tail -n 80 logs/${TASK}.tests.out; fi)\"
    " 60

    # Stage 6: Documentation Update
    run_stage_with_dashboard "docs" "
        if command -v poetry >/dev/null 2>&1; then \
            DASHBOARD_URL='$DASHBOARD_URL' poetry run python -m src.maestro.documentation_agent -v; \
        else \
            DASHBOARD_URL='$DASHBOARD_URL' python3 -m src.maestro.documentation_agent -v; \
        fi
    " 60
    
    # Check final status
    if [[ -f "reports/qa.json" ]]; then
        local status=$(python3 -c "import json; print(json.load(open('reports/qa.json'))['status'])" 2>/dev/null || echo "unknown")
        
        if [[ "$status" == "pass" ]]; then
            log "SUCCESS" "Task $TASK passou em todos os critérios"
            notify_pipeline_complete "true"
        else
            log "WARN" "Task $TASK falhou - verificar reports/qa.json"
            notify_pipeline_complete "false"
        fi
    else
        log "ERROR" "Relatório QA não foi gerado"
        notify_pipeline_complete "false"
        exit 1
    fi
    
    log "END" "Orquestrador concluído para task=$TASK"
}

# Run main function
main "$@"
