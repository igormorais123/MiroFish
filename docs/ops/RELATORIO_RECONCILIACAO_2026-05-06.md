> SUPERSEDIDO em 2026-05-10 — leia [`RELATORIO_RECONCILIACAO_2026-05-10.md`](RELATORIO_RECONCILIACAO_2026-05-10.md). Este documento fica preservado apenas como registro histórico do ciclo 2026-05-06.

# Relatório de reconciliação — MiroFish — 2026-05-06

## Resumo

O MiroFish estava operacional, mas sem fonte única de verdade. Havia divergência entre:

1. GitHub `igormorais123/MiroFish`.
2. Site público Vercel em `https://inteia.com.br/mirofish`.
3. Diretório VPS `/opt/mirofish` sem `.git`.
4. Container `mirofish` usando imagem externa `ghcr.io/666ghj/mirofish:latest`.
5. Subdomínio legado `mirofish.inteia.com.br` apontando para porta sem serviço.

## Evidências principais

- `https://inteia.com.br/mirofish` respondeu 200 via Vercel.
- `https://inteia.com.br/mirofish/api/simulation/history?limit=1` respondeu 200.
- A resposta pública da API tinha o mesmo hash do backend local `127.0.0.1:5001`.
- `/opt/mirofish` retornou `fatal: not a git repository`.
- `/opt/mirofish-inteia` retornou `fatal: not a git repository`.
- O frontend local em `3001` estava em modo dev Vite com marcações chinesas antigas.
- O build público, o build local e o build do GitHub gerado em teste tinham nomes de asset diferentes.

## Decisão

Este PR não troca deploy nem apaga nada. Ele cria documentação operacional e um script de verificação para impedir novas mudanças erradas.

A próxima etapa segura é criar uma branch de reconciliação de código real, trazendo apenas patches úteis da VPS para o GitHub e descartando lixo operacional.

## Próxima etapa recomendada

1. Backup completo da VPS.
2. Clone limpo do GitHub em novo diretório.
3. Diff controlado contra `/opt/mirofish`.
4. PR com patches reais.
5. Deploy do frontend pela Vercel a partir do GitHub.
6. Deploy do backend na VPS a partir de clone Git limpo.
