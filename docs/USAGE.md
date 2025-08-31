# Guia de Uso do Orquestrador "Magro"

## 🚀 Primeiros Passos

### 1. Configuração Inicial

```bash
# Clone o repositório
git clone <repository-url>
cd Maestro

# Instale o Poetry (se não tiver)
curl -sSL https://install.python-poetry.org | python3 -

# Instale as dependências Python
poetry install

# Configure as CLIs (substitua pelos comandos reais)
# brew install gemini-cli
# brew install codex-cli  
# brew install cursor-cli

# Configure secrets
cp secrets/env.example secrets/.env
# Edite secrets/.env com suas chaves

# Configure permissões
chmod +x orchestrator/orchestrate.sh
chmod +x orchestrator/write_qa.py
chmod +x scripts/dev.sh
```

### 2. Teste Inicial

```bash
# Execute o teste de fumaça
poetry run pytest tests/smoke

# Verifique o status
make status
```

## 📝 Criando uma Nova Task

### 1. Usando o Template

```bash
# Copie o template
cp issues/TEMPLATE.md issues/minha-feature.md

# Edite o issue
vim issues/minha-feature.md
```

### 2. Exemplo de Issue Completo

```markdown
# Implementar autenticação JWT

## Contexto
- Sistema precisa de autenticação segura
- Usuários precisam fazer login/logout
- API deve validar tokens JWT

## Objetivo
Sistema de autenticação JWT funcional com login, logout e validação de tokens

## Escopo incluído
- Endpoint POST /auth/login
- Endpoint POST /auth/logout
- Middleware de validação JWT
- Testes unitários

## Escopo excluído
- Refresh tokens
- OAuth integration
- Password reset

## Entregáveis esperados
- src/auth/jwt.py: implementação JWT
- src/middleware/auth.py: middleware de validação
- tests/test_auth.py: testes unitários
- docs/auth.md: documentação da API

## Critérios de aceitação
- [ ] Login retorna token JWT válido
- [ ] Logout invalida token
- [ ] Middleware bloqueia requests sem token
- [ ] Testes passam com cobertura >70%

## Riscos
- Segurança: usar biblioteca JWT confiável
- Performance: cache de tokens inválidos

## Limites
- Tempo máx etapa: Planner=120, Coder=300, Tester=600
- Diff máx: 1000 linhas
- Paths permitidos: src/auth/**, tests/test_auth.py, docs/auth.md

## Referências
- https://pyjwt.readthedocs.io/
- https://jwt.io/
```

## 🔄 Executando o Pipeline

### Comando Único (Recomendado)

```bash
# Execute o pipeline completo
./orchestrator/orchestrate.sh minha-feature

# Ou usando Makefile
make TASK=minha-feature all
```

### Etapas Individuais

```bash
# 1. Planejamento
make TASK=minha-feature plan

# Verifique o plano gerado
cat handoff/plan.json
cat handoff/spec.md

# 2. Geração de código
make TASK=minha-feature code

# 3. Integração
make TASK=minha-feature integrate

# 4. Testes canônicos
make TASK=minha-feature pipeline-test

# 5. Relatório
make TASK=minha-feature report
```

## 📊 Monitoramento e Debug

### Verificar Status

```bash
# Status geral
make status

# Status de uma task específica
make TASK=minha-feature status
```

### Analisar Logs

```bash
# Logs de planejamento
cat logs/minha-feature.plan.log

# Output de linting
cat logs/minha-feature.lint.out

# Output de type checking
cat logs/minha-feature.types.out

# Output de testes
cat logs/minha-feature.tests.out
```

### Relatório QA

```bash
# Ver relatório completo
cat reports/qa.json

# Status apenas
poetry run python -c "import json; print(json.load(open('reports/qa.json'))['status'])"

# Próximas ações
poetry run python -c "import json; print('\n'.join(json.load(open('reports/qa.json'))['next_actions']))"
```

## 🎭 Dashboard

### Iniciar Dashboard

```bash
# Iniciar servidor do dashboard
make dashboard

# Ou diretamente
poetry run python dashboard/server.py
```

### Executar Demo

```bash
# Executar demo do dashboard
make demo

# Ou diretamente
poetry run python dashboard/demo.py
```

### Acessar Dashboard

O dashboard estará disponível em `http://localhost:8000` após iniciar o servidor.

## 🛠️ Comandos Úteis

### Desenvolvimento com Poetry

```bash
# Instalar dependências
make install

# Executar testes
make test

# Executar linting
make lint

# Executar type checking
make type-check

# Formatar código
make format

# Abrir shell Poetry
make shell

# Limpar cache Poetry
make clean-poetry
```

### Limpeza

```bash
# Limpar artefatos de uma task
make TASK=minha-feature clean

# Limpar tudo
make clean
```

### Criação Rápida

```bash
# Criar issue de exemplo
make create-demo

# Executar demo
make TASK=demo all
```

### Debug

```bash
# Ver configuração
cat orchestrator/config.json

# Ver templates
cat handoff/plan.template.json
cat reports/qa.template.json

# Validar configuração
make validate
```

## 🔧 Configuração Avançada

