# Makefile para orquestrador "magro"
# Uso: make TASK=demo plan|code|integrate|test|report|all

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

.PHONY: help plan code integrate test report all clean validate

help:
	@echo "Orquestrador 'magro' - Comandos disponíveis:"
	@echo "  make TASK=<id> plan     - Gerar plano e especificação"
	@echo "  make TASK=<id> code     - Gerar código conforme plano"
	@echo "  make TASK=<id> integrate- Aplicar diffs e build local"
	@echo "  make TASK=<id> test     - Executar testes canônicos"
	@echo "  make TASK=<id> report   - Gerar relatório QA"
	@echo "  make TASK=<id> all      - Executar pipeline completo"
	@echo "  make clean             - Limpar artefatos temporários"
	@echo ""
	@echo "Exemplo: make TASK=demo all"

validate:
	@echo "Validando ambiente para task=$(TASK)..."
	@test -f issues/$(TASK).md || (echo "❌ Issue não encontrado: issues/$(TASK).md"; exit 1)
	@command -v gemini >/dev/null 2>&1 || (echo "❌ gemini CLI não encontrado"; exit 1)
	@command -v codex >/dev/null 2>&1 || (echo "❌ codex CLI não encontrado"; exit 1)
	@command -v cursor >/dev/null 2>&1 || (echo "❌ cursor CLI não encontrado"; exit 1)
	@echo "✅ Ambiente validado"

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

test: validate
	$(call log,TEST,Iniciando testes canônicos para task=$(TASK))
	@mkdir -p logs
	@echo "Executando linting..."
	@set +e; \
	ruff_out=$$(ruff check . 2>&1); \
	ruff_rc=$$?; \
	echo "$$ruff_out" > logs/$(TASK).lint.out; \
	set -e
	@echo "Executando type checking..."
	@set +e; \
	mypy_out=$$(mypy src 2>&1); \
	mypy_rc=$$?; \
	echo "$$mypy_out" > logs/$(TASK).types.out; \
	set -e
	@echo "Executando testes unitários/integração..."
	@set +e; \
	pytest_out=$$(pytest -q --maxfail=1 --disable-warnings --cov=src --cov-report=term 2>&1); \
	pytest_rc=$$?; \
	echo "$$pytest_out" > logs/$(TASK).tests.out; \
	set -e
	$(call log,TEST,Testes canônicos concluídos)

report: validate
	$(call log,REPORT,Gerando relatório QA para task=$(TASK))
	@mkdir -p reports
	@python3 orchestrator/write_qa.py \
		--task $(TASK) \
		--lint_rc $$(if [ -f logs/$(TASK).lint.out ]; then echo "$$(grep -q "error" logs/$(TASK).lint.out && echo "1" || echo "0")"; else echo "0"; fi) \
		--lint_out "$$(if [ -f logs/$(TASK).lint.out ]; then tail -n 50 logs/$(TASK).lint.out; fi)" \
		--types_rc $$(if [ -f logs/$(TASK).types.out ]; then echo "$$(grep -q "error" logs/$(TASK).types.out && echo "1" || echo "0")"; else echo "0"; fi) \
		--types_out "$$(if [ -f logs/$(TASK).types.out ]; then tail -n 50 logs/$(TASK).types.out; fi)" \
		--tests_rc $$(if [ -f logs/$(TASK).tests.out ]; then echo "$$(grep -q "FAILED" logs/$(TASK).tests.out && echo "1" || echo "0")"; else echo "0"; fi) \
		--tests_out "$$(if [ -f logs/$(TASK).tests.out ]; then tail -n 80 logs/$(TASK).tests.out; fi)"
	@if [ -f reports/qa.json ]; then \
		status=$$(python3 -c "import json; print(json.load(open('reports/qa.json'))['status'])"); \
		if [ "$$status" = "pass" ]; then \
			echo "✅ Task $(TASK) passou em todos os critérios"; \
			echo "📋 Revisar reports/qa.json antes do merge"; \
			echo "🔒 Merge requer aprovação manual"; \
		else \
			echo "❌ Task $(TASK) falhou - verificar reports/qa.json"; \
			echo "📋 Próximas ações:"; \
			python3 -c "import json; print('\n'.join(json.load(open('reports/qa.json'))['next_actions']))"; \
		fi; \
	fi
	$(call log,REPORT,Relatório QA concluído)

all: validate plan code integrate test report
	$(call log,END,Pipeline completo concluído para task=$(TASK))

clean:
	@echo "Limpando artefatos temporários..."
	@rm -rf handoff/plan.json handoff/spec.md
	@rm -rf reports/qa.json
	@rm -rf logs/$(TASK).*.log logs/$(TASK).*.out
	@rm -rf diffs/$(TASK).diff
	@echo "✅ Limpeza concluída"

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
		status=$$(python3 -c "import json; print(json.load(open('reports/qa.json'))['status'])"); \
		echo "Status final: $$status"; \
	fi
