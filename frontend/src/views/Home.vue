<template>
  <div class="home-container">
    <!-- Barra de navegação superior -->
    <nav class="navbar">
      <div class="nav-brand">
        <img src="../assets/logo/inteia_brasao.png" alt="INTEIA" class="nav-brasao" />
        <div class="nav-brand-text">
          <span class="nav-brand-main">INTEIA</span>
          <span class="nav-brand-sub">MIROFISH LAB</span>
        </div>
      </div>
      <div class="nav-links">
        <a href="https://github.com/igormorais123/MiroFish" target="_blank" class="github-link">
          Acessar o repositório no GitHub <span class="arrow">↗</span>
        </a>
      </div>
    </nav>

    <div class="main-content">
      <!-- Parte superior: Área Hero -->
      <section class="hero-section">
        <div class="hero-left">
          <div class="tag-row">
            <span class="orange-tag">INTEIA SIGNAL ENGINE</span>
            <span class="version-text">/ módulo de simulação social</span>
          </div>

          <h1 class="main-title">
            Transforme contexto bruto em<br>
            <span class="gradient-text">cenários acionáveis da INTEIA</span>
          </h1>

          <div class="hero-desc">
            <p>
              O <span class="highlight-bold">MiroFish-INTEIA</span> opera aqui como um motor de simulação e leitura de comportamento dentro do ecossistema <span class="highlight-orange">INTEIA</span>. A partir de relatórios, memorandos, dossiês e sinais políticos, ele monta um ambiente sintético e testa trajetórias prováveis de reação coletiva com disciplina analítica.
            </p>
            <p class="slogan-text">
              Menos demo genérica, mais inteligência aplicada à decisão<span class="blinking-cursor">_</span>
            </p>
          </div>

          <div class="decoration-square"></div>
        </div>

        <div class="hero-right">
          <!-- Área do Logo -->
          <div class="logo-container">
            <div class="inteia-mark">
              <img src="../assets/logo/inteia_brasao.png" alt="INTEIA" class="inteia-badge-img" />
              <div class="inteia-mark-copy">
                <div class="inteia-mark-title">INTEIA</div>
                <div class="inteia-mark-sub">Simulação estratégica com núcleo MiroFish</div>
              </div>
            </div>
            <img src="../assets/logo/inteia_mirror.png" alt="INTEIA - Simulação Estratégica" class="hero-logo" />
          </div>

          <button class="scroll-down-btn" @click="scrollToBottom">
            ↓
          </button>
        </div>
      </section>

      <!-- Parte inferior: Layout de duas colunas -->
      <section class="dashboard-section">
        <!-- Coluna esquerda: Status e etapas -->
        <div class="left-panel">
          <div class="panel-header">
            <span class="status-dot">■</span> Status do sistema
          </div>

          <h2 class="section-title">Pronto para uso</h2>
          <p class="section-desc">
            O motor de previsão está pronto. Envie múltiplos dados não estruturados para iniciar a simulação.
          </p>

          <!-- Cartões de indicadores de dados -->
          <div class="metrics-row">
            <div class="metric-card">
              <div class="metric-value">Baixo custo</div>
              <div class="metric-label">Simulações comuns em torno de US$ 5 por execução</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">Escalável</div>
              <div class="metric-label">Suporte para simulações com até milhões de agentes</div>
            </div>
          </div>

          <!-- Grafo de conhecimento SVG — estilo rico -->
          <div class="graph-preview">
            <svg viewBox="0 0 640 400" class="graph-svg" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <filter id="glow"><feGaussianBlur stdDeviation="2" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
              </defs>

              <!-- === ARESTAS (camada de fundo) === -->
              <!-- Cluster central -->
              <line x1="310" y1="170" x2="200" y2="110" stroke="rgba(15,39,71,0.35)" stroke-width="1.2"/>
              <line x1="310" y1="170" x2="430" y2="120" stroke="rgba(15,39,71,0.35)" stroke-width="1.2"/>
              <line x1="310" y1="170" x2="180" y2="230" stroke="rgba(15,39,71,0.30)" stroke-width="1"/>
              <line x1="310" y1="170" x2="440" y2="240" stroke="rgba(15,39,71,0.30)" stroke-width="1"/>
              <line x1="310" y1="170" x2="310" y2="60" stroke="rgba(15,39,71,0.25)" stroke-width="1"/>
              <line x1="310" y1="170" x2="260" y2="310" stroke="rgba(15,39,71,0.20)" stroke-width="0.8"/>
              <line x1="310" y1="170" x2="390" y2="320" stroke="rgba(15,39,71,0.20)" stroke-width="0.8"/>
              <!-- Sub-clusters esquerda -->
              <line x1="200" y1="110" x2="100" y2="60" stroke="rgba(15,39,71,0.22)" stroke-width="0.8"/>
              <line x1="200" y1="110" x2="90" y2="140" stroke="rgba(15,39,71,0.22)" stroke-width="0.8"/>
              <line x1="200" y1="110" x2="140" y2="180" stroke="rgba(15,39,71,0.18)" stroke-width="0.7"/>
              <line x1="200" y1="110" x2="260" y2="60" stroke="rgba(15,39,71,0.18)" stroke-width="0.7"/>
              <line x1="100" y1="60" x2="90" y2="140" stroke="rgba(15,39,71,0.12)" stroke-width="0.6"/>
              <line x1="90" y1="140" x2="140" y2="180" stroke="rgba(15,39,71,0.12)" stroke-width="0.6"/>
              <!-- Sub-clusters direita -->
              <line x1="430" y1="120" x2="520" y2="70" stroke="rgba(15,39,71,0.22)" stroke-width="0.8"/>
              <line x1="430" y1="120" x2="540" y2="160" stroke="rgba(15,39,71,0.22)" stroke-width="0.8"/>
              <line x1="430" y1="120" x2="490" y2="190" stroke="rgba(15,39,71,0.18)" stroke-width="0.7"/>
              <line x1="520" y1="70" x2="540" y2="160" stroke="rgba(15,39,71,0.12)" stroke-width="0.6"/>
              <line x1="540" y1="160" x2="490" y2="190" stroke="rgba(15,39,71,0.12)" stroke-width="0.6"/>
              <!-- Sub-clusters inferior -->
              <line x1="180" y1="230" x2="100" y2="280" stroke="rgba(15,39,71,0.18)" stroke-width="0.7"/>
              <line x1="180" y1="230" x2="140" y2="310" stroke="rgba(15,39,71,0.15)" stroke-width="0.6"/>
              <line x1="180" y1="230" x2="260" y2="310" stroke="rgba(15,39,71,0.15)" stroke-width="0.6"/>
              <line x1="440" y1="240" x2="520" y2="290" stroke="rgba(15,39,71,0.18)" stroke-width="0.7"/>
              <line x1="440" y1="240" x2="500" y2="330" stroke="rgba(15,39,71,0.15)" stroke-width="0.6"/>
              <line x1="440" y1="240" x2="390" y2="320" stroke="rgba(15,39,71,0.15)" stroke-width="0.6"/>
              <!-- Cross-cluster -->
              <line x1="200" y1="110" x2="430" y2="120" stroke="rgba(15,39,71,0.10)" stroke-width="0.5" stroke-dasharray="4,4"/>
              <line x1="180" y1="230" x2="440" y2="240" stroke="rgba(15,39,71,0.08)" stroke-width="0.5" stroke-dasharray="4,4"/>
              <line x1="100" y1="280" x2="140" y2="310" stroke="rgba(15,39,71,0.10)" stroke-width="0.5"/>
              <line x1="520" y1="290" x2="500" y2="330" stroke="rgba(15,39,71,0.10)" stroke-width="0.5"/>
              <!-- Periféricos -->
              <line x1="310" y1="60" x2="260" y2="60" stroke="rgba(15,39,71,0.12)" stroke-width="0.5"/>
              <line x1="310" y1="60" x2="370" y2="30" stroke="rgba(15,39,71,0.12)" stroke-width="0.5"/>
              <line x1="260" y1="310" x2="390" y2="320" stroke="rgba(15,39,71,0.08)" stroke-width="0.5" stroke-dasharray="3,3"/>

              <!-- === LABELS DE ARESTAS === -->
              <text x="248" y="135" fill="rgba(15,39,71,0.28)" font-size="5.5" font-family="JetBrains Mono" transform="rotate(-18,248,135)">PERTENCE_A</text>
              <text x="370" y="140" fill="rgba(15,39,71,0.28)" font-size="5.5" font-family="JetBrains Mono" transform="rotate(12,370,140)">ATUA_EM</text>
              <text x="230" y="205" fill="rgba(15,39,71,0.22)" font-size="5" font-family="JetBrains Mono" transform="rotate(22,230,205)">INFLUENCIA</text>
              <text x="380" y="210" fill="rgba(15,39,71,0.22)" font-size="5" font-family="JetBrains Mono" transform="rotate(-20,380,210)">COMPETE_COM</text>
              <text x="145" y="90" fill="rgba(15,39,71,0.20)" font-size="4.5" font-family="JetBrains Mono" transform="rotate(-22,145,90)">TRABALHA_EM</text>
              <text x="475" y="92" fill="rgba(15,39,71,0.20)" font-size="4.5" font-family="JetBrains Mono" transform="rotate(18,475,92)">MONITORA</text>
              <text x="135" y="260" fill="rgba(15,39,71,0.16)" font-size="4.5" font-family="JetBrains Mono">REPORTA_A</text>
              <text x="485" y="265" fill="rgba(15,39,71,0.16)" font-size="4.5" font-family="JetBrains Mono">CITA</text>
              <text x="300" y="120" fill="rgba(15,39,71,0.18)" font-size="5" font-family="JetBrains Mono">GERA</text>
              <text x="280" y="250" fill="rgba(15,39,71,0.14)" font-size="4.5" font-family="JetBrains Mono">AVALIA</text>

              <!-- === NÓS === -->
              <!-- Central: Cenário (maior, pulsante) -->
              <circle cx="310" cy="170" r="20" fill="#0f2747" stroke="#f59e0b" stroke-width="2.5" filter="url(#glow)">
                <animate attributeName="r" values="20;22;20" dur="3.5s" repeatCount="indefinite"/>
              </circle>
              <text x="310" y="167" text-anchor="middle" fill="#f59e0b" font-size="7" font-weight="700" font-family="JetBrains Mono">Trabalho</text>
              <text x="310" y="177" text-anchor="middle" fill="#fbbf24" font-size="6.5" font-weight="600" font-family="JetBrains Mono">Remoto</text>

              <!-- Hubs (navy, médios) -->
              <circle cx="200" cy="110" r="14" fill="#0f2747" stroke="#1e3a5f" stroke-width="1.8"/>
              <text x="200" y="114" text-anchor="middle" fill="#e2e8f0" font-size="7" font-weight="600" font-family="Inter">TechBrasil</text>

              <circle cx="430" cy="120" r="14" fill="#0f2747" stroke="#1e3a5f" stroke-width="1.8"/>
              <text x="430" y="124" text-anchor="middle" fill="#e2e8f0" font-size="7" font-weight="600" font-family="Inter">Mercado TI</text>

              <circle cx="180" cy="230" r="13" fill="#0f2747" stroke="#1e3a5f" stroke-width="1.5"/>
              <text x="180" y="234" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="500" font-family="Inter">Gestão RH</text>

              <circle cx="440" cy="240" r="13" fill="#0f2747" stroke="#1e3a5f" stroke-width="1.5"/>
              <text x="440" y="244" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="500" font-family="Inter">Imprensa</text>

              <circle cx="310" cy="60" r="12" fill="#0f2747" stroke="#1e3a5f" stroke-width="1.5"/>
              <text x="310" y="64" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="500" font-family="Inter">Produtividade</text>

              <!-- Person nodes (amber) -->
              <circle cx="100" cy="60" r="8" fill="#f59e0b" opacity="0.85"/>
              <text x="100" y="50" text-anchor="middle" fill="#0f2747" font-size="5.5" font-weight="600" font-family="Inter">CEO Silva</text>

              <circle cx="90" cy="140" r="7" fill="#f59e0b" opacity="0.85"/>
              <text x="90" y="155" text-anchor="middle" fill="#0f2747" font-size="5.5" font-family="Inter">CTO Pereira</text>

              <circle cx="520" cy="70" r="8" fill="#f59e0b" opacity="0.85"/>
              <text x="520" y="60" text-anchor="middle" fill="#0f2747" font-size="5.5" font-weight="600" font-family="Inter">Analista Mkt</text>

              <circle cx="540" cy="160" r="7" fill="#f59e0b" opacity="0.85"/>
              <text x="555" y="155" text-anchor="start" fill="#0f2747" font-size="5.5" font-family="Inter">Jornalista</text>

              <!-- Entity nodes (navy escuro) -->
              <circle cx="140" cy="180" r="7" fill="#1e3a5f"/>
              <text x="140" y="195" text-anchor="middle" fill="rgba(15,39,71,0.6)" font-size="5" font-family="Inter">Equipe DevOps</text>

              <circle cx="260" cy="60" r="6" fill="#1e3a5f"/>
              <text x="260" y="50" text-anchor="middle" fill="rgba(15,39,71,0.6)" font-size="5" font-family="Inter">Sprint Backlog</text>

              <circle cx="490" cy="190" r="7" fill="#1e3a5f"/>
              <text x="505" y="192" text-anchor="start" fill="rgba(15,39,71,0.6)" font-size="5" font-family="Inter">LinkedIn</text>

              <circle cx="370" cy="30" r="5.5" fill="#1e3a5f"/>
              <text x="370" y="22" text-anchor="middle" fill="rgba(15,39,71,0.5)" font-size="4.5" font-family="Inter">Story Points</text>

              <!-- Organization nodes (verde escuro) -->
              <circle cx="100" cy="280" r="7" fill="#2d6a4f" opacity="0.8"/>
              <text x="100" y="295" text-anchor="middle" fill="#2d6a4f" font-size="5" font-family="Inter">Sindicato</text>

              <circle cx="520" cy="290" r="7" fill="#2d6a4f" opacity="0.8"/>
              <text x="520" y="305" text-anchor="middle" fill="#2d6a4f" font-size="5" font-family="Inter">ABES</text>

              <!-- Periféricos menores -->
              <circle cx="140" cy="310" r="5" fill="rgba(15,39,71,0.4)"/>
              <text x="140" y="325" text-anchor="middle" fill="rgba(15,39,71,0.35)" font-size="4.5" font-family="Inter">Turnover 18%</text>

              <circle cx="260" cy="310" r="5" fill="rgba(15,39,71,0.4)"/>
              <text x="260" y="325" text-anchor="middle" fill="rgba(15,39,71,0.35)" font-size="4.5" font-family="Inter">NPS 52</text>

              <circle cx="390" cy="320" r="5" fill="rgba(15,39,71,0.4)"/>
              <text x="390" y="335" text-anchor="middle" fill="rgba(15,39,71,0.35)" font-size="4.5" font-family="Inter">Custo R$45k</text>

              <circle cx="500" cy="330" r="5" fill="rgba(15,39,71,0.4)"/>
              <text x="500" y="345" text-anchor="middle" fill="rgba(15,39,71,0.35)" font-size="4.5" font-family="Inter">Reajuste 8%</text>

              <circle cx="50" cy="210" r="4" fill="rgba(15,39,71,0.3)"/>
              <text x="35" y="213" text-anchor="middle" fill="rgba(15,39,71,0.25)" font-size="4" font-family="Inter">CLT</text>

              <circle cx="590" cy="120" r="4" fill="rgba(15,39,71,0.3)"/>
              <text x="605" y="123" text-anchor="start" fill="rgba(15,39,71,0.25)" font-size="4" font-family="Inter">Glassdoor</text>

              <circle cx="30" cy="320" r="4" fill="rgba(15,39,71,0.25)"/>
              <text x="30" y="335" text-anchor="middle" fill="rgba(15,39,71,0.2)" font-size="4" font-family="Inter">Pesquisa Q4</text>

              <circle cx="580" cy="240" r="4" fill="rgba(15,39,71,0.25)"/>
              <text x="595" y="243" text-anchor="start" fill="rgba(15,39,71,0.2)" font-size="4" font-family="Inter">Concorrente X</text>

              <!-- Arestas extras periféricas -->
              <line x1="50" y1="210" x2="90" y2="140" stroke="rgba(15,39,71,0.08)" stroke-width="0.4"/>
              <line x1="590" y1="120" x2="540" y2="160" stroke="rgba(15,39,71,0.08)" stroke-width="0.4"/>
              <line x1="30" y1="320" x2="100" y2="280" stroke="rgba(15,39,71,0.06)" stroke-width="0.4"/>
              <line x1="580" y1="240" x2="520" y2="290" stroke="rgba(15,39,71,0.06)" stroke-width="0.4"/>
              <line x1="50" y1="210" x2="180" y2="230" stroke="rgba(15,39,71,0.06)" stroke-width="0.4"/>
              <line x1="590" y1="120" x2="430" y2="120" stroke="rgba(15,39,71,0.06)" stroke-width="0.4"/>

              <!-- Glow central -->
              <circle cx="310" cy="170" r="35" fill="none" stroke="rgba(245,158,11,0.06)" stroke-width="12">
                <animate attributeName="r" values="35;42;35" dur="5s" repeatCount="indefinite"/>
                <animate attributeName="stroke-opacity" values="0.06;0.02;0.06" dur="5s" repeatCount="indefinite"/>
              </circle>

              <!-- Legenda -->
              <rect x="16" y="352" width="200" height="42" rx="6" fill="rgba(255,255,255,0.85)" stroke="rgba(15,39,71,0.12)" stroke-width="0.8"/>
              <text x="24" y="365" fill="#0f2747" font-size="5.5" font-weight="700" font-family="Inter">TIPOS DE ENTIDADE</text>
              <circle cx="28" cy="375" r="3.5" fill="#f59e0b"/><text x="36" y="378" fill="#0f2747" font-size="5" font-family="Inter">Person</text>
              <circle cx="78" cy="375" r="3.5" fill="#0f2747"/><text x="86" y="378" fill="#0f2747" font-size="5" font-family="Inter">Entity</text>
              <circle cx="120" cy="375" r="3.5" fill="#1e3a5f"/><text x="128" y="378" fill="#0f2747" font-size="5" font-family="Inter">Recurso</text>
              <circle cx="170" cy="375" r="3.5" fill="#2d6a4f"/><text x="178" y="378" fill="#0f2747" font-size="5" font-family="Inter">Organização</text>

              <!-- Badge de status -->
              <rect x="170" y="380" width="300" height="18" rx="9" fill="rgba(15,39,71,0.85)"/>
              <text x="320" y="392" text-anchor="middle" fill="rgba(245,158,11,0.8)" font-size="5.5" font-family="Inter" font-weight="500">Memória de curto e longo prazo do GraphRAG atualizada em tempo real</text>
            </svg>
          </div>

          <!-- Introdução das etapas de simulação do projeto (área nova) -->
          <div class="steps-container">
            <div class="steps-header">
               <span class="diamond-icon">◇</span> Fluxo de trabalho
            </div>
            <div class="workflow-list">
              <div class="workflow-item">
                <span class="step-num">01</span>
                <div class="step-info">
                  <div class="step-title">Construção do grafo</div>
                  <div class="step-desc">Extração de sinais reais, memória individual e coletiva, e montagem do GraphRAG</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">02</span>
                <div class="step-info">
                  <div class="step-title">Configuração do ambiente</div>
                  <div class="step-desc">Extração de entidades e relações, geração de perfis e parametrização do mundo simulado</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">03</span>
                <div class="step-info">
                  <div class="step-title">Início da simulação</div>
                  <div class="step-desc">Simulação paralela em duas plataformas, interpretação automática do cenário e memória temporal dinâmica</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">04</span>
                <div class="step-info">
                  <div class="step-title">Geração de relatório</div>
                  <div class="step-desc">O agente de relatório usa ferramentas especializadas para analisar o ambiente após a simulação</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">05</span>
                <div class="step-info">
                  <div class="step-title">Interação profunda</div>
                  <div class="step-desc">Converse com agentes do mundo simulado e com o agente de relatório</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Coluna direita: Console interativo -->
        <div class="right-panel">
          <!-- Diagrama: Fluxo completo de simulação -->
          <div class="inteia-illustration right-illustration">
            <svg viewBox="0 0 480 280" xmlns="http://www.w3.org/2000/svg" class="graphrag-pipeline-svg">
              <defs>
                <marker id="flowArrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                  <path d="M0,0 L8,3 L0,6" fill="#f59e0b"/>
                </marker>
                <filter id="stepGlow"><feGaussianBlur stdDeviation="2" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
              </defs>

              <!-- Background -->
              <rect width="480" height="280" rx="14" fill="#f6f3ec"/>
              <rect x="1" y="1" width="478" height="278" rx="13" fill="none" stroke="rgba(15,39,71,0.08)" stroke-width="1"/>

              <!-- Title -->
              <text x="240" y="22" text-anchor="middle" fill="#0f2747" font-size="9" font-weight="700" font-family="Inter" letter-spacing="0.5px" opacity="0.7">COMO FUNCIONA A SIMULAÇÃO</text>

              <!-- === STEP 1: Upload === -->
              <rect x="16" y="36" width="86" height="54" rx="8" fill="#0f2747"/>
              <text x="59" y="52" text-anchor="middle" fill="#fbbf24" font-size="7" font-weight="700" font-family="JetBrains Mono">01</text>
              <text x="59" y="64" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">Envie seu</text>
              <text x="59" y="74" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">documento</text>
              <text x="59" y="84" text-anchor="middle" fill="rgba(255,255,255,0.4)" font-size="5" font-family="Inter">PDF, MD, TXT</text>

              <!-- Arrow 1→2 -->
              <line x1="106" y1="63" x2="126" y2="63" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#flowArrow)"/>

              <!-- === STEP 2: Ontologia === -->
              <rect x="130" y="36" width="86" height="54" rx="8" fill="#0f2747"/>
              <text x="173" y="52" text-anchor="middle" fill="#fbbf24" font-size="7" font-weight="700" font-family="JetBrains Mono">02</text>
              <text x="173" y="64" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">IA extrai</text>
              <text x="173" y="74" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">entidades</text>
              <text x="173" y="84" text-anchor="middle" fill="rgba(255,255,255,0.4)" font-size="5" font-family="Inter">Pessoas, empresas...</text>

              <!-- Arrow 2→3 -->
              <line x1="220" y1="63" x2="240" y2="63" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#flowArrow)"/>

              <!-- === STEP 3: Grafo === -->
              <rect x="244" y="36" width="86" height="54" rx="8" fill="#0f2747" stroke="#f59e0b" stroke-width="1.2"/>
              <text x="287" y="52" text-anchor="middle" fill="#fbbf24" font-size="7" font-weight="700" font-family="JetBrains Mono">03</text>
              <text x="287" y="64" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">Monta grafo</text>
              <text x="287" y="74" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">de relações</text>
              <text x="287" y="84" text-anchor="middle" fill="rgba(255,255,255,0.4)" font-size="5" font-family="Inter">Quem se conecta a quem</text>

              <!-- Arrow 3→4 -->
              <line x1="334" y1="63" x2="354" y2="63" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#flowArrow)"/>

              <!-- === STEP 4: Agentes === -->
              <rect x="358" y="36" width="106" height="54" rx="8" fill="#0f2747"/>
              <text x="411" y="52" text-anchor="middle" fill="#fbbf24" font-size="7" font-weight="700" font-family="JetBrains Mono">04</text>
              <text x="411" y="64" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">Cria agentes</text>
              <text x="411" y="74" text-anchor="middle" fill="#e2e8f0" font-size="6.5" font-weight="600" font-family="Inter">com personalidade</text>
              <text x="411" y="84" text-anchor="middle" fill="rgba(255,255,255,0.4)" font-size="5" font-family="Inter">Bio, opinião, MBTI</text>

              <!-- Arrow 4→5 (curva para baixo) -->
              <path d="M411,94 L411,108" fill="none" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#flowArrow)"/>

              <!-- === STEP 5: Simulação (centro, maior) === -->
              <rect x="130" y="112" width="334" height="60" rx="10" fill="#0f2747" stroke="#f59e0b" stroke-width="1.5" filter="url(#stepGlow)"/>
              <text x="297" y="132" text-anchor="middle" fill="#fbbf24" font-size="8" font-weight="700" font-family="JetBrains Mono">05  SIMULAÇÃO</text>
              <text x="297" y="146" text-anchor="middle" fill="#e2e8f0" font-size="7" font-weight="500" font-family="Inter">Agentes interagem em redes sociais simuladas (posts, likes, comentários)</text>
              <text x="297" y="158" text-anchor="middle" fill="rgba(255,255,255,0.4)" font-size="5.5" font-family="Inter">Feed aberto + Comunidade  •  Múltiplas rodadas  •  Memória temporal</text>

              <!-- Mini social icons inside step 5 -->
              <circle cx="160" y="140" r="4" fill="#f59e0b" opacity="0.6"/>
              <circle cx="172" y="140" r="3" fill="#f59e0b" opacity="0.4"/>
              <circle cx="182" y="140" r="3.5" fill="#f59e0b" opacity="0.5"/>
              <line x1="160" y1="140" x2="172" y2="140" stroke="#f59e0b" stroke-width="0.5" opacity="0.3"/>
              <line x1="172" y1="140" x2="182" y2="140" stroke="#f59e0b" stroke-width="0.5" opacity="0.3"/>

              <!-- Arrow 5→6 -->
              <path d="M297,176 L297,190" fill="none" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#flowArrow)"/>

              <!-- === STEP 6: Relatório (resultado final) === -->
              <rect x="96" y="194" width="288" height="56" rx="10" fill="rgba(245,158,11,0.12)" stroke="#f59e0b" stroke-width="1.2"/>
              <text x="240" y="212" text-anchor="middle" fill="#0f2747" font-size="8" font-weight="700" font-family="JetBrains Mono">RELATÓRIO DE PREVISÃO</text>
              <text x="240" y="226" text-anchor="middle" fill="#0f2747" font-size="6.5" font-weight="500" font-family="Inter" opacity="0.7">Análise com dados do grafo • Entrevistas com agentes • Busca de fatos</text>
              <text x="240" y="238" text-anchor="middle" fill="#0f2747" font-size="5.5" font-family="Inter" opacity="0.5">Gerado por IA com ferramentas de investigação sobre o mundo simulado</text>

              <!-- Document icon on result -->
              <rect x="106" y="206" width="18" height="24" rx="2" fill="#0f2747" opacity="0.12"/>
              <line x1="110" y1="213" x2="120" y2="213" stroke="#0f2747" stroke-width="0.6" opacity="0.3"/>
              <line x1="110" y1="217" x2="118" y2="217" stroke="#0f2747" stroke-width="0.6" opacity="0.2"/>
              <line x1="110" y1="221" x2="120" y2="221" stroke="#0f2747" stroke-width="0.6" opacity="0.3"/>
              <line x1="110" y1="225" x2="116" y2="225" stroke="#0f2747" stroke-width="0.6" opacity="0.2"/>

              <!-- Left decoration: upload icon -->
              <rect x="22" y="112" width="86" height="60" rx="8" fill="rgba(15,39,71,0.04)" stroke="rgba(15,39,71,0.08)" stroke-width="0.8"/>
              <text x="65" y="138" text-anchor="middle" fill="#0f2747" font-size="6" font-weight="600" font-family="Inter" opacity="0.5">Seu cenário</text>
              <text x="65" y="150" text-anchor="middle" fill="#0f2747" font-size="5.5" font-family="Inter" opacity="0.35">"Migrar para</text>
              <text x="65" y="159" text-anchor="middle" fill="#0f2747" font-size="5.5" font-family="Inter" opacity="0.35">trabalho remoto"</text>
              <!-- Arrow left→5 -->
              <line x1="112" y1="142" x2="126" y2="142" stroke="#f59e0b" stroke-width="1" marker-end="url(#flowArrow)" opacity="0.5"/>

              <!-- Bottom tagline -->
              <text x="240" y="268" text-anchor="middle" fill="#0f2747" font-size="6" font-family="Inter" opacity="0.3">Envie um documento → IA simula o futuro → Receba o relatório</text>
            </svg>
          </div>

          <div class="console-box">
            <!-- Área de upload -->
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">01 / Dados de origem</span>
                <span class="console-meta">Formatos suportados: PDF, MD, TXT</span>
              </div>

              <div
                class="upload-zone"
                :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
                @dragover.prevent="handleDragOver"
                @dragleave.prevent="handleDragLeave"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept=".pdf,.md,.markdown,.txt"
                  @change="handleFileSelect"
                  style="display: none"
                  :disabled="loading"
                />

                <div v-if="files.length === 0" class="upload-placeholder">
                  <div class="upload-icon">↑</div>
                  <div class="upload-title">Arraste arquivos para enviar</div>
                  <div class="upload-hint">ou clique para abrir o sistema de arquivos</div>
                </div>

                <div v-else class="file-list">
                  <div v-for="(file, index) in files" :key="index" class="file-item">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ file.name }}</span>
                    <button @click.stop="removeFile(index)" class="remove-btn">×</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Linha divisória -->
            <div class="console-divider">
              <span>Parâmetros</span>
            </div>

            <!-- Área de entrada -->
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">>_ 02 / Cenário da simulação</span>
              </div>
              <div class="input-wrapper">
                <textarea
                  v-model="formData.simulationRequirement"
                  class="code-input"
                  placeholder="// Descreva em linguagem natural o cenário de simulação ou previsão"
                  rows="6"
                  :disabled="loading"
                ></textarea>
                <div class="model-badge">Motor: INTEIA / MiroFish</div>
              </div>
            </div>

            <!-- Botao de iniciar -->
            <div class="console-section btn-section">
              <button
                class="start-engine-btn"
                @click="startSimulation"
                :disabled="!canSubmit || loading"
              >
                <span v-if="!loading">Iniciar motor</span>
                <span v-else>Inicializando...</span>
                <span class="btn-arrow">→</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Base de dados de projetos históricos -->
      <HistoryDatabase />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { setPendingUpload } from '../store/pendingUpload'
