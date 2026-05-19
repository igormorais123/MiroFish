# Plano pratico nivel 2: Vox Science Harness v2 no MiroFish

Data: 2026-05-18
Status: plano pratico de implementacao
Base: plano metodologico nivel 1 em `2026-05-18-mirofish-vox-harness-metodologia-cientifica.md`
Restricao fixa: sem entrevistas novas, sem questionarios novos, sem nova coleta humana

## 1. Resultado esperado

Construir uma versao v2 do harness Vox dentro do MiroFish que entregue simulacoes sinteticas com:

1. Populacao sintetica ancorada em dados publicos e ativos internos.
2. Prompts versionados, com parafrases, ordem controlada e seeds.
3. Execucao sintetica rastreavel por modelo, temperatura, seed e celula.
4. Relatorio de fidelidade com variancia, estabilidade e erro contra baseline quando houver.
5. Science Gate que define a forca maxima do claim.
6. Evidence bundle enriquecido com `methodology` e `qualityGates`.
7. Linguagem externa forte: simulacao calibrada, cenarios, sinais, sensibilidade e inteligencia de decisao.

O objetivo nao e imitar pesquisa humana tradicional. O objetivo e criar um motor rapido, auditavel e comparavel que usa o melhor lastro disponivel sem depender de nova coleta.

## 2. Decisao estrategica nivel 2

O MiroFish deve seguir a rota "Public-Data Grounded Synthetic Harness".

Essa rota aceita que o melhor resultado academico atual vem de agentes com self-reports ricos e entrevistas longas, mas transforma isso em engenharia viavel:

- Onde o estado da arte usa entrevista individual, o MiroFish usa microdados, surveys publicos, documentos, grafo e ativos ja existentes.
- Onde a literatura encontra risco de erro por subgrupo, o MiroFish cria gate de subgrupo e rebaixa claim internamente.
- Onde ha risco de prompt dirigir a resposta, o MiroFish registra prompt, parafrase, ordem, seed e PIMMUR.
- Onde ha risco de output bonito mas fragil, o MiroFish exige `fidelity_report.json` antes de claim forte.

## 3. O que muda na pratica

Hoje o harness ja consegue gerar relatorio, decision packet, forecast ledger, mission bundle, evidencia e bundle interno.

O nivel 2 adiciona uma camada cientifica antes, durante e depois da simulacao:

```mermaid
flowchart LR
  A["Intake da missao"] --> B["Baseline Registry"]
  B --> C["Persona Frame"]
  C --> D["Prompt Registry"]
  D --> E["Synthetic Runs"]
  E --> F["Fidelity Report"]
  F --> G["PIMMUR + Claim Gate"]
  G --> H["Harness Science Gate"]
  H --> I["Report + Decision Packet"]
  I --> J["Evidence Bundle v2"]
```

## 4. Workstreams

### Workstream 1: Baseline e dados publicos

Responsabilidade: transformar fontes publicas em lastro operacional.

Arquivos novos:

- `backend/app/services/vox_science/baseline_registry.py`
- `backend/app/services/vox_science/public_data_anchors.py`
- `backend/app/services/vox_science/source_cards.py`

Artefatos:

- `baseline_registry.json`
- `public_data_anchors.json`
- `source_cards.json`

Criterio de aceite:

- Toda variavel de persona tem uma fonte, proxy ou classificacao `unsupported_prior`.
- Toda fonte tem data, link, granularidade, variaveis extraidas, status de uso e limitacao interna.
- Outcome usado como validacao nao entra no prompt da persona.

Fontes prioritarias:

- Geral Brasil: IBGE Censo 2022, PNAD Continua, TSE Dados Abertos, ESEB/CESOP, WVS/Latinobarometro quando cabivel.
- Servidores federais: PEP/MGI, Pesquisa Vozes/MGI-Enap, Atlas do Estado Brasileiro/IPEA quando cabivel, dados de concursos/carreiras/remuneracao disponiveis.
- Eleitoral/territorial: TSE eleitorado, resultados por municipio/secao, IBGE municipio, camara/senado/dados legislativos, documentos oficiais e noticias publicas.

### Workstream 2: Persona Frame

Responsabilidade: gerar a populacao sintetica sem caricatura.

