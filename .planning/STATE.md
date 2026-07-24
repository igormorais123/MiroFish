# STATE — MiroFish INTEIA

Atualizado em: 2026-07-24

## Estado atual

- **Milestone:** v1.4 — Coordenação segura pela Helena.
- **Produção:** `https://inteia.com.br/mirofish/`, servida pela VPS `hermes`.
- **Código publicado:** PR `#99`, commit
  `07306e711509772038b381176781ce80edacdfa0`.
- **Runtime:** `mirofish-inteia` observado `running/healthy`, zero reinícios.
- **Helena:** status público `available=true`, versão `1.0`.
- **Posicionamento científico:** exploratório auditado (C0–C2); C3–C4 seguem
  bloqueados sem painel humano.

## Entregue

1. Caixa Helena global nas cinco fases, acessível por `Alt+H` e responsiva.
2. Contexto de rota e identificadores canônicos revalidados no servidor.
3. Planejamento por allowlist, sem shell, escrita arbitrária ou HTTP livre.
4. Confirmação humana para mutações, tokens de uso único, TTL e idempotência.
5. Executor no navegador reutilizando exclusivamente as APIs das fases.
6. Auditoria atômica e redigida em `backend/uploads/helena_commands/`.
7. Bloqueio de comandos equivalentes e reconciliação de operações abandonadas.
8. Gate estrutural, evidência, diversidade social e governança cliente/demo
   preservados sem regressão.
9. Backup e imagem de rollback criados antes do cutover.

## Evidência de validação

- backend completo: `390 passed`;
- backend focado Helena: `15 passed`;
- frontend Helena: `8 passed`;
- build frontend, `compileall`, `pip-audit` e `npm audit --audit-level=high`
  aprovados;
- seis rotas críticas verificadas em desktop e móvel;
- contrato público, autenticação, plano de leitura, aprovação, execução,
  cancelamento e histórico exercitados;
- health público e status Helena responderam corretamente após o deploy.

O registro detalhado está em
[`docs/ops/PUBLICACAO_HELENA_2026-07-24.md`](../docs/ops/PUBLICACAO_HELENA_2026-07-24.md).

## Decisões vigentes

- `main` e `/opt/mirofish-git` são as únicas fontes do deploy.
- Vercel é alternativa histórica, não a produção canônica.
- A Helena não aprova o próprio plano e não executa mutações sem humano.
- O token interno nunca vai para bundle, query string ou persistência do browser.
- Relatório cliente só é `publishable` após gates estrutural e de evidência.
- Demo/smoke permanece `diagnostic_only`.

## Pendências reais

1. Executar uma simulação cliente longa, com fontes reais e LLM ativo, até um
   relatório `publishable`.
2. Observar métricas operacionais e feedback de uso da Helena antes de ampliar
   sua allowlist.
3. Corrigir a infraestrutura externa de GitHub Actions, cuja execução falhou
   antes de produzir steps/logs; os testes locais e de produção foram aprovados.

## Mapas vivos

- [Arquitetura do sistema](architecture/system-architecture.html).
- [Arquitetura da Helena](architecture/helena-control-plane.html).
- [Grafo estrutural](../graphify-out/graph.html).
- [Mapa da documentação](DOCUMENTATION_MAP.md).