import HistoryDatabase from '../components/HistoryDatabase.vue'

const router = useRouter()

// Dados do formulário
const formData = ref({
  simulationRequirement: ''
})

// Lista de arquivos
const files = ref([])

// Estado
const loading = ref(false)
const error = ref('')
const isDragOver = ref(false)

// Referencia de entrada de arquivo
const fileInput = ref(null)

// Propriedade computada: se pode submeter
const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== ''
})

// Disparar seleção de arquivo
const triggerFileInput = () => {
  if (!loading.value) {
    fileInput.value?.click()
  }
}

// Tratar seleção de arquivo
const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
}

// Tratar eventos de arrastar e soltar
const handleDragOver = (e) => {
  if (!loading.value) {
    isDragOver.value = true
  }
}

const handleDragLeave = (e) => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return

  const droppedFiles = Array.from(e.dataTransfer.files)
  addFiles(droppedFiles)
}

// Adicionar arquivo
const addFiles = (newFiles) => {
  error.value = ''
  const validFiles = newFiles.filter(file => {
    const ext = file.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'markdown', 'txt'].includes(ext)
  })
  const rejectedCount = newFiles.length - validFiles.length
  if (rejectedCount > 0) {
    error.value = `${rejectedCount} arquivo(s) ignorado(s). Use PDF, MD, MARKDOWN ou TXT.`
  }
  files.value.push(...validFiles)
}