Arquivos novos:

- `backend/app/services/vox_science/persona_frame.py`
- `backend/app/services/vox_science/persona_sampler.py`
- `backend/app/services/vox_science/anti_caricature.py`

Artefatos:

- `persona_frame.json`
- `persona_sample_manifest.json`
- `anti_caricature_audit.json`

Criterio de aceite:

- Cada agente tem `agent_id`, `cell_id`, `weight`, `profile_variables`, `source_trace` e `prompt_allowed_variables`.
- O frame diferencia `profile_variable`, `context_variable`, `outcome_variable` e `forbidden_prompt_variable`.
- Variaveis psicologicas entram como prior fraco, nunca como fato individual, salvo quando vierem de base publica adequada.
- O `anti_caricature_audit.json` mede concentracao de estereotipos, extremismo artificial, repeticao lexical e colapso de variancia.

Regra de construcao:

- Primeiro preservar estrutura: idade, sexo, territorio, escolaridade, renda, ocupacao, vinculo, carreira ou segmento.
- Depois adicionar contexto: documentos, grafo, temas, exposicao a debate, friccoes institucionais.
- Por ultimo adicionar textura comportamental com priors amplos e incerteza.

### Workstream 3: Prompt Registry e execucao sintetica

Responsabilidade: tornar cada resposta sintetica reprodutivel.

Arquivos novos:

- `backend/app/services/vox_science/prompt_registry.py`
- `backend/app/services/vox_science/synthetic_runner.py`
- `backend/app/services/vox_science/model_run_registry.py`

Artefatos:

- `prompt_registry.json`
- `model_run_registry.json`
- `synthetic_interviews_manifest.json`
- `synthetic_responses.jsonl`

Criterio de aceite:

- Toda pergunta tem `question_id`, `construct`, `claim_use`, `paraphrase_set`, `response_schema` e `randomization_policy`.
- Todo run tem modelo, temperatura, seed, prompt hash, persona hash, data e custo.
- Itens fechados criticos rodam pelo menos 3 parafrases x 5 seeds no MVP.
- Itens sensiveis rodam tambem em terceira pessoa quando isso reduz desejabilidade social.
- Multi-resposta recebe teste proprio, porque evidencias recentes indicam fragilidade maior nesse formato.

Padrao inicial de execucao:

```json
{
  "closed_item_low_risk": {"paraphrases": 3, "seeds": 5, "temperature": 0.2},
  "closed_item_high_risk": {"paraphrases": 5, "seeds": 10, "temperature": 0.1},
  "open_item": {"paraphrases": 2, "seeds": 5, "temperature": 0.5},
  "scenario_test": {"paraphrases": 3, "seeds": 8, "temperature": 0.3}
}
```

### Workstream 4: Fidelity Report

Responsabilidade: medir se a simulacao aguenta a propria entrega.

Arquivos novos:

- `backend/app/services/vox_science/fidelity_metrics.py`
- `backend/app/services/vox_science/subgroup_error.py`
- `backend/app/services/vox_science/robustness.py`

Artefato:

- `fidelity_report.json`

Metricas P0:

- `mean_absolute_error_pp`: erro medio em pontos percentuais quando houver baseline.
- `subgroup_max_error_pp`: maior erro por subgrupo comparavel.
- `variance_ratio`: variancia sintetica dividida pela variancia humana/publica comparavel.
- `seed_dispersion`: dispersao entre seeds.
- `paraphrase_dispersion`: dispersao entre parafrases.
- `order_effect_score`: efeito da ordem de alternativas.
- `nonresponse_rate`: respostas invalidas, recusas, schema failures.
- `stereotype_concentration`: repeticao de justificativas ou atribuicoes caricaturais por grupo.

Thresholds iniciais:

| Metrica | Verde | Amarelo | Vermelho |
|---|---:|---:|---:|
| MAE agregado | <= 6 pp | 6-12 pp | > 12 pp |
| Erro maximo por subgrupo | <= 8 pp | 8-15 pp | > 15 pp |
| Variance ratio | >= 0.70 | 0.50-0.70 | < 0.50 |
| Seed dispersion | <= 0.10 | 0.10-0.20 | > 0.20 |
| Paraphrase dispersion | <= 0.10 | 0.10-0.20 | > 0.20 |
| Schema failure | <= 2% | 2-5% | > 5% |

