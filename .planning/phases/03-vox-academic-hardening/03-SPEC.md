# SPEC — Fase 03: Vox Academic Hardening

**Versão:** 1.0
**Data:** 2026-05-19
**Modo:** `--auto` (Helena/Efesto)
**Ambiguidade estimada:** 0.12 (≤0.20 ✓)

## 1. Goal travado (falsificável)

## 2. Requisitos funcionais (R)

### R1 — Métricas multi-dimensão em `fidelity_report.json`

**O quê:** O artefato `fidelity_report.json` produzido por `vox_science/artifacts.py` deve incluir, para cada construto avaliado:
- `wasserstein_distance` (float, 0..∞)
- `kl_divergence` (float, 0..∞)
- `mae` (float, 0..1)
- `dpd` (Demographic Parity Difference, dict por par de subgrupos, float 0..1)
- `intra_group_variance` (dict por subgrupo)
- `temporal_stability` (float 0..1, opcional se ausente baseline temporal)

**Falsificável:** Teste unitário que constrói artefato com dados sintéticos conhecidos e verifica que cada campo existe, tem tipo correto, e valor numericamente plausível (faixa esperada documentada no docstring).

### R2 — Blocker DPD em `harness_science_gate.json`

**O quê:** Se qualquer `dpd[par]` em `fidelity_report.json` exceder 0.15, o builder de `harness_science_gate.json` deve definir:
- `science_gate.status = "FAIL"`
- `science_gate.reason = "demographic_parity_violation"`
- `science_gate.violations[]` lista pares e valores ofensores

**Falsificável:** Teste com `fidelity_report` mock cujo DPD=0.20 → gate sai FAIL. Outro com DPD=0.10 → gate PASS.

**O quê:** Todo relatório exportado (MD, HTML, PDF) e a UI do Step4Report.vue devem exibir literalmente:

Localização:
- `executive_package.py`: bloco fixo no início do sumário executivo.
- `report_exporter.py`: rodapé em todos formatos (MD/HTML/PDF).
- `Step4Report.vue`: banner persistente acima do conteúdo do relatório.

**Falsificável:** Grep do texto literal no output de `report_exporter.export_*` e no template Vue. Snapshot test do executive_package HTML.

### R4 — `prompt_hash` + `git_commit_sha`

**O quê:** Em `prompt_registry.json`, cada entrada de prompt deve ter:
- `prompt_hash` (SHA-256 do texto canônico do prompt, hex 64 chars)
- `git_commit_sha` (hash do commit HEAD no momento da geração; null se não git)
- `osf_preregistration_url` (opcional, string url ou null)

**Falsificável:** Teste que constrói dois `prompt_registry` com prompts diferentes → hashes diferentes; com prompts iguais → hashes iguais. Test que valida formato SHA-256.

### R5 — Teto epistêmico em `claim_policy_audit.json`

**O quê:** O artefato `claim_policy_audit.json` deve incluir:
- `latent_construct_ceiling: 0.50`
- `correlation_alert_threshold: 0.65`
- `policy.blocked_claims[]` — lista de claims rejeitados por exceder `correlation_alert_threshold` sem evidência adicional declarada.
- UI Step4Report.vue exibe label "Teto epistêmico declarado: r ≤ 0.50 para construtos latentes".

**Falsificável:** Teste que envia claim com `reported_correlation=0.70` sem `evidence_overrides` → claim em `blocked_claims`. Com `evidence_overrides!=null` → claim permitido. UI exibe rótulo (snapshot Vue).

### R6 — Replicabilidade multi-LLM em `model_run_registry.json`

**O quê:** O artefato `model_run_registry.json` suporta esquema:
```json
{
  "primary_model": {"name": "...", "version": "...", "temperature": ..., "seed": ...},
  "replicators": [{...}, {...}],
  "inter_model_divergence": {"metric": "kl|wasserstein", "value": float, "pairs": [...]}
}
```
- Quando `replicators` vazio: `inter_model_divergence` = null, sem quebra.
- Quando `replicators` ≥1: builder calcula divergência.

**Falsificável:** Teste single-model (replicators=[]) → divergência null, builder não levanta exceção. Teste com 2 modelos diferentes → divergência calculada e ≥0.

### R7 — Schema de prompt biográfico estruturado

**O quê:** `prompt_registry.json` migra para schema:
```json
{
  "prompt_id": "...",
  "biographical_context": "<=200 tokens",
  "role_context": "<=200 tokens",
  "scenario_context": "<=200 tokens",
  "demographic_labels": null | {...}  // opcional, nunca raso
}
```
- Backward compat: builder aceita prompts antigos (formato livre) e os normaliza em `biographical_context` com flag `legacy=true`.

