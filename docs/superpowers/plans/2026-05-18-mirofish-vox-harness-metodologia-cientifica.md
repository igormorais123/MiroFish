# Plano Vox: bombada metodologica e cientifica do harness MiroFish

Data: 2026-05-18
Status: proposta executavel para implementacao incremental
Escopo: MiroFish / Vox Sintetica / harness de simulacao sintetica ancorada

## 1. Linha operacional

A restricao e parte do metodo: nao faremos entrevistas longas, novos questionarios, novo painel humano ou nova calibracao humana. O objetivo e extrair o maximo com dados publicos, documentos ja existentes, artefatos internos do MiroFish e avaliacao computacional rigorosa.

- Camada interna: gates, rastreabilidade, incerteza, robustez, baselines publicos e auditoria de claims.
- Camada externa: linguagem forte, executiva e confiante: simulacao calibrada, inteligencia sintetica, sinais de adesao, cenarios de decisao, sensibilidade por segmento e lastro metodologico.

Nao usar como headline: "isto nao preve", "nao substitui pesquisa", "nao serve para inferir". O controle tecnico continua existindo, mas o produto deve se apresentar pelo que entrega: uma operacao de simulacao ancorada, auditavel e comparavel.

## 2. Tese metodologica

O estado da arte mais forte em simulacao individual usa self-reports e entrevistas ricas para criar agentes individuais. Como essa rota nao esta disponivel aqui, a melhor alternativa viavel e uma arquitetura de "public-data maximum viable fidelity":

1. Ancorar a populacao em microdados e cadastros publicos.
2. Preservar distribuicoes conjuntas por raking/IPF, pesos e estratos.
3. Criar personas por perfis estruturais, nao por caricaturas textuais.
4. Adicionar textura com documentos publicos e ativos internos ja existentes.
5. Separar variaveis de perfil, tratamento e outcome para evitar vazamento.
6. Rodar multiplas seeds, parafrases, ordens de alternativas e modelos quando possivel.
7. Comparar com benchmarks publicos quando existirem.
8. Bloquear ou rebaixar internamente claims que nao tenham baseline ou robustez suficiente.

O salto cientifico do MiroFish nao deve ser "fingir que sinteticamente entrevistou humanos". O salto deve ser ter um harness que sabe exatamente de onde vem cada inferencia, quao estavel ela e, contra qual base ela foi comparada e qual forca de claim ela suporta.

## 3. Arvores de perguntas

### Arvore A: populacao, decisao e claim

- Qual decisao o cliente precisa tomar?
  - Se e comunicacao: medir aceitacao, rejeicao, argumentos, gatilhos e grupos sensiveis.
  - Se e politica publica: mapear friccoes, trade-offs, legitimidade percebida e risco de implementacao.
  - Se e eleicao/campanha: separar sinais de narrativa, segmentos e cenarios de persuasao de qualquer claim de "intencao de voto" sem baseline.
- Qual e a populacao-alvo?
  - Brasil geral, eleitorado, servidores federais, municipio, classe profissional, base digital, stakeholders institucionais.
- Existe universo publico conhecido?
  - Sim: usar IBGE, TSE, PEP/MGI, Vozes, ESEB, cadastros setoriais ou bases abertas.
  - Nao: criar `baseline_status=missing_public_baseline` e limitar a entrega a mapa de sinais, hipoteses e simulacao de cenarios.
- Qual forca de claim a entrega pretende sustentar?
  - Qualitativo: exige rastreabilidade de fontes e diversidade de perfis.
  - Quantitativo exploratorio: exige pesos, seeds, parafrases e variancia.
  - Quantitativo calibrado: exige baseline publico comparavel.
  - Causal/preditivo forte: exige desenho temporal, contrafactual ou validacao externa; se ausente, manter como cenario e sensibilidade.

### Arvore B: dados publicos e ancoragem

- Quais variaveis definem "quem" a persona representa?
  - Demografia, territorio, renda, escolaridade, ocupacao, vinculo institucional, religiao quando licita e disponivel, setor, carreira, geracao, tempo de servico.
- Essas variaveis existem em microdados ou tabelas publicas?
  - Sim: registrar fonte, data, granularidade, pesos e variaveis mapeadas.
  - Parcial: usar proxy documentado e marcar incerteza de cobertura.
  - Nao: tratar como prior fraco, nao como ancora.
- Ha dados de atitude/opiniao publicos?
  - Sim: ESEB, Vozes, Datafolha/Quaest/Ipec publicados, surveys academicos, Latinobarometro, WVS, CESOP.
  - Nao: usar documentos publicos, debates, textos, audiencias, redes abertas e relatorios como textura qualitativa, sem calibrar percentual populacional.
- O outcome aparece nos dados de perfil?
  - Se sim, remover do prompt da persona e guardar apenas como baseline de validacao.