Regra:

- Verde sustenta claim quantitativo exploratorio ou calibrado, dependendo do baseline.
- Amarelo exige nota interna, reponderacao, nova execucao ou rebaixamento de claim.
- Vermelho bloqueia claim quantitativo forte.

### Workstream 5: PIMMUR, contaminacao e claim gate

Responsabilidade: impedir que o resultado seja artefato de prompt, vazamento ou linguagem acima do lastro.

Arquivos novos:

- `backend/app/services/vox_science/pimmur_audit.py`
- `backend/app/services/vox_science/contamination_audit.py`
- `backend/app/services/vox_science/claim_policy_gate.py`
- `backend/app/services/vox_science/science_gate.py`

Artefatos:

- `pimmur_audit.json`
- `compost_audit.json`
- `claim_policy_audit.json`
- `harness_science_gate.json`

PIMMUR aplicado ao MiroFish:

- Profile: persona tem fonte e estrutura, nao so rotulo.
- Interaction: interacao sintetica nao induz resposta.
- Memory: contexto usado e registrado, sem memoria inventada.
- Minimal-Control: prompt nao determina resultado.
- Unawareness: agente nao recebe hipotese, target ou resultado esperado.
- Realism: ambiente e tarefa parecem plausiveis para a populacao simulada.

Claim gate:

| Nivel | Nome | Requisitos | Linguagem externa permitida |
|---|---|---|---|
| C0 | Qualitativo | fontes e contexto rastreaveis | sinais, argumentos, friccoes, hipoteses |
| C1 | Exploratorio sintetico | persona frame + prompt registry + seeds | simulacao sintetica, cenarios, sensibilidade |
| C2 | Quantitativo exploratorio | C1 + fidelity verde/amarelo | percentuais sinteticos, ranking, faixas de sensibilidade |
| C3 | Calibrado por baseline publico | C2 + baseline comparavel + erro aceitavel | estimativa sintetica calibrada, comparacao por segmento |
| C4 | Preditivo monitoravel | C3 + forecast ledger + horizonte + evento observavel | previsao operacional monitoravel, cenario base/contrario |

Bloqueios:

- Nao chamar output sintetico de resposta humana.
- Nao usar margem de erro amostral se nao houve amostragem humana probabilistica.
- Nao usar outcome como atributo de persona.
- Nao sustentar C3/C4 sem baseline publico comparavel.

## 5. Sequencia de build

### Fase 1: vertical slice em 5 dias uteis

Objetivo: uma simulacao pequena ja gerando os 8 artefatos essenciais.

Tarefas:

1. Criar pacote `backend/app/services/vox_science/`.
2. Criar schemas simples para os artefatos P0.
3. Implementar `build_methodology_manifest()`.
4. Implementar `build_baseline_registry()` manual/semi-manual.
5. Implementar `build_prompt_registry()` para perguntas fechadas.
6. Implementar `build_model_run_registry()` com seed, modelo, temperatura e prompt hash.
7. Implementar `evaluate_science_gate()` lendo artefatos existentes.
8. Salvar artefatos via `ReportManager.save_json_artifact()`.
9. Garantir que o evidence bundle mostre `methodology.readiness`.

Definicao de pronto:

- Um relatorio gera `methodology_manifest.json`, `baseline_registry.json`, `prompt_registry.json`, `model_run_registry.json` e `harness_science_gate.json`.
- O endpoint interno de evidence bundle retorna `methodology.readiness != legacy`.
- Teste automatizado cobre science gate aprovado, parcial e bloqueado.

### Fase 2: fidelity real em 7 dias uteis

Objetivo: sair de artefato burocratico e medir robustez de verdade.

Tarefas:

1. Criar `synthetic_responses.jsonl`.
2. Rodar 3 parafrases x 5 seeds por item fechado.
3. Calcular dispersao por seed e parafrase.
4. Calcular schema failure e respostas invalidas.
5. Calcular variance ratio quando baseline existir.
6. Criar `fidelity_report.json`.
7. Fazer `harness_science_gate.json` consumir thresholds.

