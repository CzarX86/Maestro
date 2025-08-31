# 🎭 Maestro Orchestrator - Poetry Setup

## ✅ Poetry Configurado com Sucesso!

Este projeto agora usa **Poetry** para gerenciamento de dependências Python.

## 📋 Resumo da Configuração

### ✅ Arquivos Criados/Atualizados:
- `pyproject.toml` - Configuração principal do Poetry
- `poetry.lock` - Lock file das dependências
- `src/maestro/` - Estrutura de código fonte
- `scripts/dev.sh` - Scripts de desenvolvimento
- `.poetry-config` - Configuração e lembretes
- `.cursor-poetry-reminder` - Lembrete para Cursor AI
- `Makefile` - Atualizado para usar Poetry
- `README.md` - Documentação atualizada

### ✅ Dependências Instaladas:
- `websockets` - Para dashboard em tempo real
- `pytest` - Para testes
- `pytest-cov` - Para cobertura de testes
- `ruff` - Para linting
- `mypy` - Para type checking
- `black` - Para formatação de código
- `isort` - Para ordenação de imports
- `pre-commit` - Para hooks de commit

## 🚀 Como Usar

### Comandos Principais:
```bash
# Instalar dependências
poetry install

# Executar comandos Python
poetry run python script.py
poetry run pytest tests/
poetry run ruff check src/

# Ativar ambiente virtual
poetry shell

# Adicionar dependências
poetry add package-name

# Usar comandos Make (usam Poetry internamente)
make install
make test
make lint
make dashboard
```

### Scripts de Desenvolvimento:
```bash
# Usar script de desenvolvimento
./scripts/dev.sh install
./scripts/dev.sh test
./scripts/dev.sh dashboard
./scripts/dev.sh help
```

## 🔧 Configuração para Cursor AI

O arquivo `.cursor-poetry-reminder` contém lembretes importantes:

- ✅ **SEMPRE** use `poetry run` para comandos Python
- ❌ **NUNCA** use `python` diretamente
- ✅ **SEMPRE** use `poetry add` para instalar pacotes
- ❌ **NUNCA** use `pip install`

## 📁 Estrutura do Projeto

```
Maestro/
├── src/maestro/              # Código fonte principal
│   ├── __init__.py
│   ├── orchestrator.py       # Orquestrador principal
│   ├── dashboard.py          # Servidor dashboard
│   └── demo.py              # Demo do dashboard
├── tests/                   # Testes automatizados
├── dashboard/               # Dashboard web
├── scripts/                 # Scripts de desenvolvimento
├── pyproject.toml          # Configuração Poetry
├── poetry.lock             # Lock file
├── .poetry-config          # Configuração e lembretes
├── .cursor-poetry-reminder # Lembrete para Cursor AI
└── Makefile                # Comandos Make (usam Poetry)
```

## 🎯 Próximos Passos

1. **Desenvolvimento**: Use `poetry shell` para ativar o ambiente
2. **Testes**: Execute `make test` ou `poetry run pytest`
3. **Dashboard**: Execute `make dashboard` ou `poetry run python dashboard/server.py`
4. **Linting**: Execute `make lint` ou `poetry run ruff check src/`

## 💡 Lembretes Importantes

- **SEMPRE** use Poetry para comandos Python
- **NUNCA** use `pip` diretamente
- **SEMPRE** use `poetry run` para executar scripts
- **SEMPRE** use `poetry add` para adicionar dependências

---

**🎉 Poetry configurado com sucesso! O projeto está pronto para desenvolvimento.**