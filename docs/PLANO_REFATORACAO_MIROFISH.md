# Plano de refatoração do MiroFish — versão consolidada

> Documento canônico de execução. Consolida o diagnóstico do caso Vale Trading, o
> plano de calibração jurídica e a reforma da camada de LLM numa única ordem de
> trabalho. Substitui os planos parciais anteriores.
>
> Data: 2026-07-26 · Executor: Claude Opus · Worktree: `_worktrees/mirofish-helena-control`

## Estado da execução

| Fase | Situação | PR |
|---|---|---|
| Camada de LLM — assinatura Codex, Luna/Sol | **concluída** | #101 |
| Performance — delta de ações, copiloto | **concluída** | #102 |
| **F0** — parar de fabricar confiança (10 itens) | **concluída** | #103 |
| **F1** — ingestão paginada, pincite, gate anti-eco | **concluída** | #104 |
| **F2** — ontologia processual, postura parametrizada | **concluída** | #104 |
| **F3** — conversa | destrava com F1+F2; falta rodar e verificar | — |
| **Ponte F1→F4** — aresta tipada e atributo na extração | **concluída** | #104 |
| **F4** — cronologia, omissões, cobertura, contradições, valor da informação | **concluída** | #104 |
| **F5** — simulação atrás de gate de validação | **concluída** | #104 |

Nenhum PR foi mergeado: o CI do GitHub Actions está travado por faturamento da
conta, e o check é obrigatório. O #104 está empilhado sobre o #101 e precisa
entrar depois dele.

---

## 1. O reposicionamento

O sistema foi construído para **difusão de opinião** e apontado para um **processo
judicial**. Num processo não há difusão: há um decisor único e um conjunto fechado
de documentos. Daí os priors de servidores federais, o HHI de atores e a entropia
como métrica de convicção.

A máquina de agentes **não** serve para prever comportamento judicial — isso não é
validável, e um simulador não validado gera confiança falsa com aparência
sofisticada. Ela serve para **gerar o contraditório**: produzir os argumentos que a
outra parte vai levantar, ancorados no grafo do caso.

Essa diferença é o que torna o produto auditável. Ninguém verifica se "72% de
probabilidade de êxito" está certo. Todo advogado julga se um argumento adversarial
é bom e se a resposta a ele existe nos autos.

**O MiroFish deixa de ser um simulador de opinião e passa a ser memória
interrogável de processo volumoso, com proveniência, e máquina de contraditório
antecipado sobre ela.**

Isso não é invenção de produto: o protocolo da fábrica de petições já exige, hoje
feito à mão — *"antes de redigir em processo volumoso, criar cronologia auditada e
grafo dos atos; cada recurso, decisão, retratação, destaque e intimação recebe
identificador próprio, data, sujeito, ato impugnado, pedido, efeito jurídico e
ponte exata para os autos"*. O gargalo do escritório não é opinar: é saber o que
existe nos autos e onde.

---

## 2. O achado que reorganiza a prioridade

As quatro ferramentas de conversa — `insight_forge`, `panorama_search`,
`quick_search`, `interview_agents` — leem todas do mesmo grafo. O grafo veio com
0 nós e 0 arestas, e por isso as quatro falharam juntas.

**Não são quatro defeitos. É um.** Consertar a ingestão acende as quatro sem tocar
em nenhuma delas — é o maior retorno por esforço do sistema inteiro.

E há um segundo defeito, independente, que impede qualquer resultado de ser
confiável: o sistema é **estruturalmente incapaz de dizer "não sei"**.

```python
# decision_packet.py:80
base_probability_percent = int(round(46 + 24 * conviction))
conviction = round(_clamp(raw_conviction, 0.35, 0.92), 4)
```

A "probabilidade de êxito" é função linear afim de uma média ponderada de
entropias de tweets. Com a convicção travada em [0.35, 0.92], o número só existe
entre **54% e 68%** — mesmo com grafo vazio e zero fatos ancorados. E
`knowledge_backing`, o único componente que mede substância, pesa 0,15, com
`source_scale = 1.0` a partir de 500 caracteres de fonte.

---

## 3. As fases

### F0 — Parar de fabricar confiança

