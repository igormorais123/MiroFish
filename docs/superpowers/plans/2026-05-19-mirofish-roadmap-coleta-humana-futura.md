# Roadmap contingente — Coleta humana futura (Tier S) para Mirofish INTEIA

**Versão:** 1.0
**Data:** 2026-05-19
**Origem:** Entrega E10 da Fase 03 — Vox Academic Hardening.
**Status:** plano contingente. **Não executar** sem decisão expressa do Igor.

## 1. Contexto

O Mirofish INTEIA opera hoje em modo **exploratório auditado** com restrição operacional "zero coleta humana nova". Esta restrição vem de uma decisão estratégica de viabilidade do produto: não depender de painel humano permite escalar simulações sintéticas com baixo custo marginal.

A literatura 2024–2026 (Park et al. 2024; Kambhatla et al. 2025; Bisbee 2024; Boelaert 2025; Hu & Collier 2024) é convergente: agentes sintéticos LLM têm **teto estrutural ~40–50%** para construtos latentes (persuadibilidade, integridade, identidade social). Para ultrapassar esse teto e elevar o claim para níveis **C3 (estimativa calibrada)** ou **C4 (previsão operacional)**, há dois caminhos demonstrados:

- **Tier S — Rich backstory via entrevista (Park et al. 2024, Stanford):** 2 h de entrevista semiestruturada gera persona LLM com **85% de acurácia** contra teste–reteste humano.
- **Tier A — Calibração supervisionada pós-hoc (Kambhatla et al. 2025):** painel humano pequeno (n≥100) com regressão simples sobre saídas LLM produz **+16,3% de alinhamento médio**.

Este documento descreve o plano contingente. Ativação fica condicionada a (1) decisão de Igor por elevar claim para C3/C4 em produto específico, ou (2) demanda de cliente que pague pela calibração.

## 2. Critérios de gatilho

A coleta humana só deve ser iniciada se **pelo menos um** dos seguintes for verdadeiro:

1. **Cliente paga pela calibração**: contrato explícito cobre custo (~R$ 30k–R$ 80k para n=50 entrevistas semiestruturadas com transcrição e codificação).
2. **Mudança de claim**: decisão estratégica de Igor de elevar o produto para C3/C4 em segmento específico (ex: análise eleitoral preditiva, due diligence executivo).
3. **Tese doutoral exige**: capítulo experimental do doutorado pede teto >0.65 com evidência externa.

Sem nenhum desses gatilhos, **manter posicionamento exploratório auditado**.

## 3. Plano em 4 fases

### Fase A — Decisão e desenho amostral (2 semanas)

- Definir população-alvo (ex: servidores federais ativos de carreira X, OAB-DF, prefeitos de cidades médias).
- Escolher protocolo: Tier S (entrevista 2h) ou Tier A (questionário 30min + cluster humano).
- Estratificação mínima (sexo × faixa etária × região × função) — alvo n=50 (Tier S) ou n=100 (Tier A).
- TCLE com cláusula explícita "será usado para construir agente sintético".

### Fase B — Instrumento (4 semanas)

- Roteiro semiestruturado baseado em Park et al. 2024:
  - História de vida resumida (10 min)
  - Eixos disciplinares (trabalho/lazer/relações/valores) (20 min)
  - Cenários hipotéticos do domínio (60 min)
  - Auto-percepção e variabilidade declarada (20 min)
- Codificação obrigatória: Br-STPS (Durelli et al. 2017) para persuadibilidade quando aplicável.
- Anonimização k≥5 imediata pós-transcrição. Identificadores diretos descartados.
- Storage criptografado em VPS dedicada com retenção máxima 24 meses.

### Fase C — Integração técnica no Mirofish (4 semanas, paralela à B)

Arquivos a criar/estender:

- `backend/app/services/vox_science/calibration_layer.py` (novo, ~300 LoC):
  - `load_human_panel(panel_id)` — lê transcrições anonimizadas + códigos.
  - `inject_into_prompt(prompt_registry, panel_id)` — injeta backstory truncada (≤200 tokens) no campo `biographical_context`.
  - `calibrate_against(synthetic_outputs, panel_id)` — regressão Kambhatla 2025; produz `calibrated_score`.
  - `report_human_calibration_metrics(panel_id)` — gera bloco para `fidelity_report.json` com `human_paired_mae`, `wasserstein_to_human`, `correlation_to_human`.
- `vox_science/artifacts.py`:
  - Aceitar parâmetro novo `human_panel_id` em `build_vox_science_artifacts`.
  - `methodology_manifest.json`: campo `human_collection` migra de `"none_new"` para `"tier_s_n50"` ou `"tier_a_n100"`.
  - `harness_science_gate.json`: liberar `claim_level=C3` somente se `human_paired_mae` < 0.10 e `correlation_to_human` ≥ 0.55.
