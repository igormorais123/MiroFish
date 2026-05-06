# OpenSwarm -> Mirofish: oportunidades uteis

Data: 2026-05-06

Fonte estudada:

- Repositorio: https://github.com/VRSEN/OpenSwarm
- Commit remoto confirmado: `92c8062bfeb58a9e96db8b7ac72da5f95c33479e`
- Transcricao do video fornecida pelo Igor na conversa

## Tese

Nao vale importar o OpenSwarm inteiro para o Mirofish. O Mirofish ja tem uma inteligencia propria mais valiosa: simulacao social, gate de entrega, auditoria de evidencias, livro de previsoes, cadeia de custodia e governanca cliente/demo.

O que vale importar sao padroes de produto:

1. Entregaveis reais como saida de primeira classe.
2. Fonte HTML canonica para documentos e slides.
3. Validacao visual e estrutural antes de exportar.
4. Separacao por especialistas sem transformar o produto em uma agencia generica.
5. Pacotes finais versionados com snapshots e manifesto.
6. Preflight claro de capacidades antes de rodar trabalho caro.

## Onde o OpenSwarm e forte

### 1. Entregaveis completos

OpenSwarm vende a promessa "um prompt -> pacote completo": pesquisa, graficos, slides, documento executivo e assets.

No Mirofish, a promessa equivalente deve ser:

```text
simulacao auditavel -> relatorio publicavel -> pacote executivo verificavel
```

Hoje o Mirofish ja tem `full_report.md`, artefatos JSON, `mission_bundle.json`, `forecast_ledger.json`, `cost_meter.json` e cadeia de custodia na UI. Falta transformar isso em formatos de entrega executiva: PDF, DOCX e, depois, deck.

### 2. HTML como fonte canonica

O Docs Agent do OpenSwarm cria `.source.html` e converte para DOCX/PDF/Markdown/TXT. O Slides Agent cria HTML por slide e exporta para PPTX.

Isso agrega muito ao Mirofish porque o relatorio atual nasce em Markdown. Markdown e bom para auditoria textual, mas limitado para entrega cliente. Um caminho melhor:

```text
full_report.md + artifacts JSON -> report.source.html -> PDF/DOCX -> manifest/hash
```

O Markdown continua sendo a fonte auditavel textual. O HTML vira a fonte canonica de layout para entrega.

### 3. Validacao visual

OpenSwarm renderiza slides com Playwright, cria thumbnails, checa overflow de canvas e valida HTML/CSS antes de converter.

No Mirofish, o equivalente e uma camada `deliverable_quality`:

- renderizar `report.source.html` em screenshot;
- detectar paginas em branco, blocos ausentes, texto estourando e tabelas largas;
- garantir que cadeia de custodia, auditoria de evidencias e disclaimer de `diagnostic_only` aparecem no export;
- bloquear export cliente quando o relatorio nao e `publishable`.

### 4. Orquestrador que roteia, nao executa

OpenSwarm separa o orquestrador dos especialistas. O Mirofish nao precisa de um runtime de swarm, mas pode usar a mesma disciplina dentro do ReportAgent.

Proposta:

- `Evidence Curator`: monta pacote de evidencias e limites.
- `Scenario Analyst`: escreve cenarios e previsoes a partir do ledger.
- `Red Team`: procura claims sem suporte, excesso de certeza e contradicoes.
- `Deliverable Builder`: transforma relatorio aprovado em HTML/PDF/DOCX/deck.

Isso pode ser implementado como contratos internos e modulos, nao como agentes autonomos novos.

### 5. Subtarefas isoladas por slide/secao

O Slides Agent usa uma etapa de planejamento e depois gera cada slide separadamente com brief autocontido. O Mirofish ja salva secoes por arquivo. A melhoria e formalizar um `section_packet`:

```json
{
  "section_title": "",
  "allowed_evidence_ids": [],
  "required_metrics": [],
  "forbidden_claims": [],
  "expected_output": "",
  "audit_rules": []
}
```

Cada secao fica mais facil de regenerar, auditar e explicar na UI.

## Melhorias recomendadas para o Mirofish

### P1. Exportador executivo auditavel

