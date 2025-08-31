# Makefile para orquestrador "magro" com Poetry
# Uso: make TASK=demo plan|code|integrate|test|report|all
# Todos os comandos Python usam Poetry para gerenciamento de dependências

TASK ?= demo
TIMEZONE = America/Sao_Paulo

# Configurações de timeout (em segundos)
PLANNER_TIMEOUT = 120
CODER_TIMEOUT = 300
TESTER_TIMEOUT = 600

# Configurações de limites
MAX_DIFF_LINES = 1000
MIN_COVERAGE = 70

# Função para timestamp
ts = $(shell TZ=$(TIMEZONE) date +"%Y-%m-%dT%H:%M:%S%z")

# Função para logging
log = @echo "[$(1)] $(ts) $(2)"

.PHONY: help plan code integrate test report docs docs-update docs-watch stop-docs-watch open-docs-panel dashboard-all all clean validate start-watcher stop-watcher git-automation ci-cd-automation rollback-automation

help:
	@echo "Orquestrador 'magro' - Comandos disponíveis:"
	@echo "  make TASK=<id> plan     - Gerar plano e especificação"
	@echo "  make TASK=<id> code     - Gerar código conforme plano"
	@echo "  make TASK=<id> integrate- Aplicar diffs e build local"
	@echo "  make TASK=<id> pipeline-test - Executar testes canônicos"
	@echo "  make TASK=<id> report   - Gerar relatório QA"
	@echo "  make docs               - Atualizar documentação via agente"
	@echo "  make docs-watch         - Iniciar watcher de documentação (qa.json)"
	@echo "  make stop-docs-watch    - Parar watcher de documentação"
	@echo "  make dashboard-all      - Iniciar WebSocket + HTTP do dashboard"
	@echo "  make open-docs-panel    - Abrir painel de documentação no navegador"
	@echo "  make TASK=<id> all      - Executar pipeline completo"
	@echo "  make clean             - Limpar artefatos temporários"
	@echo ""
	@echo "Automação Git/CI-CD:"
	@echo "  make TASK=<id> git-automation    - Executar automação git (commit/push/PR)"
	@echo "  make TASK=<id> ci-cd-automation  - Executar automação CI/CD (deploy staging)"
	@echo "  make TASK=<id> rollback-automation - Executar rollback automático"
	@echo ""
	@echo "Exemplo: make TASK=demo all"

validate:
	@./orchestrator/validate.sh

# Comandos Poetry para desenvolvimento
install:
	@echo "📦 Instalando dependências com Poetry..."
	@poetry install

test:
	@echo "🧪 Executando testes..."
	@poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	@echo "🔍 Executando linting..."
	@poetry run ruff check src/ tests/ dashboard/

type-check:
	@echo "🔬 Executando type checking..."
	@poetry run mypy src/

format:
	@echo "🎨 Formatando código..."
	@poetry run black src/ tests/ dashboard/
	@poetry run isort src/ tests/ dashboard/

dashboard:
	@echo "🎭 Iniciando dashboard..."
	@poetry run python dashboard/server.py

demo:
	@echo "🎪 Executando demo do dashboard..."
	@poetry run python dashboard/demo.py

shell:
	@echo "🐚 Abrindo shell Poetry..."
	@poetry shell

clean-poetry:
	@echo "🧹 Limpando cache Poetry..."
	@poetry cache clear --all pypi
	@rm -rf dist/ build/ *.egg-info/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

plan: validate
	$(call log,PLAN,Iniciando planejamento para task=$(TASK))
	@mkdir -p handoff logs
	@timeout $(PLANNER_TIMEOUT) gemini plan \
		--in issues/$(TASK).md \
		--out-json handoff/plan.json \
		--out-spec handoff/spec.md
	@test -f handoff/plan.json || (echo "❌ Plano não gerado"; exit 1)
	@test -f handoff/spec.md || (echo "❌ Especificação não gerada"; exit 1)
	$(call log,PLAN,Planejamento concluído)

