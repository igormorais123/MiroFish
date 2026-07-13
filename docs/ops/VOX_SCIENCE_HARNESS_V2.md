# Vox Science Harness v2

Data: 2026-07-13
Status: contrato de verdade C1-C4 implementado

## Objetivo

O Vox Science Harness v2 adiciona uma camada cientifica auditavel ao MiroFish sem
exigir entrevistas novas, questionarios novos, painel humano ou calibracao humana
adicional.

A regra operacional permanece:

- usar dados publicos;
- usar ativos internos ja existentes;
- registrar prompts, modelos, fontes e limites de claim;
- entregar linguagem forte e executiva, com gate interno controlando a forca do
  claim.

## Artefatos produzidos

Cada relatorio novo pode receber 11 artefatos Vox Science:

| Artefato | Papel |
|---|---|
| `methodology_manifest.json` | Escopo, populacao, decisao, restricao de coleta e claim alvo. |
| `baseline_registry.json` | Catalogo de fontes e estado do snapshot carregado. URL/catalogo sozinho e apenas metadado. |
| `public_data_anchors.json` | Variaveis ancoradas, fonte, papel e confianca. |
| `prompt_registry.json` | Perguntas, constructos, parafrases, schema e contexto proibido. |
| `model_run_registry.json` | Modelo, politica de temperatura, seeds e hashes. |
| `synthetic_interviews_manifest.json` | Unidades sinteticas, acoes observadas e matriz minima recomendada. |
| `fidelity_report.json` | Score, variancia, erro externo quando existir e modo de medicao. |
| `pimmur_audit.json` | Profile, Interaction, Memory, Minimal-Control, Unawareness, Realism. |
| `compost_audit.json` | Separacao de benchmark/outcome e risco de contaminacao. |
| `claim_policy_audit.json` | Nivel C0-C4, linguagem permitida e linguagem bloqueada. |
| `harness_science_gate.json` | Autoridade final: passe de execucao separado do nivel de claim. |

## Niveis de claim

| Nivel | Uso |
|---|---|
| C0 | Mapa qualitativo de sinais e friccoes sinteticas. |
| C1 | Trace sintetico executado, sem calibracao externa medida. E o teto de toda chamada legada. |
| C2 | Snapshot e pacote de avaliacao locais autorizados; MAE, KL e Wasserstein finitos, recalculados sobre dimensoes rotuladas comparaveis e dentro dos limiares declarados (atualmente <= 0.15 para cada metrica). |
| C3 | C2 ja aprovado nos limiares, mais 3 ou mais runs materializados com IDs/seeds unicos, estabilidade >= 0.70 e erro <= 0.15 de todos os subgrupos (minimo de 2, n >= 30). |
| C4 | C3 mais forecast por ID materializado antes dos outcomes, recibo host-only emitido antes do cutoff, heldout n >= 30 disjunto do treino e metricas recalculadas do forecast precomprometido contra outcomes posteriores. |

`passes_execution_gate` responde somente se pipeline, trace e artefatos passaram.
Ele nunca implica calibracao. O campo antigo `passes_gate` permanece apenas como
alias documentado de `passes_execution_gate`. Consumidores devem obter o nivel
exclusivamente da projecao autenticada do servidor. Um gate autenticado, atual e
com `passes_execution_gate=false` e C0 bloqueado. Gate ausente, adulterado,
desancorado ou inconsistente nao recebe nivel de claim (`claim_level=null`).

## Autoridade materializada

Os contratos fechados e versionados ficam em `baseline-snapshot.schema.json`,
`claim-evidence.schema.json`, `claim-evidence-authority.schema.json`,
`stability-run.schema.json`, `replicator-input.schema.json`,
`preregistered-forecast.schema.json`, `verified-claim-projection.schema.json` e
`preregistration-receipt.schema.json`. O backend
define a raiz por `VOX_CLAIM_EVIDENCE_ROOT` e o hash do manifesto canonico por
`VOX_CLAIM_AUTHORITY_MANIFEST_SHA256`. O chamador nao escolhe raiz nem hashes de
autoridade. O manifesto aprova os hashes exatos do snapshot e do pacote de
evidencias. Sem essa cadeia, o teto e C1.

Autenticidade e protecao contra replay usam `VOX_CLAIM_SIGNING_KEY` (segredo do
host com no minimo 32 bytes) e `VOX_CLAIM_VERIFICATION_STATE_ROOT` (raiz absoluta
local). A chave nunca entra em JSON, log ou repositorio. Gate sem HMAC valido,
chave ausente/curta ou ancora corrente ausente gera `verified=false` e nenhum
claim. C1 existe apenas para trace sintetico autentico que passou a execucao sem
evidencia suficiente para C2.

O runtime exige:

- arquivo JSON local relativo a uma raiz confiavel; caminhos absolutos, `..`,
  symlink, junction/reparse point, hardlink e arquivo nao regular sao rejeitados;