### Ajustar Timeouts

Edite `orchestrator/config.json`:

```json
{
  "timeouts": {
    "planner": 120,    // 2 minutos
    "coder": 300,      // 5 minutos
    "tester": 600,     // 10 minutos
    "integrator": 180  // 3 minutos
  }
}
```

### Ajustar Limites

```json
{
  "limits": {
    "max_diff_lines": 1000,
    "max_files_touched": 50,
    "min_coverage": 70,
    "max_lint_errors": 0,
    "max_type_errors": 0
  }
}
```

### Configurar CLIs

```json
{
  "clis": {
    "planner": {
      "command": "gemini",
      "args": [
        "plan",
        "--in",
        "{issue}",
        "--out-json",
        "{plan}",
        "--out-spec",
        "{spec}"
      ]
    },
    "coder": {
      "command": "codex",
      "args": [
        "code",
        "--plan",
        "{plan}",
        "--spec",
        "{spec}",
        "--out",
        "."
      ]
    },
    "integrator": {
      "command": "cursor",
      "args": [
        "apply",
        "--from-diff",
        "{diff}"
      ]
    }
  }
}
```

### Configurar Testes

```json
{
  "testing": {
    "lint_command": "ruff check .",
    "type_check_command": "mypy src",
    "test_command": "pytest -q --maxfail=1 --disable-warnings --cov=src --cov-report=term",
    "smoke_test_command": "pytest -q tests/smoke"
  }
}
```

## 🚨 Troubleshooting

### Erro: "CLI não encontrado"

```bash
# Verificar se CLIs estão no PATH
which gemini
which codex
which cursor

# Instalar CLIs faltantes
# brew install gemini-cli
```

### Erro: "Issue não encontrado"

```bash
# Verificar se issue existe
ls issues/

# Criar issue se necessário
cp issues/TEMPLATE.md issues/minha-task.md
```

### Erro: "Timeout"

```bash
# Aumentar timeout no config
vim orchestrator/config.json

# Ou usar Makefile com timeout maior
timeout 600 make TASK=minha-task plan
```

### Erro: "Diff muito grande"

```bash
# Verificar tamanho do diff
wc -l diffs/minha-task.diff

# Quebrar task em partes menores
# Ou aumentar limite no config
```

### Erro: "Poetry não encontrado"

```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Verificar instalação
poetry --version
```

### Erro: "Dependências não instaladas"

```bash
# Instalar dependências
poetry install

# Verificar dependências
poetry show
```

## 📈 Métricas e KPIs

### Coletar Métricas

```bash
# Tempo por etapa
grep "elapsed" logs/*.log

# Cobertura de testes
grep "TOTAL" logs/*.tests.out

# Erros de lint
grep "error" logs/*.lint.out

# Erros de type checking
grep "error" logs/*.types.out
```

### Relatório de Performance

```bash
# Gerar relatório simples
echo "=== Relatório de Performance ==="
echo "Task: $(ls issues/ | grep -v TEMPLATE)"
echo "Status: $(poetry run python -c "import json; print(json.load(open('reports/qa.json'))['status'])" 2>/dev/null || echo 'N/A')"
echo "Tempo total: $(poetry run python -c "import json; print(json.load(open('reports/qa.json'))['elapsed_sec'])" 2>/dev/null || echo 'N/A')s"
```

## 🔄 Workflow Completo

### 1. Desenvolvimento

```bash
# Criar issue
cp issues/TEMPLATE.md issues/feature-123.md
vim issues/feature-123.md

# Executar pipeline
./orchestrator/orchestrate.sh feature-123

# Verificar resultado
make TASK=feature-123 status
```

### 2. Revisão

```bash
# Analisar plano
cat handoff/plan.json

# Analisar especificação
cat handoff/spec.md

# Verificar testes
cat logs/feature-123.tests.out

# Verificar linting
cat logs/feature-123.lint.out

# Verificar type checking
cat logs/feature-123.types.out
```

### 3. Aprovação

```bash
# Verificar critérios de gate
cat reports/qa.json | jq '.status'

# Se pass, aprovar manualmente
echo "Aprovado por $(whoami) em $(date)" > logs/approval_feature-123.txt
```

### 4. Merge

```bash
# Aplicar mudanças
git add .
git commit -m "Feature 123: implementação via orquestrador"
git push origin feature-123
```

## 🎯 Boas Práticas

### Issues Bem Escritos

- ✅ Objetivo claro e mensurável
- ✅ Escopo bem definido (incluído/excluído)
- ✅ Critérios de aceitação verificáveis
- ✅ Limites realistas
- ❌ Objetivo vago ("melhorar performance")
- ❌ Escopo muito amplo
- ❌ Critérios subjetivos

### Configuração Segura

- ✅ Nunca commitar `.env`
- ✅ Usar `secrets/env.example`
- ✅ Sanitizar logs
- ❌ Hardcoded secrets
- ❌ Logs com informações sensíveis

### Monitoramento

- ✅ Verificar logs após cada etapa
- ✅ Analisar relatório QA
- ✅ Acompanhar métricas de performance
- ✅ Verificar linting e type checking
- ❌ Ignorar warnings
- ❌ Não verificar next_actions