code: validate
	$(call log,CODE,Iniciando geração de código para task=$(TASK))
	@test -f handoff/plan.json || (echo "❌ Plano não encontrado - execute 'make plan' primeiro"; exit 1)
	@test -f handoff/spec.md || (echo "❌ Especificação não encontrada - execute 'make plan' primeiro"; exit 1)
	@mkdir -p diffs
	@timeout $(CODER_TIMEOUT) codex code \
		--plan handoff/plan.json \
		--spec handoff/spec.md \
		--out .
	$(call log,CODE,Geração de código concluída)

integrate: validate
	$(call log,INTEGRATE,Iniciando integração para task=$(TASK))
	@if [ -f diffs/$(TASK).diff ]; then \
		echo "Aplicando diff: diffs/$(TASK).diff"; \
		diff_size=$$(wc -l < diffs/$(TASK).diff); \
		if [ $$diff_size -gt $(MAX_DIFF_LINES) ]; then \
			echo "❌ Diff muito grande: $$diff_size linhas (limite: $(MAX_DIFF_LINES))"; \
			exit 1; \
		fi; \
		cursor apply --from-diff diffs/$(TASK).diff; \
	fi
	@echo "Executando build local..."
	@cursor run "pip install -e ." || echo "⚠️  Build local falhou - continuando"
	@echo "Executando testes de fumaça..."
	@cursor run "pytest -q tests/smoke || true"
	$(call log,INTEGRATE,Integração concluída)

pipeline-test: validate
	$(call log,TEST,Iniciando testes canônicos para task=$(TASK))
	@mkdir -p logs
	@echo "Executando linting..."
	@set +e; \
	ruff_out=$$(poetry run ruff check . 2>&1); \
	ruff_rc=$$?; \
	echo "$$ruff_out" > logs/$(TASK).lint.out; \
	set -e
	@echo "Executando type checking..."
	@set +e; \
	mypy_out=$$(poetry run mypy src 2>&1); \
	mypy_rc=$$?; \
	echo "$$mypy_out" > logs/$(TASK).types.out; \
	set -e
	@echo "Executando testes unitários/integração..."
	@set +e; \
	pytest_out=$$(poetry run pytest -q --maxfail=1 --disable-warnings --cov=src --cov-report=term 2>&1); \
	pytest_rc=$$?; \
	echo "$$pytest_out" > logs/$(TASK).tests.out; \
	set -e
	$(call log,TEST,Testes canônicos concluídos)

report: validate
	$(call log,REPORT,Gerando relatório QA para task=$(TASK))
	@mkdir -p reports
	@poetry run python orchestrator/write_qa.py \
		--task $(TASK) \
		--lint_rc $$(if [ -f logs/$(TASK).lint.out ]; then echo "$$(grep -q "error" logs/$(TASK).lint.out && echo "1" || echo "0")"; else echo "0"; fi) \
		--lint_out "$$(if [ -f logs/$(TASK).lint.out ]; then tail -n 50 logs/$(TASK).lint.out; fi)" \
		--types_rc $$(if [ -f logs/$(TASK).types.out ]; then echo "$$(grep -q "error" logs/$(TASK).types.out && echo "1" || echo "0")"; else echo "0"; fi) \
		--types_out "$$(if [ -f logs/$(TASK).types.out ]; then tail -n 50 logs/$(TASK).types.out; fi)" \
		--tests_rc $$(if [ -f logs/$(TASK).tests.out ]; then echo "$$(grep -q "FAILED" logs/$(TASK).tests.out && echo "1" || echo "0")"; else echo "0"; fi) \
		--tests_out "$$(if [ -f logs/$(TASK).tests.out ]; then tail -n 80 logs/$(TASK).tests.out; fi)"
	@if [ -f reports/qa.json ]; then \
		status=$$(poetry run python -c "import json; print(json.load(open('reports/qa.json'))['status'])"); \
		if [ "$$status" = "pass" ]; then \
			echo "✅ Task $(TASK) passou em todos os critérios"; \
			echo "📋 Revisar reports/qa.json antes do merge"; \
			echo "🔒 Merge requer aprovação manual"; \
		else \
			echo "❌ Task $(TASK) falhou - verificar reports/qa.json"; \
			echo "📋 Próximas ações:"; \
			poetry run python -c "import json; print('\n'.join(json.load(open('reports/qa.json'))['next_actions']))"; \
		fi; \
	fi
	$(call log,REPORT,Relatório QA concluído)