// Remover arquivo
const removeFile = (index) => {
  files.value.splice(index, 1)
}

// Rolar ate o final
const scrollToBottom = () => {
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  })
}

// Iniciar simulação - navegar imediatamente, chamada de API feita na página Process
const startSimulation = () => {
  if (!canSubmit.value || loading.value) return

  setPendingUpload(files.value, formData.value.simulationRequirement)

  // Navegar imediatamente para página Process (usando identificador especial para novo projeto)
  router.push({
    name: 'Process',
    params: { projectId: 'new' }
  })
}
</script>

<style scoped>
/* Variaveis globais e reset */
:root {
  --black: #000000;
  --white: #FFFFFF;
  --orange: #FF4500;
  --gray-light: #F5F5F5;
  --gray-text: #666666;
  --border: #E5E5E5;
  /*
    Usar Space Grotesk como fonte de título principal, JetBrains Mono como fonte de código/tags
    Garantir que estas Google Fonts foram importadas no index.html
  */
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', system-ui, sans-serif;
}

.home-container {
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(245, 158, 11, 0.16), transparent 26%),
    linear-gradient(180deg, #f7f3ea 0%, #f2eee5 100%);
  font-family: var(--font-sans);
  color: var(--black);
}

/* Navegação superior */
.navbar {
  min-height: 68px;
  background: linear-gradient(135deg, #08111f 0%, #13213a 100%);
  color: var(--white);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  border-bottom: 1px solid rgba(245, 158, 11, 0.22);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-brasao {
  width: 81px;
  height: auto;
  filter: drop-shadow(0 1px 3px rgba(0,0,0,0.3));
}

.nav-brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-brand-main {
  font-family: var(--font-mono);
  font-weight: 800;
  letter-spacing: 0.22em;
  font-size: 1rem;
  color: #f7fbff;
}

.nav-brand-sub {
  font-size: 0.68rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(245, 158, 11, 0.92);
}

.nav-links {
  display: flex;
  align-items: center;
}

.github-link {
  color: rgba(255,255,255,0.88);
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: opacity 0.2s;
}

.github-link:hover {
  opacity: 0.8;
}

.arrow {
  font-family: sans-serif;
}

/* Área de conteúdo principal */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 40px;
}

/* Área Hero */
.hero-section {
  display: flex;
  justify-content: space-between;
  margin-bottom: 80px;
  position: relative;
}

.hero-left {
  flex: 1;
  padding-right: 60px;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 25px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.orange-tag {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: var(--white);
  padding: 6px 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  font-size: 0.7rem;
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(245, 158, 11, 0.18);
}

.version-text {
  color: #7b8799;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.main-title {
  font-size: 4.5rem;
  line-height: 1.2;
  font-weight: 500;
  margin: 0 0 40px 0;
  letter-spacing: -2px;
  color: var(--black);
}

.gradient-text {
  background: linear-gradient(90deg, #10203b 0%, #f59e0b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}

.hero-desc {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--gray-text);
  max-width: 640px;
  margin-bottom: 50px;
  font-weight: 400;
  text-align: justify;
}

.hero-desc p {
  margin-bottom: 1.5rem;
}

.highlight-bold {
  color: var(--black);
  font-weight: 700;
}

.highlight-orange {
  color: #d97706;
  font-weight: 700;
  font-family: var(--font-mono);
}

.highlight-code {
  background: rgba(11, 20, 38, 0.06);
  padding: 2px 6px;
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: 0.9em;
  color: #10203b;
  font-weight: 600;
}

.slogan-text {
  font-size: 1.2rem;
  font-weight: 520;
  color: var(--black);
  letter-spacing: 1px;
  border-left: 3px solid #f59e0b;
  padding-left: 15px;
  margin-top: 20px;
}

.blinking-cursor {
  color: #f59e0b;
  animation: blink 1s step-end infinite;
  font-weight: 700;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.decoration-square {
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 12px 24px rgba(245, 158, 11, 0.22);
}

.hero-right {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
}

.logo-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 18px;
  justify-content: flex-end;
  padding-right: 40px;
}

.inteia-mark {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: rgba(8, 17, 31, 0.94);
  border: 1px solid rgba(245, 158, 11, 0.24);
  border-radius: 18px;
  box-shadow: 0 24px 60px rgba(8, 17, 31, 0.18);
}

.inteia-badge-img {
  width: 117px;
  height: auto;
  filter: drop-shadow(0 2px 6px rgba(201, 162, 39, 0.3));
}

.inteia-mark-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.inteia-mark-title {
  font-family: var(--font-mono);
  font-weight: 800;
  letter-spacing: 0.16em;
  color: #fff;
}

.inteia-mark-sub {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.72);
}

.hero-logo {
  max-width: 500px;
  width: 100%;
  border-radius: 20px;
  box-shadow: 0 36px 90px rgba(245, 158, 11, 0.12), 0 0 60px rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.25);
  object-fit: cover;
}

/* Grafo SVG preview */
.graph-preview {
  margin: 24px 0;
  background: var(--inteia-paper, #f6f3ec);
  border-radius: 16px;
  padding: 12px;
  border: 1px solid rgba(15, 39, 71, 0.10);
  box-shadow: 0 16px 48px rgba(15, 39, 71, 0.08);
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: auto;
  display: block;
}

/* Ilustrações INTEIA */
.inteia-illustration {
  margin: 24px 0;
  text-align: center;
}

.inteia-illustration .illustration-img {
  width: 100%;
  max-width: 480px;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.15);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.inteia-illustration .illustration-img:hover {
  transform: translateY(-4px);
  box-shadow: 0 28px 70px rgba(245, 158, 11, 0.18);
}

.right-illustration {
  margin-bottom: 16px;
}

.right-illustration .illustration-img {
  max-width: 100%;
  border-radius: 14px;
}

.graphrag-pipeline-svg {
  width: 100%;
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.10);
  border: 1px solid rgba(245, 158, 11, 0.15);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.graphrag-pipeline-svg:hover {
  transform: translateY(-4px);
  box-shadow: 0 28px 70px rgba(245, 158, 11, 0.14);
}

.scroll-down-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #d97706;
  font-size: 1.2rem;
  transition: all 0.2s;
}

.scroll-down-btn:hover {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.08);
}