Definicao de pronto:

- Um item fechado gera matriz `agent x paraphrase x seed`.
- `fidelity_report.json` mostra metricas agregadas e por subgrupo.
- Gate bloqueia claim C2+ se dispersao passar do vermelho.

### Fase 3: primeiro dominio serio em 10 dias uteis

Dominio recomendado: servidores publicos federais.

Razao:

- Ja ha relatorios locais com variaveis de calibracao.
- PEP/MGI e Vozes oferecem lastro publico relevante.
- O usuario ja tem tese/doutorado conectado ao tema.
- Permite demonstrar alta fidelidade sem depender de coleta nova.

Tarefas:

1. Criar `domain_packs/servidores_federais/`.
2. Mapear variaveis PEP: sexo, idade/geracao, carreira, escolaridade, remuneracao, orgao, UF, situacao, tempo de servico quando disponivel.
3. Mapear Vozes: engajamento, clima, lideranca, PGD/teletrabalho, percepcao institucional quando publicamente disponivel.
4. Criar persona frame de 1.000 agentes com pesos.
5. Criar 10 perguntas-modelo: adesao a proposta, resistencia, legitimidade, risco, canal, narrativa, trade-off, friccao, persuadibilidade, condicao de mudanca.
6. Rodar piloto com 100 agentes.
7. Rodar versao 1.000 agentes se piloto passar.

Definicao de pronto:

- Dominio gera um "Vox Server Public Sector Pack" reutilizavel.
- Relatorio final separa sinais robustos, sinais instaveis e segmentos que exigem cautela interna.
- Entrega externa usa linguagem de inteligencia sintetica calibrada.

### Fase 4: frontend e operacao em 7 dias uteis

Objetivo: tornar o metodo visivel para Igor e para entrega.

Tarefas:

1. Mostrar readiness cientifico no painel do relatorio.
2. Mostrar fontes publicas usadas.
3. Mostrar claim level C0-C4.
4. Mostrar semaforo de robustez.
5. Mostrar frases permitidas pelo claim gate para o relatorio executivo.

Definicao de pronto:

- Usuario ve rapidamente: "este resultado sustenta C2" ou "este resultado sustenta C3".
- O relatorio executivo nao precisa explicar metodologia em excesso, mas carrega o lastro.

## 6. Schemas praticos P0

### `methodology_manifest.json`

```json
{
  "schema": "mirofish.vox.methodology_manifest.v1",
  "simulation_id": "sim_x",
  "population": "servidores publicos federais ativos",
  "period": "2024-2026",
  "decision": "avaliar aceitacao de proposta institucional",
  "claim_target": "C2",
  "human_collection": "none_new",
  "assets_used": ["public_data", "internal_graph", "client_documents"],
  "forbidden_methods": ["new_interviews", "new_surveys", "new_panels"]
}
```

### `baseline_registry.json`

```json
{
  "schema": "mirofish.vox.baseline_registry.v1",
  "population": "servidores publicos federais ativos",
  "anchors": [
    {
      "name": "PEP/MGI",
      "url": "https://www.gov.br/servidor/pt-br/observatorio-de-pessoal-govbr/painel-estatistico-de-pessoal",
      "type": "administrative_public_data",
      "variables": ["sexo", "idade", "escolaridade", "orgao", "remuneracao"],
      "allowed_for_prompt": true,
      "allowed_for_validation": true
    },
    {
      "name": "Pesquisa Vozes/MGI-Enap",
      "url": "https://www.gov.br/gestao/pt-br/assuntos/pesquisa-vozes",
      "type": "public_survey_results",
      "variables": ["clima", "engajamento", "lideranca", "pgd"],
      "allowed_for_prompt": false,
      "allowed_for_validation": true
    }
  ]
}
```

### `prompt_registry.json`

```json
{
  "schema": "mirofish.vox.prompt_registry.v1",
  "questions": [
    {
      "question_id": "q_acceptance_001",
      "construct": "proposal_acceptance",
      "claim_use": "C2",
      "paraphrases": ["p1", "p2", "p3"],
      "response_schema": {"type": "likert_5"},
      "randomization_policy": "rotate_options",
      "forbidden_context": ["target_distribution", "expected_answer"]
    }
  ]
}
```