docs docs-update:
	$(call log,DOCS,Atualizando documentação com Documentation Agent)
	@mkdir -p docs/templates
	@if command -v poetry >/dev/null 2>&1; then \
		poetry run python -m src.maestro.documentation_agent -v || true; \
	else \
		python3 -m src.maestro.documentation_agent -v || true; \
	fi
	$(call log,DOCS,Documentação atualizada)

all: validate plan code integrate pipeline-test report docs
	$(call log,END,Pipeline completo concluído para task=$(TASK))

clean:
	@echo "Limpando artefatos temporários..."
	@rm -rf handoff/plan.json handoff/spec.md
	@rm -rf reports/qa.json
	@rm -rf logs/$(TASK).*.log logs/$(TASK).*.out
	@rm -rf diffs/$(TASK).diff
	@echo "✅ Limpeza concluída"

# Comandos para o watcher
start-watcher:
	@echo "🚀 Starting issue watcher in the background..."
	@mkdir -p logs
	@nohup ./orchestrator/watcher.sh > logs/watcher.log 2>&1 & echo $! > .watcher.pid
	@echo "✅ Watcher started with PID $(cat .watcher.pid). Log: logs/watcher.log"

stop-watcher:
	@echo "🛑 Stopping issue watcher..."
	@if [ -f .watcher.pid ]; then \
		kill $(cat .watcher.pid); \
		rm .watcher.pid; \
		echo "✅ Watcher stopped."; \
	else \
		echo "⚠️ Watcher PID file not found. Was it running?"; \
	fi

docs-watch:
	@echo "📝 Starting documentation watcher in the background..."
	@mkdir -p logs
	@nohup ./orchestrator/documentation_watcher.sh > logs/docs_watcher.log 2>&1 & echo $! > .docs_watcher.pid
	@echo "✅ Docs watcher started with PID $(cat .docs_watcher.pid). Log: logs/docs_watcher.log"

stop-docs-watch:
	@echo "🛑 Stopping documentation watcher..."
	@if [ -f .docs_watcher.pid ]; then \
		kill $(cat .docs_watcher.pid); \
		rm .docs_watcher.pid; \
		echo "✅ Docs watcher stopped."; \
	else \
		echo "⚠️ Docs watcher PID file not found. Was it running?"; \
	fi

dashboard-all:
	@echo "🎭 Starting full dashboard (WebSocket + HTTP) ..."
	@./dashboard/start_dashboard.sh

open-docs-panel:
	@echo "🌐 Opening documentation panel..."
	@url="http://localhost:$${DASHBOARD_HTTP_PORT:-8080}/documentation_panel.html"; \
	if command -v open >/dev/null 2>&1; then open "$$url"; \
	elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$$url"; \
	else echo "Open this URL in your browser: $$url"; fi