/* Layout de duas colunas do Dashboard */
.dashboard-section {
  display: flex;
  gap: 60px;
  border-top: 1px solid var(--border);
  padding-top: 60px;
  align-items: flex-start;
}

.dashboard-section .left-panel,
.dashboard-section .right-panel {
  display: flex;
  flex-direction: column;
}

/* Painel esquerdo */
.left-panel {
  flex: 0.8;
}

.panel-header {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #999;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.status-dot {
  color: var(--orange);
  font-size: 0.8rem;
}

.section-title {
  font-size: 2rem;
  font-weight: 520;
  margin: 0 0 15px 0;
}

.section-desc {
  color: var(--gray-text);
  margin-bottom: 25px;
  line-height: 1.6;
}

.metrics-row {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.metric-card {
  border: 1px solid var(--border);
  padding: 20px 30px;
  min-width: 150px;
}

.metric-value {
  font-family: var(--font-mono);
  font-size: 1.8rem;
  font-weight: 520;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 0.85rem;
  color: #999;
}

/* Introdução das etapas de simulação do projeto */
.steps-container {
  border: 1px solid var(--border);
  padding: 30px;
  position: relative;
}

.steps-header {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #999;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.diamond-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.workflow-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.step-num {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--black);
  opacity: 0.3;
}

.step-info {
  flex: 1;
}

.step-title {
  font-weight: 520;
  font-size: 1rem;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 0.85rem;
  color: var(--gray-text);
}

/* Console interativo do lado direito */
.right-panel {
  flex: 1.2;
}

.console-box {
  border: 1px solid rgba(204, 204, 204, 0.6);
  padding: 8px;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 4px;
}

.console-section {
  padding: 20px;
}

.console-section.btn-section {
  padding-top: 0;
}

.console-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #666;
}

