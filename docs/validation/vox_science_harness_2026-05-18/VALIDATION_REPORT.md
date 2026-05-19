# Validacao Vox Science Harness

Data: 2026-05-18
Ambiente: local Windows, backend Flask em `5001`, frontend Vite em `5173`
Relatorio usado: `report_c7762071893d`
Simulacao usada: `sim_0bcb282507ec`

## Escopo validado

1. Builders dos artefatos Vox Science.
2. Integracao no fim da geracao de relatorio.
3. Contrato interno do evidence bundle.
4. Checklist metodologico.
5. Inclusao dos artefatos Vox Science nos anexos de exportacao/pacote executivo.
6. Painel Vox Science na tela de relatorio.
7. Rotas principais do frontend.

## Medicao antes/depois

| Medida | Antes | Depois |
|---|---:|---:|
| Artefatos Vox Science reconhecidos no harness | 0 | 11 |
| Artefatos auditaveis no caso `report_c7762071893d` | 9 | 20 |
| Testes dedicados a Vox Science | 0 | 16 |
| Testes backend totais passando | nao medido nesta rodada | 320 |
| Campos novos no evidence bundle interno | 0 | 2 (`methodology`, `qualityGates`) |
| Painel visual de science gate no frontend | ausente | presente |

Observacao: os 9 artefatos "antes" sao os JSONs auditaveis existentes no
relatorio, excluindo `meta.json`, `outline.json` e `progress.json`. Depois da
materializacao local foram adicionados os 11 artefatos Vox Science.

## Resultado do caso local

O relatorio antigo de demonstracao recebeu os artefatos Vox Science para
validacao visual. Como e uma demo curta com 5 perfis e 20 acoes, o gate classificou
corretamente como C1:

| Campo | Valor observado |
|---|---|
| `harness_science_gate.passes_gate` | `true` |
| `claim_level` | `C1` |
| Linguagem maxima | `simulacao sintetica exploratoria com rastreabilidade metodologica` |
| Artefatos Vox Science | 11 |
| `fidelity_report.overall_score` | 0.3159 |
| `fidelity_report.variance_ratio` | 0.7766 |
| `pimmur_audit.score` | 1.0 |
| Baselines | 3 |
| Nova coleta humana | `false` |

Isso e o comportamento esperado: a camada metodologica nao supervende uma demo
curta como C2/C3, mas preserva o valor de simulacao exploratoria rastreavel.

## Validação de backend

Comandos executados:

```powershell
cd backend
python -m pytest tests/test_vox_science_artifacts.py tests/test_internal_harness_api.py tests/test_report_method_checklist.py -q
python -m pytest tests -q
```

Resultado:

- suite focada: 25 passed;
- suite export/pacote/verificador: 22 passed;
- suite completa backend: 320 passed.

## Validação de frontend

Build:

```powershell
cd frontend
npm run build
```

Resultado:

- build concluido;
- CSS final observado: 211.37 kB;
- JS principal observado: 1,053.00 kB;
- avisos existentes de chunk grande e import do Mermaid foram mantidos.

Rotas validadas no navegador:

| Rota | Resultado |
|---|---|
| `/` | app carregado, home renderizada. |
| `/process/proj_d4e391d586a4` | Step 1 carregado. |
| `/simulation/sim_0bcb282507ec` | Step 2 carregado. |
| `/simulation/sim_0bcb282507ec/start` | Step 3 carregado. |
| `/report/report_c7762071893d` | Step 4 carregado; painel Vox Science presente. |
| `/interaction/report_c7762071893d` | Step 5 carregado; ferramentas de interacao presentes. |

No `/report/report_c7762071893d`, o navegador confirmou:

```text
VOX SCIENCE
APROVADO C1
CLAIM MAXIMO
simulacao sintetica exploratoria com rastreabilidade metodologica
C1
ARTEFATOS 11
FIDELIDADE 0.32
VARIANCIA 0.78
PIMMUR 1.00
BASELINE 3
COLETA NOVA Nao
TSE Dados Abertos
ESEB/CESOP 2022
IBGE Censo 2022
```

## Achados durante a validação

1. O relatório antigo aparece como `Entrega bloqueada` no pacote de entrega
   porque ja tinha `evidence_audit.json` reprovado e nao tinha
   `decision_packet.json`. Isso e estado legado do caso de teste, nao regressao
   do Vox Science.
2. O frontend em `3000` e `3001` retornou `EACCES` no Windows. A validacao foi
   feita em `5173`.
3. O navegador interno carregou as paginas e leu DOM/estado corretamente, mas a
   captura de screenshot por CDP deu timeout. A validacao funcional foi feita por
   DOM e logs.
4. Havia erros HTTP 409 ligados ao estado bloqueado do pacote antigo; nao houve
   `ReferenceError`, `TypeError`, `SyntaxError` ou componente Vue quebrado.

## Conclusão

O vertical slice P0 esta operacional: backend gera artefatos, checklist reconhece,
bundle interno expõe metodologia/gates e frontend mostra readiness cientifico no
fluxo de relatorio.

O proximo avanço real e instrumentar respostas por matriz `paraphrase x seed`
para elevar o `fidelity_report` de modo baseado no rastro da simulacao para modo
baseado em robustez experimental.
