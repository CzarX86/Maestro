# Guia de Uso do Orquestrador "Magro"

## 🚀 Primeiros Passos

### 1. Configuração Inicial

```bash
# Clone o repositório
git clone <repository-url>
cd Maestro

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
```

### 2. Teste Inicial

```bash
# Execute o teste de fumaça
python3 tests/smoke/test_orchestrator.py

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
- [ ] Testes passam com cobertura >80%

## Riscos
- Segurança: usar biblioteca JWT confiável
- Performance: cache de tokens inválidos

## Limites
- Tempo máx etapa: Planner=60, Coder=180, Tester=120
- Diff máx: 200
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

# 4. Testes
make TASK=minha-feature test

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

# Output de testes
cat logs/minha-feature.tests.out
```

### Relatório QA

```bash
# Ver relatório completo
cat reports/qa.json

# Status apenas
python3 -c "import json; print(json.load(open('reports/qa.json'))['status'])"

# Próximas ações
python3 -c "import json; print('\n'.join(json.load(open('reports/qa.json'))['next_actions']))"
```

## 🛠️ Comandos Úteis

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
```

## 🔧 Configuração Avançada

### Ajustar Timeouts

Edite `orchestrator/config.json`:

```json
{
  "timeouts": {
    "planner": 300,    // 5 minutos
    "coder": 600,      // 10 minutos
    "tester": 900      // 15 minutos
  }
}
```

### Ajustar Limites

```json
{
  "limits": {
    "max_diff_lines": 2000,
    "min_coverage": 80,
    "max_lint_errors": 5
  }
}
```

### Configurar CLIs

```json
{
  "clis": {
    "planner": {
      "command": "gemini",
      "args": ["plan", "--model", "gpt-4o", "--in", "{issue}"]
    }
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

## 📈 Métricas e KPIs

### Coletar Métricas

```bash
# Tempo por etapa
grep "elapsed" logs/*.log

# Cobertura de testes
grep "TOTAL" logs/*.tests.out

# Erros de lint
grep "error" logs/*.lint.out
```

### Relatório de Performance

```bash
# Gerar relatório simples
echo "=== Relatório de Performance ==="
echo "Task: $(ls issues/ | grep -v TEMPLATE)"
echo "Status: $(python3 -c "import json; print(json.load(open('reports/qa.json'))['status'])" 2>/dev/null || echo 'N/A')"
echo "Tempo total: $(python3 -c "import json; print(json.load(open('reports/qa.json'))['elapsed_sec'])" 2>/dev/null || echo 'N/A')s"
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
- ❌ Ignorar warnings
- ❌ Não verificar next_actions