### `fidelity_report.json`

```json
{
  "schema": "mirofish.vox.fidelity_report.v1",
  "overall_score": 0.78,
  "mean_absolute_error_pp": 5.8,
  "subgroup_max_error_pp": 7.5,
  "variance_ratio": 0.72,
  "seed_dispersion": 0.08,
  "paraphrase_dispersion": 0.09,
  "order_effect_score": 0.04,
  "passes_gate": true
}
```

### `harness_science_gate.json`

```json
{
  "schema": "mirofish.vox.harness_science_gate.v1",
  "passes_gate": true,
  "claim_level": "C2",
  "max_external_language": "simulacao sintetica calibrada por dados publicos e robustez auditada",
  "blockers": [],
  "warnings": ["baseline de outcome parcial"],
  "next_upgrade": "adicionar benchmark publico comparavel para C3"
}
```

## 7. Ordem de implementacao no codigo

### Primeiro PR

Escopo: infraestrutura dos artefatos.

Arquivos:

- `backend/app/services/vox_science/__init__.py`
- `backend/app/services/vox_science/artifact_schemas.py`
- `backend/app/services/vox_science/methodology_manifest.py`
- `backend/app/services/vox_science/science_gate.py`
- `backend/tests/test_vox_science_gate.py`

Integracao:

- Chamar builder de artefatos no fim da geracao do relatorio, perto de onde hoje sao salvos `decision_packet.json`, `forecast_ledger.json` e `mission_bundle.json`.

### Segundo PR

Escopo: prompts e runs.

Arquivos:

- `backend/app/services/vox_science/prompt_registry.py`
- `backend/app/services/vox_science/model_run_registry.py`
- `backend/app/services/vox_science/synthetic_runner.py`
- `backend/tests/test_vox_prompt_registry.py`

Integracao:

- Toda chamada sintetica recebe `run_id`, `prompt_hash`, `persona_hash`, `seed` e `temperature`.

### Terceiro PR

Escopo: fidelity.

Arquivos:

- `backend/app/services/vox_science/fidelity_metrics.py`
- `backend/app/services/vox_science/robustness.py`
- `backend/tests/test_vox_fidelity_metrics.py`

Integracao:

- `fidelity_report.json` vira input de `harness_science_gate.json`.

### Quarto PR

Escopo: dominio servidores federais.

Arquivos:

- `backend/app/services/vox_science/domain_packs/servidores_federais.py`
- `docs/ops/VOX_DOMAIN_PACK_SERVIDORES_FEDERAIS.md`
- `backend/tests/test_vox_servidores_domain_pack.py`

Integracao:

- Gerar 1.000 agentes ponderados e um piloto de perguntas fechadas/abertas.

## 8. Matriz de operacao para cada missao Vox

Antes de rodar:

- Definir populacao e periodo.
- Definir claim alvo C0-C4.
- Selecionar fonte publica principal.
- Separar variaveis permitidas no prompt e variaveis so de validacao.
- Definir numero de agentes, seeds e parafrases.

Durante:

- Registrar cada prompt e run.
- Guardar respostas brutas.
- Validar schema.
- Medir dispersao parcial.
- Interromper se schema failure passar de 5%.

Depois:

- Calcular fidelity.
- Rodar PIMMUR.
- Rodar claim gate.
- Gerar science gate.
- Gerar decision packet e forecast ledger apenas com claim compativel.

## 9. Como fica a entrega externa

Formato recomendado:

1. Tese operacional.
2. Segmentos mais receptivos e mais resistentes.
3. Gatilhos de aceitacao.
4. Gatilhos de rejeicao.
5. Narrativas com maior estabilidade entre seeds.
6. Pontos instaveis que exigem cuidado estrategico.
7. Cenario base, contrario e otimista.
8. Evidencias publicas e lastro sintetico.

Linguagem:

- "O Vox simulou uma populacao sintetica calibrada por dados publicos e testou robustez por parafrases e seeds."
- "O sinal mais forte esta em..."
- "A resistencia mais consistente aparece em..."
- "O resultado sustenta claim C2/C3 no gate interno."

Evitar:

