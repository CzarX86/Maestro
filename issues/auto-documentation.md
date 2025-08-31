# Implementar Documentação Automática em Tempo Real

## Contexto

- Projeto Maestro atualiza código automaticamente via pipeline
- Documentação manual (README.md, USER_MANUAL.md, USAGE.md) não é atualizada automaticamente
- Desenvolvedores precisam manter documentação sincronizada manualmente
- Watcher existe para monitorar issues mas não documentação
- Dashboard mostra métricas mas não atualiza docs

## Objetivo

Sistema de documentação automática que atualiza README.md, USER_MANUAL.md e USAGE.md baseado nas mudanças de código e relatórios QA gerados pelo pipeline

## Escopo incluído

- Agente de documentação que analisa reports/qa.json
- Atualização automática de README.md com novas features
- Atualização automática de USER_MANUAL.md com novos comandos/configurações
- Atualização automática de USAGE.md com novos exemplos
- Integração com watcher.sh para disparo automático
- Dashboard com seção de documentação em tempo real
- Templates de documentação baseados em plan.json e spec.md

## Escopo excluído

- Documentação de APIs externas
- Geração de diagramas complexos
- Tradução automática de documentação
- Versionamento de documentação histórica

## Entregáveis esperados

- src/maestro/documentation_agent.py: agente de documentação automática
- docs/templates/README.template.md: template para README.md
- docs/templates/USER_MANUAL.template.md: template para USER_MANUAL.md
- docs/templates/USAGE.template.md: template para USAGE.md
- orchestrator/documentation_watcher.sh: watcher específico para documentação
- dashboard/documentation_panel.html: painel de documentação no dashboard
- tests/test_documentation_agent.py: testes do agente de documentação

## Critérios de aceitação

- [ ] Agente detecta mudanças em reports/qa.json automaticamente
- [ ] README.md é atualizado com novas features implementadas
- [ ] USER_MANUAL.md é atualizado com novos comandos/configurações
- [ ] USAGE.md é atualizado com novos exemplos de uso
- [ ] Dashboard mostra status de documentação em tempo real
- [ ] Watcher dispara atualização de documentação quando pipeline completa
- [ ] Templates mantêm formatação e estrutura consistente
- [ ] Testes validam geração correta de documentação
- [ ] Sistema funciona com múltiplas tasks simultâneas

## Riscos

- Conflitos de merge em documentação: usar locks de arquivo
- Perda de conteúdo manual: fazer backup antes de atualizar
- Performance com muitos arquivos: implementar cache inteligente
- Formatação inconsistente: usar templates rígidos

## Limites

- Tempo máx etapa: Planner=120, Coder=300, Tester=600
- Diff máx: 2000 linhas (documentação pode ser grande)
- Paths permitidos: docs/\*\*, README.md, src/maestro/documentation_agent.py, tests/test_documentation_agent.py, dashboard/documentation_panel.html

## Referências

- docs/USER_MANUAL.md: estrutura atual da documentação
- README.md: formato atual do README
- docs/USAGE.md: exemplos de uso atuais
- orchestrator/watcher.sh: implementação atual do watcher
- dashboard/README.md: estrutura do dashboard
- reports/qa.template.json: formato dos relatórios QA