# Comando para criar issue de exemplo
create-demo:
	@echo "Criando issue de exemplo..."
	@cp issues/TEMPLATE.md issues/demo.md
	@sed -i '' 's/<resuma em 1 linha>/Gerar README.md com documentação do projeto/' issues/demo.md
	@sed -i '' 's/<bullet 1>/Projeto precisa de documentação clara/' issues/demo.md
	@sed -i '' 's/<bullet 2>/README atual está desatualizado/' issues/demo.md
	@sed -i '' 's/<resultado esperado em termos observáveis>/README.md com seções: descrição, instalação, uso, contribuição/' issues/demo.md
	@sed -i '' 's/- <itens>/- README.md principal/' issues/demo.md
	@sed -i '' 's/- <itens>/- Documentação técnica detalhada/' issues/demo.md
	@sed -i '' 's/- <arquivo ou pasta e propósito>/- README.md: documentação principal do projeto/' issues/demo.md
	@sed -i '' 's/- \[ \] <teste verificável 1>/- [ ] README.md existe e é legível/' issues/demo.md
	@sed -i '' 's/- \[ \] <teste verificável 2>/- [ ] README.md contém seções obrigatórias/' issues/demo.md
	@sed -i '' 's/- <risco e mitigação>/- Baixo risco: documentação simples/' issues/demo.md
	@sed -i '' 's/Planner=<seg>, Coder=<seg>, Tester=<seg>/Planner=30, Coder=60, Tester=30/' issues/demo.md
	@sed -i '' 's/<linhas>/50/' issues/demo.md
	@sed -i '' 's/<glob patterns>/README.md/' issues/demo.md
	@echo "✅ Issue demo criado: issues/demo.md"

# Comando para mostrar status
status:
	@echo "📊 Status do orquestrador:"
	@echo "Task atual: $(TASK)"
	@echo "Issue: $$(if [ -f issues/$(TASK).md ]; then echo "✅"; else echo "❌"; fi)"
	@echo "Plano: $$(if [ -f handoff/plan.json ]; then echo "✅"; else echo "❌"; fi)"
	@echo "Especificação: $$(if [ -f handoff/spec.md ]; then echo "✅"; else echo "❌"; fi)"
	@echo "Relatório QA: $$(if [ -f reports/qa.json ]; then echo "✅"; else echo "❌"; fi)"
	@if [ -f reports/qa.json ]; then \
		status=$$(poetry run python -c "import json; print(json.load(open('reports/qa.json'))['status'])"); \
		echo "Status final: $$status"; \
	fi
	@echo "Git Agent: $$(if [ -f src/maestro/git_agent.py ]; then echo "✅"; else echo "❌"; fi)"
	@echo "CI/CD Agent: $$(if [ -f src/maestro/ci_cd_agent.py ]; then echo "✅"; else echo "❌"; fi)"
	@echo "Config Git: $$(if [ -f config/git-automation.json ]; then echo "✅"; else echo "❌"; fi)"

# Comandos para automação Git/CI-CD
git-automation:
	$(call log,GIT_AUTO,Executando automação git para task=$(TASK))
	@test -f src/maestro/git_agent.py || (echo "❌ Git Agent não encontrado"; exit 1)
	@test -f config/git-automation.json || (echo "❌ Configuração git não encontrada"; exit 1)
	@poetry run python src/maestro/git_agent.py $(TASK)
	$(call log,GIT_AUTO,Automação git concluída)

ci-cd-automation:
	$(call log,CI_CD,Executando automação CI/CD para task=$(TASK))
	@test -f src/maestro/ci_cd_agent.py || (echo "❌ CI/CD Agent não encontrado"; exit 1)
	@test -f config/git-automation.json || (echo "❌ Configuração git não encontrada"; exit 1)
	@poetry run python src/maestro/ci_cd_agent.py deploy-staging $(TASK)
	$(call log,CI_CD,Automação CI/CD concluída)

rollback-automation:
	$(call log,ROLLBACK,Executando rollback automático para task=$(TASK))
	@test -f src/maestro/git_agent.py || (echo "❌ Git Agent não encontrado"; exit 1)
	@test -f src/maestro/ci_cd_agent.py || (echo "❌ CI/CD Agent não encontrado"; exit 1)
	@poetry run python -c "from src.maestro.git_agent import GitAgent; agent = GitAgent(); agent.rollback_changes('$(TASK)')"
	@poetry run python src/maestro/ci_cd_agent.py rollback $(TASK)
	$(call log,ROLLBACK,Rollback automático concluído)