Remoção e configuração. Sem isto, tudo que as fases seguintes produzirem continua
sendo publicado com números inventados por cima.

| # | Item | Arquivo | Estado |
|---|---|---|---|
| 0.1 | Corpus lido inteiro, em pedaços sobrepostos e paralelos | `llm_entity_extractor.py` | **feito** |
| 0.2 | Entidades com trecho verbatim e offset; não-ancoradas marcadas | `llm_entity_extractor.py` | **feito** |
| 0.3 | Queda do Graphiti deixa de ser silenciosa e avisa o modelo | `zep_tools.py` | **feito** |
| 0.4 | Gate barra grafo sem nós ou sem arestas | `report_system_gate.py` | **feito** |
| 0.5 | Matar `conviction_operational` e `base_probability_percent` | `decision_packet.py` | **feito** |
| 0.6 | Remover a regra `method_lock` que obriga divulgá-los | `decision_packet.py` | **feito** |
| 0.7 | `applies: False` pontua zero e sinaliza, nunca 1,0 | `strategic_density_gate.py` | **feito** |
| 0.8 | Desligar priors de servidores federais | `vox_science/artifacts.py` | **feito** |
| 0.9 | Política de nomeação: órgão real nunca vira perfil que emite falas | `entity_naming.py` | **feito** |
| 0.10 | Declarar truncamento de rodadas como limitação, não duração nominal | `report_agent.py` | **feito** |

O item 0.9 é exposição jurídica, não estética: fala sintética atribuída a juízo
federal, persistida em banco, é passivo se migrar para artefato externo.

### F1 — Ingestão real com proveniência processual — **feito**

O que a F0 entregou ancora por offset de caractere. Falta a âncora que o escritório
usa: **evento, página, trecho**.

- Ingerir os PDFs **paginados**, não concatenados.
- Cada entidade e cada fato carregam `doc_id`, `evento`, `página`, `trecho`.
- **Gate anti-eco:** fato retornado que seja substring do prompt não conta como
  recuperado. No ciclo Vale, o `quick_search` devolveu 11 mil caracteres ecoando o
  próprio prompt sob o carimbo "Origem: parâmetros documentados no pedido".
- Run que termina com zero fatos ancorados **aborta** em vez de gerar relatório.

### F2 — Ontologia processual — **feito**

A ontologia existe e funciona; está apontada para o domínio errado. Troca de
vocabulário, não reconstrução.

- Entidades: `Evento · Documento · Tese · Norma · Valor · Diligência`
- Arestas: `sustenta · contradiz · depende_de · foi_omitido_em`

É o que permite ao grafo responder *quais teses ficam órfãs se o documento X não
vier*.

### F3 — Conversa

Destrava sozinha quando F1 e F2 estiverem de pé. Nenhuma das quatro ferramentas
precisa ser alterada.

### F4 — Produtos do escritório — **feito**

A saída deixa de ser um relatório sobre o sistema. Passa a ser:

1. **Cronologia auditada** dos atos, com ponte para os autos.
2. **Matriz de omissões por fundamento autônomo** — era o eixo dos embargos do
   evento 239.
3. **Matriz de cobertura documental**, guia a guia.
4. **Mapa de contradições** entre as próprias peças.

Mais o que substitui a probabilidade fabricada: **valor da informação** — para cada
tese, qual documento a sustenta, qual falta, quanto custa obter, o que muda se vier.

**Postura parametrizada:** `assistente_da_parte | perito_do_juízo | red_team`,
rodando as três. A consulta encerrava com ordem expressa — *"a IA deve atuar como
perito assistente da parte"* — e o sistema entregou perito do juízo, com veredito
de não-promoção: correto sobre o quantum, adverso ao cliente.

**Na interface**, o fluxo de cinco passos permanece; muda o significado. Step 1 vira
"Montar o caso", Step 5 vira "Interrogar os autos", o GraphPanel vira linha do tempo
dos atos. O acréscimo decisivo é **clicar num fato e abrir o PDF na página exata** —
é o que separa "a IA disse" de "está na fl. X".

### F5 — Simulação social, opcional e atrás de gate — **feito**