### Arvore C: construcao de personas

- A persona nasce de microdados, de rotulo ou de texto livre?
  - Microdados: preferido.
  - Rotulo amplo: permitido apenas como fallback.
  - Texto livre inventado: proibido para claim forte.
- A persona preserva distribuicoes conjuntas?
  - Sim: usar amostragem ponderada ou IPF/raking.
  - Nao: restringir a simulacao a exploracao qualitativa.
- A persona vira caricatura?
  - Testar diversidade lexical, variancia de respostas, respostas extremas por subgrupo e dependencia de estereotipos.
- Ha memoria/backstory?
  - Usar documentos publicos e ativos internos como "context pack" por segmento.
  - Nao inventar biografia longa quando a base so sustenta perfil estrutural.

### Arvore D: coleta sintetica

- O item e fechado, aberto ou conversacional?
  - Fechado: temperatura baixa, ordem randomizada, opcoes embaralhadas, JSON schema.
  - Aberto: pedir razoes, contra-razoes, condicoes de mudanca e intensidade.
  - Conversacional: limitar turns, registrar memoria e evitar conduzir o agente.
- Quantas repeticoes?
  - Minimo: 3 parafrases x 5 seeds em piloto.
  - Operacional: 3 parafrases x 10 seeds por celula importante.
  - Alta criticidade: ensemble de modelos e teste de ordem.
- O prompt revela a hipotese?
  - Se sim, reescrever com principio de unawareness.
- O prompt controla demais a resposta?
  - Se sim, reduzir diretividade e registrar como falha Minimal-Control/PIMMUR.

### Arvore E: validacao sem nova pesquisa humana

- Existe benchmark publico comparavel?
  - Sim: calcular erro agregado, erro por subgrupo, distancia de distribuicao e variancia.
  - Nao: produzir avaliacao de robustez interna e declarar internamente que o claim e qualitativo/exploratorio.
- Qual e o nivel de estabilidade?
  - Seed dispersion, paraphrase dispersion, order effect, variance ratio, drift entre modelos.
- A simulacao reproduz medias mas perde variancia?
  - Se variance_ratio < 0.50, bloquear claim quantitativo forte.
- Pequenos grupos explodem o erro?
  - Se erro por subgrupo > 8 pp em target calibravel, exigir reponderacao ou rebaixar claim.

### Arvore F: entrega e linguagem

- O resultado e forte o bastante para numero?
  - Sim: apresentar intervalo/sensibilidade e base de ancoragem.
  - Nao: apresentar ranking, sinais, segmentos, argumentos e cenarios.
- A linguagem enfraquece o produto?
  - Trocar "nao preve" por "modelo de cenarios calibrado por dados publicos e auditado por robustez".
  - Trocar "nao substitui pesquisa" por "opera como camada rapida de pre-teste, inteligencia e simulacao antes de decisoes caras".
- O claim e rastreavel?
  - Todo claim importante deve apontar para baseline, artefato, forecast ledger ou evidence bundle.

## 4. Respostas de implantacao

| Pergunta | Resposta adotada | Como implantar |
|---|---|---|
| Como compensar ausencia de entrevistas novas? | Usar microdados, bases publicas, documentos existentes e RAG de contexto por segmento. | `baseline_registry.json`, `public_data_anchors.json`, `methodology_manifest.json`. |
| Como evitar caricatura? | Persona estrutural + textura documental, nunca estereotipo solto. | Gerador de personas com campos obrigatorios e teste D7 anticaricatura. |
| Como medir robustez? | Seeds, parafrases, ordem, modelo, dispersao e variancia. | `fidelity_report.json` com `seed_dispersion`, `paraphrase_dispersion`, `order_effect_score`, `variance_ratio`. |
| Como usar benchmarks publicos? | Separar baseline de perfil e baseline de outcome; outcome nao entra no prompt. | `baseline_registry.json` com `allowed_for_prompt=false` para outcomes. |
| Como vender sem se rebaixar? | Linguagem de simulacao calibrada, sinais, cenarios, sensibilidade e lastro. | `claim_policy_audit.json` checa termos e forca de claim. |
| Como integrar ao harness? | Acrescentar contrato cientifico ao bundle sem quebrar consumidores atuais. | `methodology` e `qualityGates` no evidence bundle. |

## 5. Protocolo MiroFish sem nova coleta humana

### Etapa 0: intake do claim

Registrar populacao, periodo, geografia, decisao, outcome, nivel de claim e ativos internos disponiveis.

Saida: `methodology_manifest.json`.

### Etapa 1: inventario de bases publicas

Buscar e registrar bases de perfil, atitude, opiniao, resultado historico e documentos setoriais.

Saida: `baseline_registry.json`.

### Etapa 2: mapa de ancoragem

Mapear cada variavel da persona para fonte, granularidade, data, peso, proxy e confianca.