- bytes JSON canonicos e SHA-256 exato autorizado pelo manifesto configurado;
- schema/version, dominio, populacao, periodo, fonte, proveniencia, data de
  captura, variaveis, unidades, categorias, subgrupos e tamanhos amostrais;
- distribuicoes ou linhas numericas finitas, sem booleanos, strings numericas,
  NaN/Infinity, massa zero, categorias duplicadas ou dimensoes divergentes;
- toda distribuicao de probabilidade em baseline, avaliacao, subgrupo, run e
  forecast deve ser nao negativa e somar `1 +/- 1e-6`; escala percentual
  (`100`) ou contagens (`10`) e rejeitada, sem normalizacao silenciosa;
- limites de bytes, profundidade JSON, nos, strings, linhas, variaveis,
  subgrupos e vetores antes do calculo;
- replicadores em schema fechado: no maximo 32 entradas, nome e versao com ate
  128 caracteres, distribuicoes com ate 256 numeros finitos e texto de resposta
  com ate 4096 caracteres; excesso falha fechado em C0 antes de metricas caras;
- pacote vinculado a report, simulation, run, config, input, snapshot e sample;
- C2 com no minimo 30 IDs de avaliacao distintos, labels/categorias vinculados
  e MAE/KL/Wasserstein categorial dentro dos limiares <= 0.15;
- C3 com cada run/seed em arquivo separado autorizado pelo manifesto, no minimo
  30 IDs por run e por predicao de subgrupo; arrays em memoria sao diagnosticos;
- C4 com forecast estrito por heldout ID materializado antes do cutoff. O emissor
  host-only usa seu proprio relogio, grava uma unica vez o recibo sob a raiz de
  estado e vincula hash/caminho exatos do forecast. Depois, o pacote fornece
  somente outcomes observados; distribuicoes previstas e metricas sao
  recalculadas do forecast precomprometido. A validacao prospectiva preserva o
  mapa forecast por ID e usa `multiclass_brier_log_loss_per_id.v1`: Brier score
  multiclasses e log loss por heldout. Antes do cutoff, o recibo host-only
  assinado congela a politica reconhecida `vox-c4-material-v1`, com
  `minimum_brier_skill_score` default e piso absoluto `0.05` e
  `maximum_log_loss_ratio` default e teto absoluto `0.99` contra a distribuicao
  constante do baseline. O emissor aceita somente criterios iguais ou mais
  estritos; `0.01`, ratio `1.0` e `policy_id` desconhecido sao rejeitados mesmo
  quando assinados. C4 exige simultaneamente o piso de skill e o
  teto de ratio registrados naquele recibo; criterio inserido ou relaxado
  depois do outcome e ignorado/rejeitado. MAE, KL e Wasserstein marginais continuam suplementares
  e obrigatorios, mas jamais promovem C4 sozinhos. Predicao inserida pos-outcome
  e rejeitada. Status `measured` declarado no mesmo pacote nunca basta sozinho.

Esses pisos pre-registrados sao um filtro de efeito material operacional. Nao
sao significancia estatistica, intervalo de confianca nem margem de erro; o
harness nao publica nenhum desses claims sem calculo especifico.

Para vetores de massa categorica rotulada, Wasserstein usa
`categorical_wasserstein_declared_order.v2`: distancia W1 discreta pela soma das
diferencas absolutas das CDFs ao longo da ordem de categorias declarada. Os
valores nunca sao ordenados por magnitude. `wasserstein_1d` por quantis permanece
reservado a amostras escalares sem rotulos.

Snapshots `data.kind=rows` continuam validos como entrada/catalogo, mas o
contrato atual de calibracao C2+ aceita somente `data.kind=distributions`, com
massas rotuladas. Rows recebem o blocker
`row_baseline_probability_metrics_not_implemented` e teto C1 ate existir metrica
separada apropriada para observacoes linha a linha.

O carregamento usa uma unica abertura, compara identidade/tamanho/mtime antes e
depois e revalida o caminho antes de promover claim. Falha ou adulteracao gera
blocker explicito e limita a C1; nao vira metrica perfeita por sentinela.

## Integração no backend

Pontos implementados:

- `backend/app/services/vox_science/artifacts.py`: builders deterministas dos
  artefatos P0.
- `backend/app/services/report_agent.py`: salva os artefatos no fim da geracao do
  relatorio, depois de auditoria/forecast e antes do `mission_bundle`.
- `backend/app/services/harness_evidence_bundle.py`: expõe `methodology` e
  `qualityGates` no contrato interno do harness.
- `backend/app/services/report_method_checklist.py`: reconhece os artefatos Vox
  Science como parte do checklist metodologico.
- `backend/app/services/executive_package.py`: inclui os artefatos Vox Science
  no anexo de evidencias do pacote executivo.
