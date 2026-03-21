from pathlib import Path
import re
import shutil

ui_path = Path(r"C:\Users\IgorPC\projetos\projetos-claude\lenia-eleitoral\public\lenia-eleitoral\js\network-ui.js")
html_path = Path(r"C:\Users\IgorPC\projetos\projetos-claude\lenia-eleitoral\public\lenia-eleitoral\lenia.html")

for src, suffix in [
    (ui_path, "network-ui.mirofish-v4-backup.js"),
    (html_path, "lenia.mirofish-v4-backup.html"),
]:
    backup = src.with_name(suffix)
    if not backup.exists():
        shutil.copy2(src, backup)

ui = ui_path.read_text(encoding="utf-8")
html = html_path.read_text(encoding="utf-8")

ui = re.sub(
    r"// Events definition\s+const EVENTS = \{.*?\};\s+\n\s*/\* ===== Estado ===== \*/",
    """// Events definition
  const BASE_EVENTS = {
    debate: { nome: 'Debate TV', global: true, dOrient: 0, dEngaj: +0.15, dToler: +0.05, desc: 'Engajamento sobe e a tolerancia melhora.' },
    escandalo: { nome: 'Escandalo', global: false, dOrient: +0.12, dEngaj: +0.20, dToler: -0.18, desc: 'Crise localizada com erosao de tolerancia.' },
    programa: { nome: 'Prog. Social', global: false, dOrient: -0.10, dEngaj: +0.08, dToler: +0.12, desc: 'Programa social reduz tensao.' },
    fakenews: { nome: 'Fake News', global: true, dOrient: +0.10, dEngaj: +0.12, dToler: -0.20, desc: 'Polariza e erode tolerancia.' },
  };

  const RR_EVENTS = {
    onda_desinfo: { nome: 'Onda desinfo', global: true, dOrient: +0.06, dEngaj: +0.10, dToler: -0.18, desc: 'Escalada de boatos nos canais locais.' },
    crise_saude: { nome: 'Crise saude', global: true, dOrient: -0.02, dEngaj: +0.08, dToler: -0.10, desc: 'Pressao territorial em saude publica.' },
    choque_migratorio: { nome: 'Choque migratorio', global: true, dOrient: +0.06, dEngaj: +0.07, dToler: -0.14, desc: 'Migracao sobe na agenda e pressiona coesao.' },
    pauta_garimpo: { nome: 'Pauta garimpo', global: false, dOrient: +0.05, dEngaj: +0.09, dToler: -0.12, desc: 'Conflito sobre garimpo e terra indigena.' },
    pacote_social: { nome: 'Pacote social', global: false, dOrient: -0.08, dEngaj: +0.05, dToler: +0.10, desc: 'Resposta social com foco em renda e servicos.' },
    operacao_seguranca: { nome: 'Operacao seguranca', global: false, dOrient: +0.04, dEngaj: +0.06, dToler: -0.06, desc: 'Acao de seguranca com impacto local.' },
    mutirao_saude: { nome: 'Mutirao saude', global: false, dOrient: -0.03, dEngaj: +0.04, dToler: +0.08, desc: 'Entrega territorial em saude.' },
  };

  const RR_SCENARIOS = {
    guerra_narrativa: { nome: 'Guerra narrativa', desc: 'Boatos + migracao + foco no municipio mais fragil.', steps: ['onda_desinfo', 'choque_migratorio', 'pauta_garimpo'] },
    crise_servicos: { nome: 'Crise servicos', desc: 'Saude, renda e resposta territorial.', steps: ['crise_saude', 'mutirao_saude', 'pacote_social'] },
    fronteira_quente: { nome: 'Fronteira quente', desc: 'Migracao, seguranca e desinformacao.', steps: ['choque_migratorio', 'operacao_seguranca', 'onda_desinfo'] },
  };

  function currentEvents() {
    return currentState?.uf === 'rr' ? RR_EVENTS : BASE_EVENTS;
  }

  function currentScenarios() {
    return currentState?.uf === 'rr' ? RR_SCENARIOS : {};
  }

  /* ===== Estado ===== */""",
    ui,
    flags=re.S,
)