Saida: `public_data_anchors.json`.

### Etapa 3: geracao da populacao sintetica

Criar amostra sintetica ponderada com preservacao de distribuicoes conjuntas. Quando possivel, usar IPF/raking para ajustar marginais conhecidos.

Saida: `persona_frame.json` ou manifest equivalente.

### Etapa 4: prompts versionados

Criar prompts por tipo de item, com parafrases, ordem randomizada, modo primeira/terceira pessoa quando sensivel e schema de resposta.

Saida: `prompt_registry.json`.

### Etapa 5: execucao controlada

Rodar seeds, parafrases, temperaturas e modelos com registro completo.

Saida: `model_run_registry.json` e `synthetic_interviews_manifest.json`.

### Etapa 6: fidelidade e robustez

Calcular medias, variancia, distancia de distribuicao, erro por subgrupo, seed dispersion, paraphrase dispersion, order effect e drift.

Saida: `fidelity_report.json`.

### Etapa 7: auditorias de metodo

Rodar PIMMUR, CoMPosT/contaminacao, claim policy e D7 anticaricatura.

Saidas: `pimmur_audit.json`, `compost_audit.json`, `claim_policy_audit.json`.

### Etapa 8: Science Gate

Congelar resultado com status, forca de claim permitida, artefatos presentes, riscos internos e modo de entrega.

Saida: `harness_science_gate.json`.

## 6. Artefatos novos

| Artefato | Obrigatorio para claim forte | Conteudo minimo |
|---|---:|---|
| `methodology_manifest.json` | Sim | populacao, periodo, decisao, tipo de claim, restricoes, ativos usados. |
| `baseline_registry.json` | Sim | fonte, link, data, variaveis, granularidade, uso permitido. |
| `public_data_anchors.json` | Sim | variavel da persona, fonte, proxy, confianca, peso. |
| `prompt_registry.json` | Sim | prompt_id, versao, item, parafrases, ordem, schema. |
| `model_run_registry.json` | Sim | modelo, temperatura, seed, data, parametros, hash de prompt. |
| `synthetic_interviews_manifest.json` | Sim | quantidade de agentes, celulas, turns, status e falhas. |
| `fidelity_report.json` | Sim | metricas agregadas, subgrupos, robustez, drift e thresholds. |
| `pimmur_audit.json` | Sim | Profile, Interaction, Memory, Minimal-Control, Unawareness, Realism. |
| `compost_audit.json` | P1 | contaminacao, uso de benchmark e separacao prompt/outcome. |
| `claim_policy_audit.json` | Sim | forca de claim, frases permitidas, frases bloqueadas, razao. |
| `harness_science_gate.json` | Sim | `passes_gate`, `claim_level`, blockers, warnings e recomendacao final. |

## 7. Science Gate proposto

P0 bloqueia claim quantitativo forte:

- Populacao-alvo ausente.
- Baseline publico ausente para claim quantitativo calibrado.
- Outcome usado no prompt da persona.
- Prompt sem versao, sem seed ou sem modelo registrado.
- Menos de 3 parafrases em item fechado critico.
- Variance ratio abaixo de 0.50 quando houver benchmark humano.
- Erro maximo por subgrupo acima de 8 pontos percentuais em benchmark comparavel.
- Seed/paraphrase dispersion acima de 0.20 sem explicacao.
- PIMMUR com falha em Profile, Minimal-Control ou Realism.
- Claim externo mais forte que o lastro interno permite.

P1 exige revisao:

- Pequeno grupo com n efetivo baixo.
- Fonte publica antiga ou proxy distante.
- Divergencia grande entre modelos.
- Ordem de alternativas muda ranking substantivo.
- Texto aberto com alta repeticao lexical ou baixa diversidade de argumentos.

Saida recomendada:

```json
{
  "passes_gate": true,
  "claim_level": "quantitative_exploratory",
  "max_external_language": "simulacao calibrada com dados publicos e robustez auditada",
  "blocked_language": ["pesquisa de opiniao", "margem de erro amostral", "intencao real de voto"],
  "required_artifacts_present": true
}
```

## 8. Politica de linguagem do produto

Usar:

- "simulacao sintetica calibrada por dados publicos"
- "inteligencia de cenarios com trilha auditavel"
- "sinais de aceitacao, resistencia e persuadibilidade por segmento"
- "robustez testada por seeds, parafrases e baselines"
- "mapa de sensibilidade para decisao rapida"

Evitar como headline:

- "nao preve"
- "nao substitui pesquisa"
- "apenas hipotetico"
- "sem validade externa"

Regra: a entrega pode ser ambiciosa na forma, desde que o gate interno controle a forca do claim e registre quando o resultado e calibrado, exploratorio ou qualitativo.

## 9. Inventario inicial de fontes publicas