- `backend/app/services/report_exporter.py`: inclui os artefatos Vox Science no
  anexo de evidencias da exportacao HTML.

Os 11 artefatos recebem o mesmo `generation_id`. O gate final vincula report,
simulation, run, config, input e hashes da autoridade, carrega hashes canonicos
dos outros dez e recebe HMAC-SHA256 sobre o payload completo. A gravacao e preparada em temporarios, rejeita
NaN/Infinity, promove cada arquivo por troca atomica e promove o gate por ultimo.
Depois do gate, uma ancora HMAC por relatorio torna a geracao corrente. Falha
entre gate e ancora deixa o gate novo nao verificavel; a ancora antiga nunca
autoriza replay. Consumidores reabrem manifesto, snapshot e evidencias sob a
raiz fixa e recusam geracoes misturadas, adulteradas ou de outro relatorio. A API de artefatos expoe
somente `verified_vox_claim` como projecao de claim; a interface nao confia nos
campos crus de gate, policy ou methodology. Sem verificacao, mostra "sem claim";
um C0 autentico mostra "Bloqueado". Em ambos, metricas, fontes e linguagem de
claim dos JSONs crus ficam ocultas. Se a geracao falhar, um
gate C0 explicito substitui qualquer gate antigo para impedir reuso de C2+ stale.

### Limite de rollback administrativo

HMAC, recibos e ancoras assumem ACLs e integridade do host para as raizes de
evidencia e estado. Eles impedem adulteracao comum e replay cruzado, mas nao
fornecem monotonicidade contra um administrador capaz de restaurar de forma
coordenada uma copia antiga valida de todos os arquivos e do estado. Esse modelo
de ameaca exige ledger externo append-only, storage WORM ou timestamping remoto;
permanece explicitamente fora do escopo desta implementacao local.

### Rotacao da chave do host

O contrato atual usa uma unica `VOX_CLAIM_SIGNING_KEY`. Sua rotacao invalida
gates, ancoras e recibos historicos assinados pela chave anterior. Para manter
um artefato historico verificavel, ele precisa ser reemitido e reancorado sob a
nova chave a partir das evidencias materializadas. Rotacao transparente por
`key_id`/keyring ainda nao existe; e uma migracao futura, nao uma garantia atual.

## Integração no frontend

`frontend/src/components/Step4Report.vue` exibe um painel leve `Vox Science` na
tela de relatorio:

- status autenticado do science gate;
- claim C0-C4 apenas quando a projecao foi verificada;
- linguagem maxima permitida;
- quantidade de artefatos;
- score de fidelidade;
- variancia;
- PIMMUR;
- quantidade de baselines;
- indicador de que nao houve coleta humana nova;
- fontes publicas principais;
- alertas do gate.

O painel usa somente `verified_vox_claim` para status, claim e linguagem. Os
JSONs completos continuam disponiveis para auditoria, mas seus detalhes nao sao
renderizados quando a projecao e nao verificada, C0 bloqueada ou C1 apenas
diagnostica. Metricas/fontes de calibracao aparecem somente em C2+ com
`calibration_mode=materialized_external_baseline`.

Enums publicos de `calibration_mode`:

- `unverified_no_calibration`: projecao nao verificada ou C0 bloqueada;
- `synthetic_trace_only`: C1 autentico com execucao aprovada, sem calibracao externa;
- `materialized_external_baseline`: C2-C4 autenticado, ancorado e reaberto sob autoridade.

## Regras de segurança metodológica

- Outcome usado para validacao nao entra em nenhum campo, parafrase, schema ou
  metadado prompt-bearing; aliases normalizados tambem sao verificados.
- `new_human_collection` deve ser `false` neste modo.
- Linguagens bloqueadas incluem "margem de erro amostral", "resposta humana
  coletada" e claims populacionais fortes sem baseline.
- Forecast planejado, chave de configuracao, `allowed_for_validation` e override
  truthy nao promovem claim.
- `qualityGates` secundarios sao diagnosticos e nunca aparecem como aprovados
  quando o gate final autenticado nao foi verificado.
- Relatorios antigos podem aparecer como `legacy`, `partial` ou `blocked` e nao
  sao tratados como calibrados.

## Comandos de validação

Backend completo:

```powershell
cd backend
uv run --frozen python -m pytest -q
```

Frontend:

```powershell
cd frontend
npm run build
```

Dev local usado na validação:

```powershell
npm run backend
cd frontend
npx vite --host localhost --port 5173
```

Portas observadas:

- backend: `http://localhost:5001`
- frontend: `http://localhost:5173`

## Uso atual

A integracao de producao ainda chama o builder sem artefatos autorizados; portanto
produz legitimamente C1. Para C2+, a operacao deve materializar snapshot e pacote,
registrar seus hashes no manifesto canonico e configurar a raiz/hash do manifesto
no backend. Nao ha fetch externo nem API paga neste fluxo.