Rebaixada a opcional. Continua no produto para os domínios em que nasceu:
eleitoral, reputacional, difusão de narrativa. Para litígio, só com validação
declarada.

---

## 4. Camada de LLM — concluída

Executada antes deste plano; é o que torna a F1 viável.

O corpus era truncado em 8000 caracteres em parte **porque processá-lo inteiro era
caro**: o gateway OmniRoute tinha `max_concurrent = 1` na única conta viva, e todas
as chamadas do sistema disputavam essa fila.

Hoje: ponte HTTP local que traduz `/v1/chat/completions` para `codex exec`,
atendendo pela assinatura. Medido nesta máquina — 16 chamadas concorrentes,
16/16 sucesso, ~40 chamadas/min. Roteamento: Luna move todo o volume (agentes,
relatório), Sol fica onde a Helena decide operação. Teto por seção do relatório
subiu de 4096 para 16000 tokens.

Ler nove PDFs em pedaços deixou de ser proibitivo e passou a ser questão de minutos.

---

## 4.1 O que a execução real corrigiu

Três defeitos que nenhum teste sintético expôs, todos encontrados rodando o
acervo da Vale de verdade:

1. **Citação inutilizável.** O pincite saía como `PARTE_1.PDF, p. 10`. Ninguém
   peticiona assim — cita-se o evento. O eproc carimba a origem em 4.246 das
   4.604 folhas (92%), e é dela que sai `Evento 239, EMBDECL1, p. 4`.
2. **Tipo partido por acento.** O modelo alterna `Orgao`/`Órgão` e
   `Diligencia`/`Diligência`; no acervo saiu `Orgao: 127` e `Órgão: 15` como
   coisas distintas — o mesmo conceito fragmentado no grafo.
3. **Aresta sem nome.** O extrator guardava a relação como frase solta com
   `edge_name` vazio, enquanto os produtos da F4 consultam `SUSTENTA`,
   `CONTRADIZ`, `DEPENDE_DE` e `FOI_OMITIDO_EM` por nome. A matriz de cobertura
   saía vazia sobre um grafo cheio, e a cronologia saía sem data porque
   nenhum atributo era lido.

## 5. Critério de sucesso

Um só, falsificável, e já existe o comparador:

> Rodar Vale Trading de novo, com postura assistente-da-parte, contra a consulta
> técnico-pericial de 20/07 escrita sem IA.
>
> **O sistema precisa achar ao menos 5 fatos com pincite que a consulta humana não
> tem.** No ciclo atual achou 1 — e com a citação apontada para o documento errado.

Se não superar o que um advogado escreveu sozinho em uma semana, o problema não é
calibragem: é o produto.

**Resultado: atendido.** Rodando Evento 228 contra o EMBDECL1 do Evento 239 saíram
12 omissões, 11 delas verificadas por trecho literal na fonte. Cinco não constam
da consulta de 20/07, e as cinco foram confirmadas nas folhas citadas: coisa
julgada progressiva, presunção de legitimidade aplicada seletivamente, preclusão
lógica da União, contradição entre invalidar os cálculos do evento 166 e
determinar o destaque, e honorários de sucumbência.

Nada disso é protocolável como está: são insumos verificados, e a força jurídica
de cada ponto é juízo do advogado.

---

## 6. Risco e pendências

- **Nenhum artefato do ciclo Vale é protocolável.** A tese central produzida ("o
  crédito não é comprovável") é adversa ao cliente.
- O achado aproveitável — a União listando o processo por R$ 1,0 bi no Anexo V de
  Riscos Fiscais do PLDO 2024 — precisa ser rastreado nas LDOs 2025 e 2026 antes de
  qualquer uso, e tem o contexto do cluster de outros processos de crédito-prêmio
  na mesma tabela, sugerindo estimativa de classe e não cálculo individualizado.
- Duas instâncias trabalharam em diretórios distintos (`_worktrees/mirofish-helena-control`
  e `projetos/Mirofish INTEIA`). Este worktree contém código; o outro, documentos.
  Definir o oficial antes de qualquer merge.
- Commits locais não enviados ao GitHub.
- A F1 depende de leitura paginada de PDF — a existência dessa capacidade no
  projeto ainda não foi verificada.