Criar um servico de export:

```text
backend/app/services/report_exporter.py
```

Responsabilidades:

- ler `ReportManager.get_report(report_id)`;
- ler artefatos JSON existentes;
- montar `report.source.html`;
- exportar PDF e DOCX;
- salvar snapshots versionados;
- gravar `export_manifest.json` com hashes, status e caminhos;
- recusar export cliente se `delivery_status != publishable`.

Endpoints sugeridos:

```text
POST /api/report/<report_id>/export
GET  /api/report/<report_id>/exports
GET  /api/report/<report_id>/exports/<filename>
```

Primeiro formato: PDF. Depois DOCX. Deck vem depois.

### P2. QA visual do relatorio

Criar:

```text
backend/app/services/report_visual_quality.py
```

Checks iniciais:

- HTML renderiza sem erro;
- screenshot existe e nao esta em branco;
- contem blocos obrigatorios: titulo, resumo, secoes, auditoria de evidencias, cadeia de custodia;
- quando `diagnostic_only`, o export precisa exibir o rotulo de diagnostico;
- quando `publishable`, o export precisa exibir hash/manifesto.

Saida:

```text
report_visual_quality.json
report_preview.jpg
```

### P3. Graficos deterministas a partir da simulacao

OpenSwarm usa o Data Analyst para gerar graficos. O Mirofish deve evitar graficos inventados e gerar visualizacoes deterministicas dos artefatos locais:

- acoes por rodada;
- diversidade semantica;
- entropia por agente;
- tipos de acao;
- previsoes congeladas;
- custo por fase.

Esses graficos entram no `report.source.html` e futuramente no deck.

### P4. Deck executivo curto

Depois do export PDF/DOCX, criar um deck de 6 a 8 slides a partir do relatorio aprovado:

1. Contexto da missao.
2. Como a simulacao foi montada.
3. Sinais sociais observados.
4. Tres cenarios.
5. Previsoes congeladas.
6. Riscos e sinais de monitoramento.
7. Cadeia de custodia.
8. Proxima decisao recomendada.

Nao usar deck antes do gate. Deck e produto de relatorio aprovado, nao substituto de evidencia.

### P5. Preflight de capacidades antes da simulacao longa

OpenSwarm mostra integracoes disponiveis e chaves ausentes. Mirofish precisa de um painel/preflight para P0.1:

- LLM configurado;
- Graphiti/Zep disponivel ou fallback declarado;
- Apify token presente quando enriquecimento for usado;
- OASIS pronto;
- estimativa de custo e tempo;
- status `client`, `demo` ou `smoke`;
- risco de nao publicabilidade antes de iniciar.

Isso reduz simulacoes caras que terminam bloqueadas por configuracao previsivel.

## O que nao importar agora

- Runtime multiagente completo.
- Composio e 10.000 integracoes externas.
- Video/image agents.
- Setup wizard que instala dependencias automaticamente.
- Handoff livre entre todos os agentes.
- Geração de assets visuais genericos.

Esses pontos aumentariam superficie de risco sem atacar o gargalo atual do Mirofish: transformar simulacao aprovada em entrega executiva verificavel.

## Primeiro PR recomendado

Implementar apenas o nucleo de export PDF auditavel:

```text
report markdown + artefatos -> HTML -> PDF + preview + export_manifest
```

Escopo pequeno:

- novo servico `report_exporter.py`;
- um endpoint `POST /api/report/<report_id>/export`;
- testes unitarios para:
  - bloqueia relatorio nao publicavel em modo cliente;
  - gera HTML com blocos obrigatorios;
  - cria manifesto com hashes;
  - preserva `diagnostic_only` no export demo.

Nao precisa de LLM, Apify, Graphiti ou simulacao nova para testar.

## Resultado esperado

O Mirofish deixa de entregar apenas "um relatorio na tela" e passa a entregar um pacote consultivo:

```text
Relatorio publicavel
+ PDF executivo
+ manifesto/hash
+ preview visual
+ anexos de evidencia
+ depois: DOCX e deck
```

Essa e a adaptacao de maior ROI do OpenSwarm: menos "swarm", mais entregavel profissional auditavel.