ui = ui.replace("let selectedEvent = null;", "let selectedEvent = null;\n  let appliedScenarioSummary = '';")
ui = ui.replace(
    "const $eventBtns    = $('event-buttons');\n  const $eventInfo    = $('event-info');",
    "const $eventBtns    = $('event-buttons');\n  const $eventInfo    = $('event-info');\n  const $scenarioBtns = $('scenario-buttons');\n  const $scenarioInfo = $('scenario-info');\n  const $scenarioPanel = $('scenario-panel');",
)
ui = ui.replace("const ev = EVENTS[selectedEvent];", "const ev = currentEvents()[selectedEvent];")
ui = ui.replace("Object.entries(EVENTS).forEach(([id, ev]) => {", "$eventBtns.innerHTML = '';\n  Object.entries(currentEvents()).forEach(([id, ev]) => {")
ui = ui.replace(
    "$('event-disclaimer').textContent = `Globais aplicam imediato. Locais: clique no ${singular} no mapa.`;",
    "$('event-disclaimer').textContent = currentState.uf === 'rr' ? `Globais aplicam imediato. Locais: clique no ${singular} para testar evento territorial.` : `Globais aplicam imediato. Locais: clique no ${singular} no mapa.`;",
)
ui = ui.replace(
    "function aggregateRRStateSummary() {\n    const rows = rrVoterAggregates?.regions || [];\n    if (!rows.length) return null;\n    const byDesinfo = [...rows].sort((a, b) => (b.desinformacao_media || 0) - (a.desinformacao_media || 0))[0];\n    const byHealth = [...rows].sort((a, b) => (a.avaliacao_saude_media || 9) - (b.avaliacao_saude_media || 9))[0];\n    const allConcerns = new Map();\n    for (const row of rows) {\n      for (const item of row.top_preocupacoes || []) {\n        allConcerns.set(item.tema, (allConcerns.get(item.tema) || 0) + item.freq);\n      }\n    }\n    const dominantConcern = [...allConcerns.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || 'Nao identificado';\n    return { byDesinfo, byHealth, dominantConcern };\n  }",
    """function aggregateRRStateSummary() {
    const rows = rrVoterAggregates?.regions || [];
    if (!rows.length) return null;
    const byDesinfo = [...rows].sort((a, b) => (b.desinformacao_media || 0) - (a.desinformacao_media || 0))[0];
    const byHealth = [...rows].sort((a, b) => (a.avaliacao_saude_media || 9) - (b.avaliacao_saude_media || 9))[0];
    const byImmigration = [...rows].sort((a, b) => (b.imigracao_negativa_share || 0) - (a.imigracao_negativa_share || 0))[0];
    const bySocial = [...rows].sort((a, b) => (b.recebe_programa_social_share || 0) - (a.recebe_programa_social_share || 0))[0];
    const allConcerns = new Map();
    for (const row of rows) {
      for (const item of row.top_preocupacoes || []) {
        allConcerns.set(item.tema, (allConcerns.get(item.tema) || 0) + item.freq);
      }
    }
    const dominantConcern = [...allConcerns.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || 'Nao identificado';
    return { byDesinfo, byHealth, byImmigration, bySocial, dominantConcern };
  }

  function getRegionalPriority(row) {
    const agg = getRRVoterAggregate(row?.nome || row?.ra_nome || row);
    if (!agg) return 0;
    const desinfo = (agg.desinformacao_media || 0) / 5;
    const saude = 1 - ((agg.avaliacao_saude_media || 0) / 5);
    const seguranca = 1 - ((agg.avaliacao_seguranca_media || 0) / 5);
    const imigracao = agg.imigracao_negativa_share || 0;
    const social = agg.recebe_programa_social_share || 0;
    return desinfo * 0.28 + saude * 0.22 + seguranca * 0.14 + imigracao * 0.20 + social * 0.16;
  }

  function getIssueProfileText(node) {
    const agg = getRRVoterAggregate(node?.nome);
    if (!agg) return null;
    return [
      `tema: ${topConcernLabel(agg)}`,
      `desinfo ${(agg.desinformacao_media || 0).toFixed(1)}/5`,
      `saude ${(agg.avaliacao_saude_media || 0).toFixed(1)}/5`,
      `imigracao neg ${((agg.imigracao_negativa_share || 0) * 100).toFixed(0)}%`,
      `programa social ${((agg.recebe_programa_social_share || 0) * 100).toFixed(0)}%`
    ].join(' | ');
  }

  function resolveScenarioTarget(stepIndex) {
    const summary = aggregateRRStateSummary();
    if (!summary) return null;
    if (stepIndex === 0) return engine.findNode(summary.byDesinfo?.regiao_administrativa);
    if (stepIndex === 1) return engine.findNode(summary.byHealth?.regiao_administrativa);
    return engine.findNode(summary.byImmigration?.regiao_administrativa || summary.bySocial?.regiao_administrativa);
  }

  function applyScenario(id) {
    const scenario = currentScenarios()[id];
    if (!scenario) return;
    const catalog = currentEvents();
    scenario.steps.forEach((eventId, idx) => {
      const eventDef = catalog[eventId];
      if (!eventDef) return;
      if (eventDef.global) {
        engine.injectEvent(eventDef, null);
      } else {
        const targetNode = resolveScenarioTarget(idx);
        if (targetNode) engine.injectEvent(eventDef, targetNode);
      }
    });
    appliedScenarioSummary = `${scenario.nome}: ${scenario.desc}`;
    if ($scenarioInfo) $scenarioInfo.textContent = appliedScenarioSummary;
    updateMapColors();
  }

  function renderScenarioControls() {
    if (!$scenarioPanel || !$scenarioBtns || !$scenarioInfo) return;
    const scenarios = currentScenarios();
    $scenarioBtns.innerHTML = '';
    if (!Object.keys(scenarios).length) {
      $scenarioPanel.style.display = 'none';
      return;
    }
    $scenarioPanel.style.display = 'block';
    Object.entries(scenarios).forEach(([id, scenario]) => {
      const btn = document.createElement('button');
      btn.className = 'event-btn';
      btn.textContent = scenario.nome;
      btn.title = scenario.desc;
      btn.addEventListener('click', () => {
        $scenarioBtns.querySelectorAll('.event-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        applyScenario(id);
      });
      $scenarioBtns.appendChild(btn);
    });
    $scenarioInfo.textContent = appliedScenarioSummary || 'Aplique uma rota piloto para testar um encadeamento tematico completo.';
  }""",
)
ui = ui.replace(
    "  await loadMirofishContext();\n  if (mirofishContext) {",
    "  await loadMirofishContext();\n  renderScenarioControls();\n  if (mirofishContext) {",
)
ui = ui.replace(
    "    renderMirofishPanel();\n  }",
    "    renderMirofishPanel();\n  }\n  if (!mirofishContext && currentState.uf === 'rr' && $eventInfo) {\n    $eventInfo.textContent = 'RR carregado com microdados agregados dos 1000 eleitores.';\n  }",
    1,
)
ui = ui.replace(
    "    updateMapColors();\n  });",
    "    appliedScenarioSummary = '';\n    if ($scenarioInfo) $scenarioInfo.textContent = currentState.uf === 'rr' ? 'Aplique uma rota piloto para testar um encadeamento tematico completo.' : '';\n    $scenarioBtns?.querySelectorAll('.event-btn').forEach(b => b.classList.remove('active'));\n    updateMapColors();\n  });",
    1,
)
ui = ui.replace(
    "const pM = getMirofishPriorityByNode(node);",
    "const pM = getMirofishPriorityByNode(node) + getRegionalPriority(node);",
)
ui = ui.replace(
    "const da = daBase + getMirofishPriority(a);\n      const db = dbBase + getMirofishPriority(b);",
    "const da = daBase + getMirofishPriority(a) + getRegionalPriority(a);\n      const db = dbBase + getMirofishPriority(b) + getRegionalPriority(b);",
)
ui = ui.replace(
    "const badge = mirofishContext && priority > 0.30 ? '<span class=\"mf-badge\">foco mirofish</span>' : '';",
    "const regional = getRegionalPriority(r);\n      const badge = ((mirofishContext && priority > 0.30) ? '<span class=\"mf-badge\">foco mirofish</span>' : '') + (regional > 0.58 ? '<span class=\"mf-badge\">pressao territorial</span>' : '');",
)
ui = ui.replace(
    "    if (!cards.length) return;",
    "    if (appliedScenarioSummary) {\n      cards.unshift(`\n        <div class=\"insight-card ins-risk\">\n          <div class=\"ins-head\"><span class=\"ins-icon\">T</span> Rota piloto aplicada</div>\n          <div class=\"ins-body\">${appliedScenarioSummary}</div>\n          <div class=\"ins-action\">Use ranking, tooltip e mapa para ver quais municipios absorveram mais impacto.</div>\n        </div>\n      `);\n    }\n    if (!cards.length) return;",
    1,
)
ui = re.sub(
    r"  function showTooltip\(e, name, node\) \{.*?\n  \}",
    """  function showTooltip(e, name, node) {
    if (!node) {
      $tooltip.textContent = name;
      $tooltip.style.display = 'block';
      $tooltip.style.left = (e.clientX + 14) + 'px';
      $tooltip.style.top = (e.clientY - 10) + 'px';
      return;
    }
    const oLabel = node.orientacao < 0.4 ? 'Esq' : node.orientacao > 0.6 ? 'Dir' : 'Ctr';
    const priority = getMirofishPriorityByNode(node);
    const regional = getRegionalPriority(node);
    const rrAgg = getRRVoterAggregate(node.nome);
    const mfLine = mirofishContext
      ? `<br>MiroFish: <span style="color:${priority > 0.3 ? '#f59e0b' : '#94a3b8'}">${priority > 0.3 ? 'Foco alto' : priority > 0.18 ? 'Foco medio' : 'Foco baixo'}</span>`
      : '';
    const regionalLine = rrAgg
      ? `<br>Pressao territorial: <span style="color:${regional > 0.62 ? '#f59e0b' : '#94a3b8'}">${regional > 0.62 ? 'Alta' : regional > 0.42 ? 'Media' : 'Baixa'}</span><br>${getIssueProfileText(node)}`
      : '';
    const scenarioLine = appliedScenarioSummary ? `<br>Rota ativa: ${appliedScenarioSummary}` : '';
    $tooltip.innerHTML =
      `<strong>${node.nome}</strong> (${node.sigla})<br>` +
      `Orient: <span style="color:${node.orientacao < 0.4 ? '#60a5fa' : node.orientacao > 0.6 ? '#f87171' : '#d69e2e'}">${oLabel} ${(node.orientacao * 100).toFixed(1)}%</span><br>` +
      `Engaj: ${(node.engajamento * 100).toFixed(1)}%<br>` +
      `Toler: <span style="color:${node.tolerancia < 0.4 ? '#ef4444' : '#22c55e'}">${(node.tolerancia * 100).toFixed(1)}%</span><br>` +
      `Inercia: ${(node.inercia * 100).toFixed(0)}% | Pop: ${(node.populacao / 1000).toFixed(0)}k` + mfLine + regionalLine + scenarioLine;
    $tooltip.style.display = 'block';
    $tooltip.style.left = (e.clientX + 14) + 'px';
    $tooltip.style.top = (e.clientY - 10) + 'px';
  }""",
    ui,
    count=1,
    flags=re.S,
)

ui_path.write_text(ui, encoding="utf-8")

html = html.replace("<h3>Eventos Eleitorais</h3>", "<h3>Eventos Tematicos</h3>")
events_block = """          <div class="ctrl-section">
            <h3>Eventos Tematicos</h3>
            <div id="event-buttons" class="ctrl-row" style="gap:4px"></div>
            <div id="event-info" class="event-info"></div>
            <p class="disclaimer" id="event-disclaimer">Globais aplicam imediato. Locais: clique na RA no mapa.</p>
          </div>"""
scenario_block = events_block + """
          <div class="ctrl-section" id="scenario-panel">
            <h3>Rotas Piloto</h3>
            <div id="scenario-buttons" class="ctrl-row" style="gap:4px"></div>
            <div id="scenario-info" class="event-info">Aplique uma rota piloto para testar um encadeamento tematico completo.</div>
            <p class="disclaimer" id="scenario-disclaimer">RR: aplique uma rota para combinar desinformacao, saude, migracao e pressao territorial.</p>
          </div>"""
html = html.replace(events_block, scenario_block, 1)
html_path.write_text(html, encoding="utf-8")

print("patched-lenia-rr-ui")