Fontes brasileiras prioritarias:

- IBGE PNAD Continua e Censo 2022: estrutura demografica, renda, trabalho, escolaridade, territorio.
- TSE Dados Abertos: perfil de eleitorado por pleito e secao, resultados eleitorais, candidaturas.
- PEP/MGI: servidores do Executivo Federal, carreira, vinculo, remuneracao, ingresso, aposentadoria e afastamentos.
- Pesquisa Vozes/MGI-Enap: ambiente de trabalho, engajamento, lideranca e perfil de servidores federais.
- CESOP/ESEB 2022: atitudes politicas, democracia, voto, confianca, ideologia e comportamento eleitoral.
- Bases publicas de institutos quando divulgadas com metodologia: Datafolha, Quaest, Ipec, PoderData e similares.
- Documentos institucionais: planos, audiencias, relatorios, notas tecnicas, consultas publicas e textos oficiais.

## 10. Backlog de implementacao

### P0

1. Criar schemas dos 11 artefatos Vox Science.
2. Fazer o ReportManager salvar/carregar os artefatos no pipeline.
3. Adicionar gerador de `methodology_manifest.json` no intake da simulacao.
4. Adicionar `baseline_registry.json` com fontes publicas e uso permitido.
5. Criar `prompt_registry.json` e `model_run_registry.json` em toda execucao sintetica.
6. Calcular `fidelity_report.json` com seeds, parafrases, variancia e erro por baseline.
7. Criar `harness_science_gate.json`.
8. Expor `methodology` e `qualityGates` no evidence bundle interno.

### P1

1. Implementar auditoria PIMMUR automatica.
2. Implementar auditoria CoMPosT/contaminacao.
3. Implementar D7 anticaricatura com testes de diversidade, extremismo e estereotipo.
4. Criar comparadores de distribuicao: TV, JS/KL, Wasserstein e erro por subgrupo.
5. Criar dashboard de robustez no frontend.

### P2

1. Ensemble multi-modelo para missoes criticas.
2. Curvas de saturacao por numero de agentes.
3. MrP/pos-estratificacao quando houver baselines territoriais.
4. Biblioteca de context packs por dominio: servidor publico, eleitorado, municipio, comunicacao institucional.
5. Export executivo com "evidence portfolio" e linguagem ajustada pelo claim gate.

## 11. Onde isto entra no codigo atual

Pontos ja existentes:

- `backend/app/services/harness_evidence_bundle.py`: contrato interno de evidencia.
- `backend/app/services/report_method_checklist.py`: checklist de entrega.
- `backend/app/services/forecast_ledger.py`: previsoes estruturadas e calibracao quando resolvidas.
- `backend/app/services/oasis_profile_generator.py`: geracao de perfis/personas.
- `backend/app/services/decision_packet.py`: cenarios, convergencia e red team.

Mudanca recomendada:

- O evidence bundle passa a carregar a camada `methodology` e `qualityGates`.
- O checklist reconhece artefatos Vox Science.
- O pipeline de relatorio deve produzir os artefatos, nao apenas o markdown final.

## 12. Referencias estudadas

Relatorios locais:

- `voxsintetica_spec.md`
- `DOSSIE_IA_DETALHADO.md`
- `01_variaveis_calibracao_1000_agentes_servidores_federais.md`
- `02_vulnerabilidades_agentes_sinteticos_revisao_2024-2026.md`
- `03_vulnerabilidades_mitigacoes_estado_arte_2026.md`
- `04_personas_sinteticas_ancoradas_microdados_2024-2026.md`
- `05_ranking_fidelidade_e_desenho_metodologico_otimo.md`
- `06_ranking_6_dimensoes_e_protocolo_prescritivo_8_etapas.md`

Fontes externas consultadas:

- Park et al., "LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals", arXiv 2411.10109: https://arxiv.org/abs/2411.10109
- Zhou et al., "The PIMMUR Principles", arXiv 2509.18052: https://arxiv.org/abs/2509.18052
- AAPOR, "Responsible AI Integration in Survey Research", 2026: https://aapor.org/announcements/task-force-on-responsible-ai-integration-in-survey-research-report/
- PEP/MGI, Painel Estatistico de Pessoal: https://www.gov.br/servidor/pt-br/observatorio-de-pessoal-govbr/painel-estatistico-de-pessoal
- Pesquisa Vozes/MGI: https://www.gov.br/gestao/pt-br/assuntos/pesquisa-vozes
- TSE Dados Abertos, Eleitorado: https://dadosabertos.tse.jus.br/id/group/eleitorado
- CESOP/ESEB 2022: https://www.cesop.unicamp.br/democracia/survey/detalhes/id/304/titulo/Estudo%20Eleitoral%20Brasileiro%20-%20ESEB%202022/
- IBGE PNAD Continua microdados: https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/2022/