- Linguagem de amostra humana quando nao houve amostra humana.
- Percentual com aparencia de pesquisa tradicional se o gate for C0/C1.
- Explicacao defensiva longa no inicio. O detalhe metodologico fica em anexo ou evidencia.

## 10. Piloto recomendado

Missao: testar o Vox para servidores publicos federais.

Populacao: servidores publicos federais ativos.

Amostra sintetica inicial:

- Piloto: 100 agentes.
- Operacional: 1.000 agentes.
- Alta criticidade: 3.000 agentes, se custo permitir.

Perguntas iniciais:

1. Aceitacao de proposta institucional.
2. Nivel de resistencia.
3. Condicao de mudanca.
4. Confiança no emissor.
5. Narrativa mais persuasiva.
6. Medo/friccao principal.
7. Canal preferido.
8. Risco de mobilizacao negativa.
9. Trade-off mais sensivel.
10. Argumento adversario mais forte.

Saidas:

- `persona_frame.json`
- `prompt_registry.json`
- `synthetic_responses.jsonl`
- `fidelity_report.json`
- `harness_science_gate.json`
- relatorio executivo Vox

## 11. Riscos que viram engenharia, nao freio comercial

| Risco | Tratamento pratico |
|---|---|
| Colapso de variancia | `variance_ratio` e bloqueio de C2+ quando vermelho. |
| Erro em subgrupo pequeno | `subgroup_max_error_pp`, n efetivo e reponderacao. |
| Prompt conduz resposta | PIMMUR Minimal-Control e parafrase obrigatoria. |
| Modelo responde media generica | seed/paraphrase dispersion + diversidade lexical. |
| Contaminacao por benchmark | outcome fora do prompt e `compost_audit.json`. |
| Desejabilidade social | terceira pessoa, formulacao indireta e comparacao de modo. |
| Multi-resposta fragil | schema especifico e gate mais severo para multi-select. |
| Linguagem acima do lastro | `claim_policy_audit.json`. |

## 12. Indicadores de sucesso

Em 30 dias:

- 1 dominio pack funcionando.
- 1 pipeline que gera os artefatos P0 automaticamente.
- Evidence bundle mostrando readiness cientifico.
- 1 relatorio Vox com claim gate explicito.
- 15 testes automatizados novos.

Em 60 dias:

- 2 dominios: servidores federais e eleitoral/territorial.
- Fidelity metrics por subgrupo.
- Dashboard simples de robustez.
- Biblioteca de fontes publicas reutilizaveis.

Em 90 dias:

- Claim C3 em pelo menos um dominio com baseline publico forte.
- Forecast ledger alimentado por science gate.
- Relatorios executivos com linguagem forte e lastro auditavel.

## 13. Referencias operacionais usadas

- Park et al., "LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals", arXiv 2411.10109: https://arxiv.org/abs/2411.10109
- Zhou et al., "The PIMMUR Principles", arXiv 2509.18052: https://arxiv.org/abs/2509.18052
- AAPOR, "Responsible AI Integration in Survey Research", 2026: https://aapor.org/announcements/task-force-on-responsible-ai-integration-in-survey-research-report/
- Gallup, "Gallup Begins Research on Simulated Responses", 2026: https://news.gallup.com/opinion/methodology/709373/gallup-begins-research-synthetic-responses.aspx
- Verasight, "Can Large Language Models Replicate Survey Data Across Topics?", 2026: https://www.verasight.io/reports/synthetic-omnibus-survey
- Lee et al., "Can large language models estimate public opinion about global warming?", PLOS Climate, 2024: https://journals.plos.org/climate/article?id=10.1371/journal.pclm.0000429
- PEP/MGI: https://www.gov.br/servidor/pt-br/observatorio-de-pessoal-govbr/painel-estatistico-de-pessoal
- Pesquisa Vozes/MGI: https://www.gov.br/gestao/pt-br/assuntos/pesquisa-vozes
- TSE Dados Abertos: https://dadosabertos.tse.jus.br/
- ESEB/CESOP 2022: https://www.cesop.unicamp.br/democracia/survey/detalhes/id/304/titulo/Estudo%20Eleitoral%20Brasileiro%20-%20ESEB%202022/

