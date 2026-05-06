# Ranking: OpenSwarm Specialist Routing v1

## Fonte

- Repositorio estudado: `https://github.com/VRSEN/OpenSwarm`.
- Commit estudado: `92c8062bfeb58a9e96db8b7ac72da5f95c33479e`.
- Data do commit: `2026-05-06 16:15:23 +0400`.
- Transcricao fornecida pelo usuario: capitulos 1 a 8 sobre OpenSwarm.

## Observacoes extraidas

- OpenSwarm separa especialistas por pasta, prompt e ferramentas.
- `swarm.py` conecta orquestrador a especialistas via `SendMessage` e permite `Handoff` entre agentes.
- `AGENTS.md` funciona como guia para agentes de codigo customizarem o proprio swarm.
- O orquestrador e instruido a rotear, nao executar.
- O video enfatiza handoff de contexto util em vez de despejar resultados crus no proximo agente.
- A demo transforma pesquisa, analise de dados, slides e documentos em um pacote de entregaveis.
- O agente de slides usa subagentes isolados por slide; a qualidade depende de brief completo antes de executar.

## Criterios

Pontuacao de 0 a 100 usando a semente Efesto adaptada:

- formato_blocos: artefatos claros e portaveis.
- verificabilidade_factual: fontes, commit, evidencias e limites.
- acionabilidade: proxima acao pequena.
- protocolo_sem_muro: bloqueios e riscos explicitos.
- red_team_real: critica de complexidade e seguranca.
- dominio_especifico: encaixe com Ralph Loop Mirofish.

## Variantes

| Rank | Variante | Score | Decisao |
| --- | --- | ---: | --- |
| 1 | Lanes especialistas dentro de AutoResearch, sem runtime multiagente | 92.1 | Vencedor |
| 2 | Context packets obrigatorios entre PM, executor, verifier e AutoResearch | 89.4 | Incorporar parcialmente |
| 3 | Adicionar agentes de entregaveis docs/slides ao Ralph | 74.2 | Adiar ate haver 3 a 5 runs |
| 4 | Copiar topologia OpenSwarm inteira para Ralph | 57.0 | Rejeitar agora |
| 5 | Nao mudar o metodo | 51.8 | Rejeitar |

## Vencedor

Adicionar uma camada leve de roteamento por lanes ao PM e ao AutoResearch:

- `research_intake`
- `method_mapper`
- `evaluator_designer`
- `patch_writer`
- `red_team`

Essas lanes sao papeis de metodo, nao agentes autonomos com permissao ampla. Cada run continua tendo uma unidade pequena e verificavel.

## Justificativa

A variante vencedora aproveita o melhor do OpenSwarm sem violar a regra central Ralph. Ela melhora a acionabilidade porque o PM classifica o tipo de trabalho antes de marcar a tarefa como pronta. Tambem melhora red-team porque transforma revisao adversarial em lane explicita quando a fonte e externa ou o patch mexe no metodo.