**Falsificável:** Teste alimenta prompt antigo (string única) → builder gera entrada com `legacy=true` e `biographical_context` preenchido. Teste com schema novo → todos 3 campos presentes, cada um ≤200 tokens (validado por contagem).

### R8 — Teste-cego em `fidelity_report.json`

**O quê:** Cada construto em `fidelity_report.json` ganha bloco:
```json
"blind_test": {
  "target_variable": "...",
  "masked_in_prompt": true|false,
  "recovery_score": float 0..1,
  "method": "literal_substring|semantic|regex"
}
```
Builder valida automaticamente que `target_variable` (literal ou variantes morfológicas básicas) NÃO aparece em nenhum dos 3 campos de prompt. Se aparecer → `masked_in_prompt=false` + alerta no `harness_science_gate.violations`.

**Falsificável:** Test com `target_variable="persuadibilidade"` ausente do prompt → masked_in_prompt=true. Mesmo target inserido literal no `scenario_context` → masked_in_prompt=false + violation no gate.

### R10 — Roadmap doc para coleta humana

**O quê:** Arquivo `docs/superpowers/plans/2026-05-19-mirofish-roadmap-coleta-humana-futura.md` descreve plano contingente em 4 fases:
1. Decisão de gatilho (quando coletar)
2. Desenho amostral (n≥50, estratificado)
3. Instrumento (entrevista semi-estruturada 1h, baseado em Park et al. 2024)
4. Integração no Mirofish (camada `calibration_layer.py` ainda não implementada)

**Falsificável:** Arquivo existe, ≥150 linhas, contém as 4 seções, cita Park et al. 2024 + Kambhatla et al. 2025.

## 3. Requisitos não-funcionais (NF)

- **NF1:** `python -m pytest backend/tests -q` verde (0 fails) ao final da fase.
- **NF2:** `cd frontend && npm run build` verde sem warning novo.
- **NF3:** Tempo de build do `fidelity_report` ≤2x do atual (overhead de novas métricas controlado).
- **NF4:** Zero quebra de contrato com runs single-model existentes (E6 retro-compatível).
- **NF5:** Smoke test E2E via Playwright: console limpo (0 error/warning) ao navegar Step1→Step4.

## 4. Fronteiras explícitas (do/don't)

| ✅ Faz | ❌ NÃO faz |
|---|---|
| Estende artefatos JSON existentes | Quebra schema de runs já persistidos |
| Calcula métricas com `scipy.stats` se disponível, fallback puro-Python | Adiciona dependência pesada (numpy só se já presente) |
| Adiciona UI badges/cards no Step4Report | Refatora layout do Step4Report |
| Documenta teto 0.50 em UI/JSON | Bloqueia claims com r≤0.50 (apenas alerta acima 0.65) |
| Suporta replicabilidade multi-LLM opcional | Força ≥2 LLMs como obrigatório |
| Escreve roadmap para coleta humana | Inicia coleta de fato |

## 5. Critérios de aceite (verificação)

Status de "PRONTO" só após todos os 7 critérios:

1. ✅ Todos `pytest` verde, incluindo ≥1 teste novo por requisito R1–R8.
2. ✅ `npm run build` verde, sem warning novo.
3. ✅ Smoke test API: `POST /api/report/...` retorna relatório com 11 artefatos + campos R1–R8 preenchidos.
5. ✅ `docs/MAPA_SISTEMA.md` reflete novos campos.
6. ✅ `README.md` declara "exploratório auditado".
7. ✅ Memórias atualizadas em `MEMORY.md`, `CONTEXTO_ATIVO.md`, `.planning/STATE.md`, `.planning/LEARNINGS_VOX_ACADEMIC_HARDENING.md`.

## 6. Ambiguidade scorecard (auto-avaliação)

| Dimensão | Min | Score | OK |
|---|---|---|---|
| Goal clarity (o que entrega) | 0.85 | 0.92 | ✓ |
| Acceptance criteria (como medir pronto) | 0.85 | 0.94 | ✓ |
| Boundary definition (do/don't) | 0.80 | 0.90 | ✓ |
| Dependency awareness (o que precede/segue) | 0.75 | 0.88 | ✓ |
| **Total ambiguidade residual** | **≤0.20** | **0.12** | **✓** |

## 7. Riscos e mitigações

- **R-risc-1:** scipy não disponível na VPS de produção → fallback puro-Python para Wasserstein/KL (implementação O(n log n)).
- **R-risc-2:** LLMs secundários (replicators) podem custar tokens → E6 opt-in, default desabilitado em produção.
- **R-risc-3:** Hook de acentuação PT-BR pode bloquear edits — usar `--fix` antes em arquivos pré-existentes.
- **R-risc-4:** Migration de schema de prompt antigo pode quebrar runs persistidos — flag `legacy=true` preserva.

## 8. Próximo passo