.upload-zone {
  border: 1px dashed #CCC;
  height: 200px;
  overflow-y: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #FAFAFA;
}

.upload-zone.has-files {
  align-items: flex-start;
}

.upload-zone:hover {
  background: #F0F0F0;
  border-color: #999;
}

.upload-placeholder {
  text-align: center;
}

.upload-icon {
  width: 40px;
  height: 40px;
  border: 1px solid #DDD;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  color: #999;
}

.upload-title {
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.upload-hint {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #999;
}

.file-list {
  width: 100%;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  background: var(--white);
  padding: 8px 12px;
  border: 1px solid #EEE;
  font-family: var(--font-mono);
  font-size: 0.85rem;
}

.file-name {
  flex: 1;
  margin: 0 10px;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: #999;
}

.console-divider {
  display: flex;
  align-items: center;
  margin: 10px 0;
}

.console-divider::before,
.console-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #EEE;
}

.console-divider span {
  padding: 0 15px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: #BBB;
  letter-spacing: 1px;
}

.input-wrapper {
  position: relative;
  border: 1px solid #DDD;
  background: #FAFAFA;
}

.code-input {
  width: 100%;
  border: none;
  background: transparent;
  padding: 20px;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  min-height: 150px;
}

.model-badge {
  position: absolute;
  bottom: 10px;
  right: 15px;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: #AAA;
}