### Desenvolvimento com Poetry

- ✅ Usar `poetry run` para comandos Python
- ✅ Usar `poetry install` para dependências
- ✅ Usar `poetry shell` para desenvolvimento
- ✅ Commitar `poetry.lock` para reproduzibilidade
- ❌ Instalar dependências globalmente
- ❌ Usar `pip` diretamente

## 🧪 Estratégia de Testes

### Testes Unitários

```bash
# Executar testes unitários
poetry run pytest tests/unit/

# Com cobertura
poetry run pytest --cov=src --cov-report=html
```

### Testes de Fumaça

```bash
# Executar testes de fumaça
poetry run pytest tests/smoke/
```

### Linting e Type Checking

```bash
# Linting com Ruff
poetry run ruff check src/ tests/

# Type checking com MyPy
poetry run mypy src/
```

### Formatação

```bash
# Formatar com Black
poetry run black src/ tests/

# Organizar imports com isort
poetry run isort src/ tests/
```

## 📋 Checklist de Configuração

- [ ] Poetry instalado e configurado
- [ ] Dependências instaladas (`poetry install`)
- [ ] CLIs configuradas (gemini, codex, cursor)
- [ ] Secrets configurados (`secrets/.env`)
- [ ] Permissões configuradas
- [ ] Teste inicial executado
- [ ] Dashboard funcionando
- [ ] Makefile funcionando
- [ ] Configuração validada (`make validate`)

## 🔗 Recursos Adicionais

- **Documentação do Poetry**: https://python-poetry.org/docs/
- **Ruff (Linter)**: https://docs.astral.sh/ruff/
- **MyPy (Type Checker)**: https://mypy.readthedocs.io/
- **Pytest**: https://docs.pytest.org/
- **Dashboard**: `http://localhost:8000` (após `make dashboard`)

<!-- BEGIN AUTO-DOC: DocumentationAgent -->

## 📚 Documentation Status 🔴

- Task: `demo`
- Status: `fail`
- Tests: `16` passed, `0` failed
- Coverage: `41.0%`
- Lint errors: `1` | Type errors: `10`
- Last updated: `2025-08-31T05:12:58.812066Z`

### Next Actions
- Corrigir erros de linting
- Corrigir erros de type checking
- Corrigir testes falhando

### Objetivo (Spec)
Sistema de documentação automática que atualiza README.md, USER_MANUAL.md e USAGE.md baseado nas mudanças de código e relatórios QA gerados pelo pipeline

### Escopo incluído (Spec)
- Agente de documentação que analisa reports/qa.json
- Atualização automática de README.md com novas features
- Atualização automática de USER_MANUAL.md com novos comandos/configurações
- Atualização automática de USAGE.md com novos exemplos
- Integração com watcher.sh para disparo automático
- Dashboard com seção de documentação em tempo real
- Templates de documentação baseados em plan.json e spec.md

### Escopo excluído (Spec)
- Documentação de APIs externas
- Geração de diagramas complexos
- Tradução automática de documentação
- Versionamento de documentação histórica

### Critérios de aceitação (Spec)
- [ ] Agente detecta mudanças em reports/qa.json automaticamente
- [ ] README.md é atualizado com novas features implementadas
- [ ] USER_MANUAL.md é atualizado com novos comandos/configurações
- [ ] USAGE.md é atualizado com novos exemplos de uso
- [ ] Dashboard mostra status de documentação em tempo real
- [ ] Watcher dispara atualização de documentação quando pipeline completa
- [ ] Templates mantêm formatação e estrutura consistente
- [ ] Testes validam geração correta de documentação
- [ ] Sistema funciona com múltiplas tasks simultâneas

### Plano (Steps)
- setup_structure: Criar a estrutura de diretórios e arquivos vazios para a nova funcionalidade de documentação automática.
- create_templates: Copiar conteúdo existente dos arquivos de documentação para os novos templates para servir como base.
- implement_documentation_agent: Implementar o agente de documentação em `src/maestro/documentation_agent.py`. O agente será responsável por ler os relatórios de QA, processar os dados e atualizar os arquivos de documentação usando os templates.
- implement_agent_tests: Implementar testes unitários para o `documentation_agent` em `tests/test_documentation_agent.py` para garantir que a geração da documentação funcione corretamente.
- implement_watcher: Criar o script `orchestrator/documentation_watcher.sh` que monitora mudanças em `reports/qa.json` e dispara o `documentation_agent.py`.
- integrate_watcher: Integrar o novo `documentation_watcher.sh` com o `watcher.sh` principal para que ele seja executado como parte do pipeline de orquestração.
- implement_dashboard_panel: Desenvolver o painel de documentação `dashboard/documentation_panel.html` que exibirá o status da documentação em tempo real.
- integrate_dashboard: Integrar o `documentation_panel.html` ao dashboard principal, atualizando o `server.py` ou `dashboard.py` para incluir os dados e o novo painel.
- verify_and_review: Revisar toda a implementação, executar os testes e garantir que todos os critérios de aceitação foram atendidos.

<!-- END AUTO-DOC -->