- Banner UI: substituir "exploratório auditado" por "calibrado com painel humano (n=50, Tier S, ago/2026)" quando aplicável.

### Fase D — Validação cruzada (2 semanas)

- Teste–reteste: subamostra (n=10) responde novamente 4 semanas depois → medir estabilidade humana.
- Teste-cego mantém-se obrigatório: variáveis de validação **nunca** injetadas no prompt.
- Pré-registro em OSF antes de gerar simulações com painel.
- Comparação contra baseline público (Pesquisa Vozes/MGI-Enap, ESEB, ANES) para confirmar plausibilidade externa.

## 4. Recursos necessários

| Recurso | Estimativa | Observação |
|---|---|---|
| Entrevistadores treinados (Tier S) | 3 × 50h = 150h | terceirizar ou treinar internamente |
| Transcrição + codificação | R$ 60–80/h | ~150h × 5 = 750h = R$ 45k–60k |
| Plataforma CEP/CONEP submissão | 30 dias | bloqueador de prazo |
| Storage criptografado | VPS dedicada | R$ 300/mês |
| Tempo Helena/Efesto | 6 semanas Helena (desenho), 8 semanas Efesto (build) | trabalho técnico real |
| Custo total estimado | **R$ 80k–120k** | excluindo tempo interno |

## 5. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Painel n=50 não cobre subgrupos minoritários | IPF/raking sobre marginais Atlas IPEA antes de ativar (R9 que ficou de fora da fase 03) |
| LLM "memoriza" backstory e gera respostas idênticas | temperatura ≥ 0.5 em open items; teste de paráfrases ≥ 3 |
| Custo escala se cliente cancela contrato após coleta | contrato com cláusula de não-reembolso pós-fase B |
| Calibração funciona em domínio A mas não em B | painel separado por domínio; nunca extrapolar entre setores |

## 6. Critérios de "calibração pronta"

Tier S/A só é considerado **operacional** se atingir:

1. n ≥ 50 (Tier S) ou n ≥ 100 (Tier A) com estratificação cumprida.
2. Aprovação CEP/CONEP com parecer favorável final.
3. Teste-cego: variáveis-alvo nunca aparecem no prompt; `recovery_score` ≤ 0.10.
4. `human_paired_mae` < 0.10 em pelo menos 3 construtos diferentes.
5. `correlation_to_human` ≥ 0.55 em construtos não-latentes; ≥ 0.40 em latentes.
6. Pré-registro OSF com timestamp anterior à execução.

Sem todos os 6 critérios, **manter claim em C2** e reportar "calibração em andamento".

## 7. Relação com a Fase 03 (vox-academic-hardening)

A Fase 03 deixa a **infraestrutura técnica pronta** para receber o painel humano:

- `prompt_registry.json` já tem schema `biographical_context` (≤200 tokens).
- `model_run_registry.json` já aceita `replicators[]` para comparar primary vs. calibrated.
- `fidelity_report.json` já tem bloco `multi_metric` (Wasserstein, KL, MAE, DPD) e `blind_test`.
- `claim_policy_audit.json` já declara teto epistêmico 0.50 e bloqueia correlação >0.65 sem evidência.
- `harness_science_gate.json` já bloqueia DPD>0.15 e blind test leak.

Ativar Tier S/A é, do ponto de vista do código, **adicionar `calibration_layer.py`** e passar `human_panel_id` no builder. O resto já existe.

## 8. Referências

- Park, J. S. et al. (2024). *Generative agent simulations of 1,000 people*. arXiv:2411.10109.
- Kambhatla, N. et al. (2025). *Supervised post-hoc calibration of LLM-based silicon samples*. arXiv:2503.03021.
- Bisbee, J. et al. (2024). LLMs as research tools: Replication crisis. *Political Analysis* 32(4).
- Boelaert, J. et al. (2025). Machine bias in LLM-based survey simulations. *Sociological Methods & Research* 54(3).
- Hu, T. & Collier, B. (2024). Bias of personalized LLMs in opinion polling. *ACL Findings*.
- Durelli, V. M. et al. (2017). Validação brasileira da Escala de Suscetibilidade à Persuasão (Br-STPS).
- NIST AI 600-1 (2024); ICC/ESOMAR Synthetic Data Guidelines (2025).

## 9. Próximo passo (não-executar)

Se gatilho for ativado:

1. Helena escreve `docs/superpowers/plans/AAAA-MM-DD-tier-s-decisao-ativacao.md` com o caso de negócio.
2. Igor aprova ou veta.
3. Fase 04 do roadmap é aberta com este documento como anexo de design.
4. Cícero (jurídico) valida TCLE e cláusulas CEP/CONEP antes de qualquer coleta.

**Até lá, este documento permanece dormente.**