.start-engine-btn {
  width: 100%;
  background: var(--black);
  color: var(--white);
  border: none;
  padding: 20px;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1.1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 1px;
  position: relative;
  overflow: hidden;
}

/* Estado clicavel (não desabilitado) */
.start-engine-btn:not(:disabled) {
  background: var(--black);
  border: 1px solid var(--black);
  animation: pulse-border 2s infinite;
}

.start-engine-btn:hover:not(:disabled) {
  background: var(--orange);
  border-color: var(--orange);
  transform: translateY(-2px);
}

.start-engine-btn:active:not(:disabled) {
  transform: translateY(0);
}

.start-engine-btn:disabled {
  background: #E5E5E5;
  color: #999;
  cursor: not-allowed;
  transform: none;
  border: 1px solid #E5E5E5;
}

/* Animação de guia: pulso sutil na borda */
@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.2); }
  70% { box-shadow: 0 0 0 6px rgba(0, 0, 0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
}

/* Adaptação responsiva */
@media (max-width: 1024px) {
  .dashboard-section {
    flex-direction: column;
  }

  .hero-section {
    flex-direction: column;
  }

  .hero-left {
    padding-right: 0;
    margin-bottom: 40px;
  }

  .hero-logo {
    max-width: 200px;
    margin-bottom: 20px;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: 30px 16px;
  }

  .main-title {
    font-size: 2rem;
    letter-spacing: -0.5px;
  }

  .hero-desc {
    font-size: 0.95rem;
  }

  .tag-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .metrics-row {
    flex-direction: column;
  }

  .graph-preview {
    display: none;
  }

  .navbar {
    padding: 12px 16px;
  }

  .nav-brand-sub {
    display: none;
  }

  .logo-container {
    max-width: 100%;
  }

  .hero-logo {
    max-width: 160px;
  }

  .slogan-text {
    font-size: 1rem;
  }

  .home-container {
    overflow-x: hidden;
  }
}
</style>
