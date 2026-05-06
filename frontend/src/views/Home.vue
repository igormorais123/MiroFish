<template>
  <div class="home-container">
    <!-- Camadas locais (canvas neural + grain ficam globais via InteiaBackground) -->
    <div class="bg-grid" aria-hidden="true"></div>
    <div class="bg-gold-glow" aria-hidden="true"></div>

    <!-- Navbar flutuante -->
    <nav class="navbar">
      <div class="nav-inner">
        <div class="nav-brand">
          <img src="../assets/logo/inteia_shield.png" alt="INTEIA" class="nav-brasao" />
          <div class="nav-brand-text">
            <span class="nav-brand-main">INTEIA</span>
            <span class="nav-brand-sub">Mirofish Lab</span>
          </div>
        </div>

        <div class="nav-meta">
          <span class="nav-meta-item"><span class="nav-pulse"></span> Motor online</span>
          <span class="nav-meta-divider">/</span>
          <span class="nav-meta-item nav-mono">v2.0 · simulação social</span>
        </div>

        <div class="nav-links">
          <a href="https://github.com/igormorais123/MiroFish" target="_blank" rel="noopener" class="github-link" data-cursor-label="abrir">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.52-1.32-1.27-1.67-1.27-1.67-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.68 1.24 3.34.95.1-.74.4-1.24.73-1.53-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.18-3.1-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.18 1.19a11.1 11.1 0 0 1 5.78 0c2.21-1.5 3.18-1.19 3.18-1.19.62 1.59.23 2.76.11 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.7 5.41-5.27 5.69.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56C20.21 21.39 23.5 17.08 23.5 12 23.5 5.65 18.35.5 12 .5Z"/>
            </svg>
            <span>Repositório</span>
            <span class="arrow">↗</span>
          </a>
        </div>
      </div>
    </nav>

    <main class="main-content">
      <!-- HERO -->
      <section class="hero-section">
        <div class="hero-left">
          <div class="eyebrow">
            <span class="eyebrow-dot"></span>
            <span class="eyebrow-tag">INTEIA Signal Engine</span>
            <span class="eyebrow-meta">/ módulo de simulação social</span>
          </div>

          <h1 class="display-title">
            Transforme contexto bruto em
            <span class="display-italic">cenários acionáveis</span>
            <span class="display-accent">da INTEIA.</span>
          </h1>

          <div class="hero-desc">
            <p>
              O <span class="strong">Mirofish&nbsp;INTEIA</span> opera como motor de simulação e leitura de comportamento dentro do ecossistema <span class="gold">INTEIA</span>. A partir de relatórios, memorandos, dossiês e sinais políticos, monta um ambiente sintético e testa trajetórias prováveis de reação coletiva com disciplina analítica.
            </p>
            <p class="quote">
              Menos demo genérica, mais inteligência aplicada à decisão<span class="cursor">_</span>
            </p>
          </div>

          <div class="hero-pillars">
            <div class="pillar">
              <div class="pillar-num">01</div>
              <div class="pillar-label">GraphRAG narrativo</div>
              <div class="pillar-desc">Memória de curto e longo prazo, multi-fonte.</div>
            </div>
            <div class="pillar">
              <div class="pillar-num">02</div>
              <div class="pillar-label">Agentes psicometricamente parametrizados</div>
              <div class="pillar-desc">Bio, opinião, MBTI e ancoragem social.</div>
            </div>
            <div class="pillar">
              <div class="pillar-num">03</div>
              <div class="pillar-label">Relatório auditável</div>
              <div class="pillar-desc">Análise com citações de cenário e entidade.</div>
            </div>
          </div>
        </div>

        <aside class="hero-right">
          <div class="brand-card">
            <div class="brand-card-edge brand-card-edge-tl"></div>
            <div class="brand-card-edge brand-card-edge-tr"></div>
            <div class="brand-card-edge brand-card-edge-bl"></div>
            <div class="brand-card-edge brand-card-edge-br"></div>

            <div class="brand-card-header">
              <img src="../assets/logo/inteia_shield.png" alt="" class="brand-card-brasao" />
              <div>
                <div class="brand-card-title">INTEIA</div>
                <div class="brand-card-sub">Simulação estratégica · núcleo Mirofish</div>
              </div>
            </div>

            <div class="brand-card-image-wrap">
              <video
                class="brand-card-image brand-card-video"
                src="/hero-mirror.mp4"
                poster="/hero-mirror-poster.jpg"
                autoplay
                muted
                loop
                playsinline
                preload="metadata"
                aria-label="INTEIA — Simulação estratégica"
              ></video>
              <div class="brand-card-video-mask" aria-hidden="true"></div>
              <div class="brand-card-image-glow" aria-hidden="true"></div>
            </div>

            <div class="brand-card-footer">
              <div class="kpi">
                <div class="kpi-value">~ US$&nbsp;5</div>
                <div class="kpi-label">por execução típica</div>
              </div>
              <div class="kpi-divider"></div>
              <div class="kpi">
                <div class="kpi-value">10⁶</div>
                <div class="kpi-label">agentes simulados</div>
              </div>
              <div class="kpi-divider"></div>
              <div class="kpi">
                <div class="kpi-value">5</div>
                <div class="kpi-label">etapas auditáveis</div>
              </div>
            </div>
          </div>

          <button class="scroll-down-btn" @click="scrollToConsole" aria-label="Rolar para console" data-cursor-label="ir para console">
            <span class="scroll-down-label">console</span>
            <span class="scroll-down-arrow">↓</span>
          </button>
        </aside>
      </section>

      <!-- DASHBOARD -->
      <section class="dashboard-section" id="console-anchor">
        <div class="dashboard-divider">
          <span class="dashboard-divider-line"></span>
          <span class="dashboard-divider-label">Console operacional</span>
          <span class="dashboard-divider-line"></span>
        </div>

        <div class="dashboard-grid">
          <!-- Coluna esquerda -->
          <div class="left-panel">
            <div class="panel-header">
              <span class="status-dot"></span>
              <span class="panel-header-label">Status do sistema</span>
              <span class="panel-header-mono">READY</span>
            </div>

            <h2 class="section-title">Pronto para uso<span class="title-period">.</span></h2>
            <p class="section-desc">
              O motor de previsão está pronto. Envie múltiplos dados não estruturados para iniciar a simulação.
            </p>

            <div class="metrics-row">
              <div class="metric-card">
                <div class="metric-label-top">custo</div>
                <div class="metric-value">Baixo</div>
                <div class="metric-label">Simulações típicas em torno de US$&nbsp;5 por execução.</div>
              </div>
              <div class="metric-card">
                <div class="metric-label-top">escala</div>
                <div class="metric-value">Massiva</div>
                <div class="metric-label">Suporte a simulações com até milhões de agentes.</div>
              </div>
            </div>

            <div class="graph-preview">
              <div class="graph-preview-header">
                <span class="graph-preview-tag">GraphRAG · memória dinâmica</span>
                <span class="graph-preview-mono">live</span>
              </div>
              <svg viewBox="0 0 640 400" class="graph-svg" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <filter id="glow"><feGaussianBlur stdDeviation="2.5" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                  <radialGradient id="centerGold" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="#e7b948" stop-opacity="1"/>
                    <stop offset="100%" stop-color="#c9952a" stop-opacity="0.7"/>
                  </radialGradient>
                </defs>

                <!-- Arestas (paper-friendly) -->
                <g stroke="rgba(20,22,30,0.30)" stroke-width="1">
                  <line x1="310" y1="170" x2="200" y2="110"/>
                  <line x1="310" y1="170" x2="430" y2="120"/>
                  <line x1="310" y1="170" x2="180" y2="230"/>
                  <line x1="310" y1="170" x2="440" y2="240"/>
                  <line x1="310" y1="170" x2="310" y2="60"/>
                  <line x1="310" y1="170" x2="260" y2="310"/>
                  <line x1="310" y1="170" x2="390" y2="320"/>
                </g>
                <g stroke="rgba(20,22,30,0.18)" stroke-width="0.7">
                  <line x1="200" y1="110" x2="100" y2="60"/>
                  <line x1="200" y1="110" x2="90" y2="140"/>
                  <line x1="200" y1="110" x2="140" y2="180"/>
                  <line x1="200" y1="110" x2="260" y2="60"/>
                  <line x1="430" y1="120" x2="520" y2="70"/>
                  <line x1="430" y1="120" x2="540" y2="160"/>
                  <line x1="430" y1="120" x2="490" y2="190"/>
                  <line x1="180" y1="230" x2="100" y2="280"/>
                  <line x1="180" y1="230" x2="140" y2="310"/>
                  <line x1="180" y1="230" x2="260" y2="310"/>
                  <line x1="440" y1="240" x2="520" y2="290"/>
                  <line x1="440" y1="240" x2="500" y2="330"/>
                  <line x1="440" y1="240" x2="390" y2="320"/>
                </g>
                <g stroke="rgba(20,22,30,0.12)" stroke-width="0.5" stroke-dasharray="4,4">
                  <line x1="200" y1="110" x2="430" y2="120"/>
                  <line x1="180" y1="230" x2="440" y2="240"/>
                </g>

                <!-- Labels arestas -->
                <g fill="rgba(20,22,30,0.55)" font-size="5.5" font-family="JetBrains Mono">
                  <text x="248" y="135" transform="rotate(-18,248,135)">PERTENCE_A</text>
                  <text x="370" y="140" transform="rotate(12,370,140)">ATUA_EM</text>
                  <text x="230" y="205" transform="rotate(22,230,205)">INFLUENCIA</text>
                  <text x="380" y="210" transform="rotate(-20,380,210)">COMPETE_COM</text>
                  <text x="300" y="120">GERA</text>
                </g>

                <!-- Núcleo central -->
                <circle cx="310" cy="170" r="40" fill="none" stroke="rgba(201,149,42,0.10)" stroke-width="14">
                  <animate attributeName="r" values="38;46;38" dur="5s" repeatCount="indefinite"/>
                  <animate attributeName="stroke-opacity" values="0.10;0.04;0.10" dur="5s" repeatCount="indefinite"/>
                </circle>
                <circle cx="310" cy="170" r="20" fill="url(#centerGold)" stroke="#e7b948" stroke-width="1.5" filter="url(#glow)">
                  <animate attributeName="r" values="20;22;20" dur="3.5s" repeatCount="indefinite"/>
                </circle>
                <text x="310" y="167" text-anchor="middle" fill="#0a0e1a" font-size="7" font-weight="700" font-family="JetBrains Mono">Cenário</text>
                <text x="310" y="177" text-anchor="middle" fill="#0a0e1a" font-size="6.5" font-weight="600" font-family="JetBrains Mono">central</text>

                <!-- Hubs -->
                <g font-family="Geist, Outfit" font-weight="600">
                  <circle cx="200" cy="110" r="14" fill="#1c1e27" stroke="#c9952a" stroke-width="1.4"/>
                  <text x="200" y="114" text-anchor="middle" fill="#f5f2ea" font-size="7">TechBrasil</text>
                  <circle cx="430" cy="120" r="14" fill="#1c1e27" stroke="#c9952a" stroke-width="1.4"/>
                  <text x="430" y="124" text-anchor="middle" fill="#f5f2ea" font-size="7">Mercado TI</text>
                  <circle cx="180" cy="230" r="13" fill="#1c1e27" stroke="rgba(201,149,42,0.7)" stroke-width="1.2"/>
                  <text x="180" y="234" text-anchor="middle" fill="#f5f2ea" font-size="6.5">Gestão RH</text>
                  <circle cx="440" cy="240" r="13" fill="#1c1e27" stroke="rgba(201,149,42,0.7)" stroke-width="1.2"/>
                  <text x="440" y="244" text-anchor="middle" fill="#f5f2ea" font-size="6.5">Imprensa</text>
                  <circle cx="310" cy="60" r="12" fill="#1c1e27" stroke="rgba(201,149,42,0.7)" stroke-width="1.2"/>
                  <text x="310" y="64" text-anchor="middle" fill="#f5f2ea" font-size="6.5">Produtividade</text>
                </g>

                <!-- Pessoas -->
                <g font-family="Geist, Outfit">
                  <circle cx="100" cy="60" r="8" fill="#c9952a"/>
                  <text x="100" y="50" text-anchor="middle" fill="#7a5a18" font-size="5.5" font-weight="600">CEO Silva</text>
                  <circle cx="90" cy="140" r="7" fill="#c9952a"/>
                  <text x="90" y="155" text-anchor="middle" fill="#7a5a18" font-size="5.5">CTO Pereira</text>
                  <circle cx="520" cy="70" r="8" fill="#c9952a"/>
                  <text x="520" y="60" text-anchor="middle" fill="#7a5a18" font-size="5.5" font-weight="600">Analista Mkt</text>
                  <circle cx="540" cy="160" r="7" fill="#c9952a"/>
                  <text x="555" y="155" text-anchor="start" fill="#7a5a18" font-size="5.5">Jornalista</text>
                </g>

                <!-- Recursos / org -->
                <g font-family="Geist, Outfit">
                  <circle cx="140" cy="180" r="7" fill="#5C9EAD"/>
                  <text x="140" y="195" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5">Equipe DevOps</text>
                  <circle cx="260" cy="60" r="6" fill="#5C9EAD"/>
                  <text x="260" y="50" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5">Sprint Backlog</text>
                  <circle cx="490" cy="190" r="7" fill="#5C9EAD"/>
                  <text x="505" y="192" text-anchor="start" fill="rgba(20,22,30,0.55)" font-size="5">LinkedIn</text>
                  <circle cx="100" cy="280" r="7" fill="#3FB77C"/>
                  <text x="100" y="295" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5">Sindicato</text>
                  <circle cx="520" cy="290" r="7" fill="#3FB77C"/>
                  <text x="520" y="305" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5">ABES</text>
                </g>

                <!-- Periféricos -->
                <g fill="rgba(20,22,30,0.45)" font-family="Geist, Outfit" font-size="4.5">
                  <circle cx="140" cy="310" r="5" fill="rgba(201,149,42,0.55)"/>
                  <text x="140" y="325" text-anchor="middle">Turnover 18%</text>
                  <circle cx="260" cy="310" r="5" fill="rgba(201,149,42,0.55)"/>
                  <text x="260" y="325" text-anchor="middle">NPS 52</text>
                  <circle cx="390" cy="320" r="5" fill="rgba(201,149,42,0.55)"/>
                  <text x="390" y="335" text-anchor="middle">Custo R$45k</text>
                  <circle cx="500" cy="330" r="5" fill="rgba(201,149,42,0.55)"/>
                  <text x="500" y="345" text-anchor="middle">Reajuste 8%</text>
                </g>

                <!-- Legenda -->
                <g>
                  <rect x="16" y="358" width="220" height="34" rx="6" fill="rgba(245,242,234,0.95)" stroke="rgba(20,22,30,0.18)" stroke-width="0.7"/>
                  <text x="24" y="370" fill="#7a5a18" font-size="5.5" font-weight="700" font-family="Geist, Outfit" letter-spacing="0.6">TIPOS DE ENTIDADE</text>
                  <circle cx="28" cy="382" r="3" fill="#c9952a"/><text x="36" y="385" fill="#14161e" font-size="5" font-family="Geist, Outfit">Pessoa</text>
                  <circle cx="76" cy="382" r="3" fill="#1c1e27"/><text x="84" y="385" fill="#14161e" font-size="5" font-family="Geist, Outfit">Hub</text>
                  <circle cx="118" cy="382" r="3" fill="#5C9EAD"/><text x="126" y="385" fill="#14161e" font-size="5" font-family="Geist, Outfit">Recurso</text>
                  <circle cx="172" cy="382" r="3" fill="#3FB77C"/><text x="180" y="385" fill="#14161e" font-size="5" font-family="Geist, Outfit">Organização</text>
                </g>
              </svg>
            </div>

            <div class="steps-container">
              <div class="steps-header">
                <span class="diamond-icon">◇</span>
                <span>Fluxo de trabalho</span>
                <span class="steps-header-meta">5 etapas</span>
              </div>
              <div class="workflow-list">
                <div class="workflow-item" v-for="step in workflowSteps" :key="step.num">
                  <span class="step-num">{{ step.num }}</span>
                  <div class="step-info">
                    <div class="step-title">{{ step.title }}</div>
                    <div class="step-desc">{{ step.desc }}</div>
                  </div>
                  <span class="step-tick">→</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Coluna direita: console -->
          <div class="right-panel">
            <div class="pipeline-card">
              <div class="pipeline-card-header">
                <span class="pipeline-card-title">Como funciona a simulação</span>
                <span class="pipeline-card-mono">/ pipeline</span>
              </div>
              <svg viewBox="0 0 480 280" xmlns="http://www.w3.org/2000/svg" class="pipeline-svg">
                <defs>
                  <marker id="flowArrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6" fill="#c9952a"/>
                  </marker>
                  <filter id="stepGlow"><feGaussianBlur stdDeviation="2.5" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                </defs>

                <rect width="480" height="280" rx="12" fill="#fbf8ee"/>
                <rect x="1" y="1" width="478" height="278" rx="11" fill="none" stroke="rgba(20,22,30,0.10)" stroke-width="1"/>

                <text x="240" y="22" text-anchor="middle" fill="#7a5a18" font-size="9" font-weight="600" font-family="Geist, Outfit" letter-spacing="1.2">PIPELINE · DADO → PREVISÃO</text>

                <!-- Step 1 -->
                <rect x="16" y="36" width="86" height="54" rx="8" fill="#ffffff" stroke="rgba(20,22,30,0.14)" stroke-width="0.8"/>
                <text x="59" y="52" text-anchor="middle" fill="#7a5a18" font-size="7" font-weight="700" font-family="JetBrains Mono">01</text>
                <text x="59" y="64" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">Envie seu</text>
                <text x="59" y="74" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">documento</text>
                <text x="59" y="84" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5" font-family="Geist, Outfit">PDF · MD · TXT</text>

                <line x1="106" y1="63" x2="126" y2="63" stroke="#c9952a" stroke-width="1.3" marker-end="url(#flowArrow)"/>

                <!-- Step 2 -->
                <rect x="130" y="36" width="86" height="54" rx="8" fill="#ffffff" stroke="rgba(20,22,30,0.14)" stroke-width="0.8"/>
                <text x="173" y="52" text-anchor="middle" fill="#7a5a18" font-size="7" font-weight="700" font-family="JetBrains Mono">02</text>
                <text x="173" y="64" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">IA extrai</text>
                <text x="173" y="74" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">entidades</text>
                <text x="173" y="84" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5" font-family="Geist, Outfit">Pessoas, empresas...</text>

                <line x1="220" y1="63" x2="240" y2="63" stroke="#c9952a" stroke-width="1.3" marker-end="url(#flowArrow)"/>

                <!-- Step 3 (destacado) -->
                <rect x="244" y="36" width="86" height="54" rx="8" fill="#ffffff" stroke="#c9952a" stroke-width="1.4"/>
                <text x="287" y="52" text-anchor="middle" fill="#7a5a18" font-size="7" font-weight="700" font-family="JetBrains Mono">03</text>
                <text x="287" y="64" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">Monta grafo</text>
                <text x="287" y="74" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">de relações</text>
                <text x="287" y="84" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5" font-family="Geist, Outfit">Quem se conecta a quem</text>

                <line x1="334" y1="63" x2="354" y2="63" stroke="#c9952a" stroke-width="1.3" marker-end="url(#flowArrow)"/>

                <!-- Step 4 -->
                <rect x="358" y="36" width="106" height="54" rx="8" fill="#ffffff" stroke="rgba(20,22,30,0.14)" stroke-width="0.8"/>
                <text x="411" y="52" text-anchor="middle" fill="#7a5a18" font-size="7" font-weight="700" font-family="JetBrains Mono">04</text>
                <text x="411" y="64" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">Cria agentes</text>
                <text x="411" y="74" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="600" font-family="Geist, Outfit">com personalidade</text>
                <text x="411" y="84" text-anchor="middle" fill="rgba(20,22,30,0.55)" font-size="5" font-family="Geist, Outfit">Bio, opinião, MBTI</text>

                <path d="M411,94 L411,108" fill="none" stroke="#c9952a" stroke-width="1.3" marker-end="url(#flowArrow)"/>

                <!-- Step 5 (destacado/dark accent) -->
                <rect x="130" y="112" width="334" height="60" rx="10" fill="#1c1e27" stroke="#c9952a" stroke-width="1.5" filter="url(#stepGlow)"/>
                <text x="297" y="132" text-anchor="middle" fill="#eab14a" font-size="8" font-weight="700" font-family="JetBrains Mono">05  ·  SIMULAÇÃO</text>
                <text x="297" y="146" text-anchor="middle" fill="#f5f2ea" font-size="7" font-weight="500" font-family="Geist, Outfit">Agentes interagem em redes simuladas (posts, likes, comentários)</text>
                <text x="297" y="158" text-anchor="middle" fill="rgba(245,242,234,0.65)" font-size="5.5" font-family="Geist, Outfit">Feed aberto + comunidade · múltiplas rodadas · memória temporal</text>

                <path d="M297,176 L297,190" fill="none" stroke="#c9952a" stroke-width="1.3" marker-end="url(#flowArrow)"/>

                <!-- Resultado -->
                <rect x="96" y="194" width="288" height="56" rx="10" fill="rgba(201,149,42,0.14)" stroke="#c9952a" stroke-width="1.2"/>
                <text x="240" y="212" text-anchor="middle" fill="#7a5a18" font-size="8" font-weight="700" font-family="JetBrains Mono">RELATÓRIO DE PREVISÃO</text>
                <text x="240" y="226" text-anchor="middle" fill="#14161e" font-size="6.5" font-weight="500" font-family="Geist, Outfit" opacity="0.92">Análise com dados do grafo · entrevistas com agentes · busca de fatos</text>
                <text x="240" y="238" text-anchor="middle" fill="rgba(20,22,30,0.65)" font-size="5.5" font-family="Geist, Outfit">Gerado por IA com ferramentas de investigação sobre o mundo simulado</text>

                <!-- Cenário lateral -->
                <rect x="22" y="112" width="86" height="60" rx="8" fill="rgba(201,149,42,0.08)" stroke="rgba(201,149,42,0.40)" stroke-width="0.8" stroke-dasharray="3,3"/>
                <text x="65" y="138" text-anchor="middle" fill="#7a5a18" font-size="6" font-weight="600" font-family="Geist, Outfit" opacity="0.95">Seu cenário</text>
                <text x="65" y="150" text-anchor="middle" fill="rgba(20,22,30,0.65)" font-size="5.5" font-family="Geist, Outfit" font-style="italic">"Migrar para</text>
                <text x="65" y="159" text-anchor="middle" fill="rgba(20,22,30,0.65)" font-size="5.5" font-family="Geist, Outfit" font-style="italic">trabalho remoto"</text>
                <line x1="112" y1="142" x2="126" y2="142" stroke="#c9952a" stroke-width="0.8" marker-end="url(#flowArrow)" opacity="0.7"/>

                <text x="240" y="270" text-anchor="middle" fill="rgba(122,90,24,0.55)" font-size="6" font-family="Geist, Outfit" letter-spacing="1.5">DOCUMENTO → SIMULAÇÃO → RELATÓRIO</text>
              </svg>
            </div>

            <div class="console-box">
              <div class="console-box-header">
                <span class="console-box-title">Console interativo</span>
                <span class="console-box-mono">/ Mirofish · INTEIA</span>
              </div>

              <div class="console-section">
                <div class="console-header">
                  <span class="console-label"><span class="console-label-num">01</span> Dados de origem</span>
                  <span class="console-meta">PDF · MD · TXT</span>
                </div>

                <div
                  class="upload-zone"
                  :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
                  @dragover.prevent="handleDragOver"
                  @dragleave.prevent="handleDragLeave"
                  @drop.prevent="handleDrop"
                  @click="triggerFileInput"
                  data-cursor-label="enviar arquivos"
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
                    <div class="upload-icon" aria-hidden="true">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 19V5"/><path d="M5 12l7-7 7 7"/>
                      </svg>
                    </div>
                    <div class="upload-title">Arraste arquivos para enviar</div>
                    <div class="upload-hint">ou clique para abrir o sistema de arquivos</div>
                  </div>

                  <div v-else class="file-list">
                    <div v-for="(file, index) in files" :key="index" class="file-item">
                      <span class="file-icon" aria-hidden="true">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>
                        </svg>
                      </span>
                      <span class="file-name">{{ file.name }}</span>
                      <button @click.stop="removeFile(index)" class="remove-btn" :aria-label="'Remover ' + file.name">×</button>
                    </div>
                  </div>
                </div>
                <div v-if="error" class="upload-error">{{ error }}</div>
              </div>

              <div class="console-divider">
                <span>Parâmetros</span>
              </div>

              <div class="console-section">
                <div class="console-header">
                  <span class="console-label"><span class="console-label-num">02</span> Cenário da simulação</span>
                  <span class="console-meta">linguagem natural</span>
                </div>
                <div class="input-wrapper">
                  <textarea
                    id="scenario"
                    v-model="formData.simulationRequirement"
                    class="code-input"
                    placeholder="// Descreva em linguagem natural o cenário de simulação ou previsão"
                    rows="6"
                    :disabled="loading"
                  ></textarea>
                  <div class="model-badge">Motor: INTEIA / Mirofish</div>
                </div>
              </div>

              <div class="console-section btn-section">
                <button
                  class="start-engine-btn"
                  @click="startSimulation"
                  :disabled="!canSubmit || loading"
                >
                  <span class="btn-label">
                    <span v-if="!loading">Iniciar motor</span>
                    <span v-else>Inicializando...</span>
                  </span>
                  <span class="btn-arrow" aria-hidden="true">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M5 12h14"/><path d="M13 5l7 7-7 7"/>
                    </svg>
                  </span>
                </button>
                <p class="btn-hint" v-if="!canSubmit">Descreva ao menos um cenário para liberar o motor.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="history-wrap">
        <HistoryDatabase />
      </div>
    </main>

    <footer class="footer">
      <div class="footer-inner">
        <div class="footer-left">
          <span class="footer-brand">INTEIA</span>
          <span class="footer-meta">Mirofish Lab · simulação social</span>
        </div>
        <div class="footer-right">
          <span class="footer-meta">© INTEIA · Inteligência aplicada à decisão.</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { setPendingUpload } from '../store/pendingUpload'
import HistoryDatabase from '../components/HistoryDatabase.vue'

onMounted(() => { document.body.dataset.theme = 'paper' })
onBeforeUnmount(() => { delete document.body.dataset.theme })

const router = useRouter()

const formData = ref({
  simulationRequirement: ''
})

const files = ref([])
const loading = ref(false)
const error = ref('')
const isDragOver = ref(false)
const fileInput = ref(null)

const workflowSteps = [
  { num: '01', title: 'Construção do grafo', desc: 'Extração de sinais reais, memória individual e coletiva, montagem do GraphRAG.' },
  { num: '02', title: 'Configuração do ambiente', desc: 'Extração de entidades e relações, geração de perfis e parametrização do mundo.' },
  { num: '03', title: 'Início da simulação', desc: 'Simulação paralela em duas plataformas, interpretação automática e memória dinâmica.' },
  { num: '04', title: 'Geração de relatório', desc: 'Agente de relatório usa ferramentas especializadas para analisar o ambiente simulado.' },
  { num: '05', title: 'Interação profunda', desc: 'Converse com agentes do mundo simulado e com o agente de relatório.' }
]

const canSubmit = computed(() => formData.value.simulationRequirement.trim() !== '')

const triggerFileInput = () => {
  if (!loading.value) fileInput.value?.click()
}

const handleFileSelect = (event) => {
  addFiles(Array.from(event.target.files))
}

const handleDragOver = () => {
  if (!loading.value) isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return
  addFiles(Array.from(e.dataTransfer.files))
}

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

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const scrollToConsole = () => {
  const el = document.getElementById('console-anchor')
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  else window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  setPendingUpload(files.value, formData.value.simulationRequirement)
  router.push({ name: 'Process', params: { projectId: 'new' } })
}
</script>

<style scoped>
/* === Tokens INTEIA (modo paper — alinhado com MainView/Process) === */
.home-container {
  --ink: #07070A;
  --ink-2: #0C0D11;
  --ink-3: #13141A;
  --ink-4: #1C1E27;
  --gold: #C9952A;
  --gold-light: #EAB14A;
  --gold-deep: #7A5A18;
  --gold-glow: rgba(234, 177, 74, 0.14);
  --gold-haze: rgba(201, 149, 42, 0.04);
  --paper-bg: #f5f2ea;
  --paper-bg-2: #efeadc;
  --paper-card: rgba(255, 255, 255, 0.78);
  --paper-card-strong: rgba(255, 255, 255, 0.92);
  --line: rgba(15, 18, 28, 0.10);
  --line-strong: rgba(15, 18, 28, 0.18);
  --gold-soft: #faf5e6;
  --text: #14161e;
  --text-muted: rgba(20, 22, 30, 0.62);
  --text-faint: rgba(20, 22, 30, 0.42);
  --serif: 'Fraunces', Georgia, 'Times New Roman', serif;
  --sans: 'Geist', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, 'SFMono-Regular', monospace;
  --ease: cubic-bezier(0.2, 0.8, 0.2, 1);
  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  position: relative;
  min-height: 100vh;
  background:
    /* Pontilhado editorial sutil tipo print */
    radial-gradient(circle at 1px 1px, rgba(20, 22, 30, 0.10) 1px, transparent 0),
    radial-gradient(900px 500px at 80% -10%, var(--gold-glow), transparent 60%),
    radial-gradient(900px 500px at 0% 100%, var(--gold-haze), transparent 60%),
    linear-gradient(180deg, var(--paper-bg) 0%, var(--paper-bg-2) 100%);
  background-size: 24px 24px, auto, auto, auto;
  font-family: var(--sans);
  color: var(--text);
  overflow-x: hidden;
}

/* Camadas de fundo (grain editorial INTEIA) */
.bg-noise {
  position: fixed; inset: 0; pointer-events: none; z-index: 2;
  opacity: 0.22; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' seed='5'/%3E%3CfeColorMatrix values='0 0 0 0 0.96, 0 0 0 0 0.95, 0 0 0 0 0.92, 0 0 0 0.012 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.bg-grid {
  position: absolute; inset: 0; pointer-events: none; opacity: 0.5; z-index: 0;
  background-image:
    linear-gradient(to right, rgba(234, 177, 74, 0.025) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(234, 177, 74, 0.025) 1px, transparent 1px);
  background-size: 80px 80px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
.bg-gold-glow {
  position: absolute; top: 280px; right: 0; width: 520px; height: 520px;
  transform: translateX(35%);
  background: radial-gradient(circle, rgba(201, 149, 42, 0.18), transparent 70%);
  filter: blur(40px); pointer-events: none; z-index: 0;
}

/* === Navbar === */
.navbar {
  position: sticky; top: 0; z-index: 50;
  padding: 16px 24px 0;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}
.nav-inner {
  max-width: 1400px; margin: 0 auto;
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 22px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(20, 22, 30, 0.10);
  border-radius: 999px;
  box-shadow: 0 12px 32px rgba(20, 22, 30, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.6);
}
.nav-brand { display: flex; align-items: center; gap: 12px; }
.nav-brasao {
  width: 38px; height: 38px; object-fit: contain;
  filter: drop-shadow(0 2px 8px rgba(201, 149, 42, 0.45));
}
.nav-brand-text { display: flex; flex-direction: column; gap: 1px; }
.nav-brand-main {
  font-family: var(--mono); font-weight: 700; letter-spacing: 0.24em;
  font-size: 0.85rem; color: var(--gold-deep, #7a5a18);
}
.nav-brand-sub {
  font-family: var(--sans); font-size: 0.62rem; letter-spacing: 0.22em;
  text-transform: uppercase; color: var(--gold-deep, #7a5a18); opacity: 0.7;
}
.nav-meta {
  display: flex; align-items: center; gap: 10px;
  font-family: var(--mono); font-size: 0.72rem; color: rgba(20, 22, 30, 0.62);
}
.nav-meta-item { display: flex; align-items: center; gap: 6px; }
.nav-meta-divider { color: rgba(20, 22, 30, 0.30); }
.nav-mono { color: var(--gold-deep, #7a5a18); opacity: 0.85; }
.nav-pulse {
  width: 7px; height: 7px; border-radius: 50%;
  background: #4ade80; box-shadow: 0 0 8px #4ade80;
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }

.github-link {
  display: inline-flex; align-items: center; gap: 8px;
  min-height: 44px;
  padding: 10px 18px; border-radius: 999px;
  border: 1px solid rgba(20, 22, 30, 0.14);
  background: rgba(255, 255, 255, 0.55);
  color: var(--gold-deep, #7a5a18);
  font-family: var(--mono); font-size: 0.78rem; font-weight: 500;
  text-decoration: none; cursor: pointer;
  transition: all 200ms ease;
}
.github-link:hover {
  border-color: var(--gold, #c9952a); color: var(--gold-deep, #7a5a18);
  background: rgba(201, 149, 42, 0.10);
  box-shadow: 0 0 0 4px rgba(201, 149, 42, 0.10);
}
.github-link .arrow { font-family: sans-serif; }

/* === Main === */
.main-content {
  position: relative; z-index: 1;
  max-width: 1400px; margin: 0 auto;
  padding: 80px 40px 40px;
}

/* === Hero === */
.hero-section {
  position: relative;
  display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 64px;
  margin-bottom: 120px; align-items: start;
}
/* Vinheta removida no modo paper — fundo já é claro */
.hero-section::before { display: none; }
.hero-left { padding-right: 12px; position: relative; z-index: 1; }

.eyebrow {
  display: inline-flex; align-items: center; gap: 12px;
  padding: 8px 14px; margin-bottom: 32px;
  border: 1px solid rgba(201, 149, 42, 0.32);
  border-radius: 999px;
  background: rgba(201, 149, 42, 0.08);
  font-family: var(--mono); font-size: 0.72rem;
}
.eyebrow-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--gold);
  box-shadow: 0 0 12px var(--gold-light);
}
.eyebrow-tag { color: var(--gold-deep); font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; }
.eyebrow-meta { color: var(--text-muted); }

.display-title {
  font-family: var(--serif);
  font-size: clamp(2.8rem, 5.6vw, 5rem);
  line-height: 1.02; letter-spacing: -0.025em;
  font-weight: 500;
  font-variation-settings: "opsz" 144, "SOFT" 0, "WONK" 0;
  color: var(--text); margin: 0 0 36px;
  /* sem text-shadow no modo paper */
}
.display-italic {
  display: inline-block; font-style: italic; font-weight: 500;
  font-variation-settings: "opsz" 144, "SOFT" 50, "WONK" 1;
  color: var(--gold-deep);
}
.display-accent {
  display: inline-block;
  font-family: var(--serif); font-weight: 500; font-style: normal;
  font-variation-settings: "opsz" 144, "SOFT" 0, "WONK" 0;
  color: var(--text); letter-spacing: -0.02em;
}

.hero-desc {
  font-size: 1.05rem; line-height: 1.75;
  color: var(--text-muted);
  max-width: 560px; margin-bottom: 44px;
}
.hero-desc p { margin: 0 0 18px; }
.strong { color: var(--text); font-weight: 600; }
.gold {
  color: var(--gold-light); font-weight: 600;
  font-family: var(--mono); letter-spacing: 0.04em;
}
.quote {
  font-family: var(--serif); font-style: italic;
  font-size: 1.25rem; line-height: 1.55;
  color: var(--gold-deep);
  border-left: 2px solid var(--gold);
  padding: 6px 0 6px 18px;
  margin-top: 8px;
}
.cursor {
  color: var(--gold); font-weight: 700;
  animation: blink 1.1s step-end infinite;
}
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

.hero-pillars {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
  padding-top: 24px; border-top: 1px solid var(--line);
}
.pillar { display: flex; flex-direction: column; gap: 6px; }
.pillar-num {
  font-family: var(--mono); font-size: 0.72rem; font-weight: 600;
  color: var(--gold); letter-spacing: 0.18em;
}
.pillar-label {
  font-family: var(--serif); font-size: 1.05rem; font-weight: 500;
  color: var(--text); line-height: 1.25;
}
.pillar-desc { font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; }

/* Hero right */
.hero-right { display: flex; flex-direction: column; align-items: stretch; gap: 24px; }
.brand-card {
  position: relative;
  padding: 28px;
  background: var(--paper-card-strong);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--line-strong);
  border-radius: 22px;
  box-shadow: 0 24px 60px rgba(15, 18, 28, 0.10), inset 0 1px 0 rgba(255, 255, 255, 0.6);
  overflow: hidden;
}
.brand-card-edge {
  position: absolute; width: 22px; height: 22px;
  border: 1px solid var(--gold); pointer-events: none;
}
.brand-card-edge-tl { top: 10px; left: 10px; border-right: none; border-bottom: none; }
.brand-card-edge-tr { top: 10px; right: 10px; border-left: none; border-bottom: none; }
.brand-card-edge-bl { bottom: 10px; left: 10px; border-right: none; border-top: none; }
.brand-card-edge-br { bottom: 10px; right: 10px; border-left: none; border-top: none; }

.brand-card-header {
  display: flex; align-items: center; gap: 14px;
  padding-bottom: 18px; margin-bottom: 18px;
  border-bottom: 1px solid var(--line);
}
.brand-card-brasao {
  width: 64px; height: 64px; object-fit: contain;
  filter: drop-shadow(0 4px 14px rgba(201, 149, 42, 0.45));
}
.brand-card-title {
  font-family: var(--mono); font-weight: 700;
  letter-spacing: 0.22em; color: var(--text); font-size: 1.05rem;
}
.brand-card-sub { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }

.brand-card-image-wrap {
  position: relative; border-radius: 14px; overflow: hidden;
  aspect-ratio: 16 / 9;
  background: #000;
  border: 1px solid var(--line);
}
.brand-card-image {
  width: 100%; display: block; border-radius: 14px;
}
.brand-card-video {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  border: 0;
  border-radius: 14px;
}
/* Máscara para esconder marca d'água "Veo" no canto inferior direito do vídeo.
   Como o fundo do vídeo é preto puro, podemos cobrir totalmente sem efeito visível. */
/* Máscara apenas no cantinho do "Veo" — pequena e sólida, sem invadir o anel dourado. */
.brand-card-video-mask {
  position: absolute;
  right: 0; bottom: 0;
  width: 11%; height: 9%;
  background: #000;
  pointer-events: none;
  z-index: 2;
}
.brand-card-image-glow {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at center, transparent 60%, rgba(201, 149, 42, 0.18) 100%);
  pointer-events: none;
  z-index: 3;
}

.brand-card-footer {
  display: flex; align-items: stretch; gap: 0;
  margin-top: 22px; padding-top: 22px;
  border-top: 1px solid var(--line);
}
.kpi { flex: 1; display: flex; flex-direction: column; gap: 4px; padding: 0 14px; }
.kpi:first-child { padding-left: 0; }
.kpi:last-child { padding-right: 0; }
.kpi-divider { width: 1px; background: var(--line); }
.kpi-value {
  font-family: var(--serif); font-size: 1.5rem; font-weight: 500;
  color: var(--gold-deep); line-height: 1;
}
.kpi-label {
  font-family: var(--mono); font-size: 0.66rem;
  color: var(--text-muted); letter-spacing: 0.06em;
}

.scroll-down-btn {
  align-self: flex-end;
  display: inline-flex; align-items: center; gap: 10px;
  min-height: 44px;
  padding: 12px 20px;
  background: transparent;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--gold-light); cursor: pointer;
  font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.12em;
  transition: all 200ms ease;
}
.scroll-down-btn:hover {
  border-color: var(--gold); background: rgba(231, 185, 72, 0.08);
  color: var(--gold-soft);
}
.scroll-down-arrow {
  display: inline-block; transition: transform 250ms ease;
}
.scroll-down-btn:hover .scroll-down-arrow { transform: translateY(2px); }

/* === Dashboard === */
.dashboard-section { padding-top: 0; }
.dashboard-divider {
  display: flex; align-items: center; gap: 18px;
  margin-bottom: 56px;
}
.dashboard-divider-line {
  flex: 1; height: 1px;
  background: linear-gradient(90deg, transparent, var(--line-strong), transparent);
}
.dashboard-divider-label {
  font-family: var(--mono); font-size: 0.78rem;
  letter-spacing: 0.24em; text-transform: uppercase;
  color: var(--gold-light);
}
.dashboard-grid {
  display: grid; grid-template-columns: 0.85fr 1.15fr; gap: 56px;
  align-items: start;
}

/* Painel esquerdo */
.panel-header {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 18px;
  font-family: var(--mono); font-size: 0.74rem;
  color: var(--text-muted);
}
.status-dot {
  width: 8px; height: 8px; border-radius: 2px;
  background: #4ade80; box-shadow: 0 0 10px #4ade80;
}
.panel-header-mono {
  margin-left: auto;
  color: var(--gold); letter-spacing: 0.18em;
}

.section-title {
  font-family: var(--serif); font-size: 2.6rem; font-weight: 400;
  font-variation-settings: "opsz" 96, "SOFT" 50, "WONK" 1;
  letter-spacing: -0.02em; line-height: 1.05;
  color: var(--text); margin: 0 0 14px;
}
.title-period { color: var(--gold); }
.section-desc {
  color: var(--text-muted); line-height: 1.7;
  margin: 0 0 28px; max-width: 460px;
}

.metrics-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 24px; }
.metric-card {
  position: relative;
  padding: 22px 20px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--paper-card);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: 0 12px 28px rgba(15, 18, 28, 0.05);
  transition: border-color 200ms ease, transform 200ms ease, box-shadow 200ms ease;
}
.metric-card:hover {
  border-color: var(--line-strong); transform: translateY(-2px);
  box-shadow: 0 18px 40px rgba(15, 18, 28, 0.08);
}
.metric-label-top {
  font-family: var(--mono); font-size: 0.65rem;
  letter-spacing: 0.22em; text-transform: uppercase;
  color: var(--gold); margin-bottom: 8px;
}
.metric-value {
  font-family: var(--serif); font-size: 1.7rem; font-weight: 500;
  color: var(--text); line-height: 1; margin-bottom: 10px;
}
.metric-label { font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; }

.graph-preview {
  margin: 28px 0;
  background: var(--paper-card-strong);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 12px 32px rgba(15, 18, 28, 0.06);
}
.graph-preview-tag { color: var(--text-muted) !important; }
.graph-preview-mono { color: var(--mint, #3FB77C) !important; }
.graph-preview-header { border-bottom-color: var(--line) !important; }
.graph-preview-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 6px 10px; border-bottom: 1px solid var(--line);
  margin-bottom: 8px;
}
.graph-preview-tag {
  font-family: var(--mono); font-size: 0.7rem;
  color: var(--gold-light); letter-spacing: 0.12em;
}
.graph-preview-mono {
  font-family: var(--mono); font-size: 0.66rem;
  color: #4ade80; letter-spacing: 0.18em;
}
.graph-svg { width: 100%; height: auto; display: block; }

.steps-container {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 28px;
  background: var(--paper-card);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: 0 12px 32px rgba(15, 18, 28, 0.06);
}
.steps-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 22px;
  font-family: var(--mono); font-size: 0.78rem;
  color: var(--gold-light); letter-spacing: 0.12em;
}
.diamond-icon { font-size: 1.1rem; line-height: 1; color: var(--gold); }
.steps-header-meta { margin-left: auto; color: var(--text-muted); }
.workflow-list { display: flex; flex-direction: column; gap: 0; }
.workflow-item {
  display: grid; grid-template-columns: auto 1fr auto;
  align-items: flex-start; gap: 18px;
  padding: 16px 0;
  border-top: 1px solid var(--line);
  transition: border-color 200ms ease;
}
.workflow-item:first-child { border-top: none; padding-top: 0; }
.workflow-item:hover { border-color: var(--line-strong); }
.step-num {
  font-family: var(--mono); font-weight: 600;
  font-size: 0.86rem; color: var(--gold);
  letter-spacing: 0.04em;
  padding-top: 2px;
}
.step-info { flex: 1; }
.step-title {
  font-family: var(--serif); font-size: 1.1rem; font-weight: 500;
  color: var(--text); margin-bottom: 4px; line-height: 1.3;
}
.step-desc { font-size: 0.84rem; color: var(--text-muted); line-height: 1.55; }
.step-tick {
  font-family: var(--mono); color: var(--gold-light); opacity: 0.5;
  align-self: center;
  transition: transform 250ms ease, opacity 250ms ease;
}
.workflow-item:hover .step-tick { opacity: 1; transform: translateX(4px); }

/* Pipeline e console */
.right-panel { display: flex; flex-direction: column; gap: 28px; }
.pipeline-card {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
  background: var(--paper-card);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  box-shadow: 0 12px 32px rgba(15, 18, 28, 0.06);
}
.pipeline-card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 6px 12px; border-bottom: 1px solid var(--line);
  margin-bottom: 12px;
}
.pipeline-card-title {
  font-family: var(--serif); font-size: 1.1rem; font-weight: 500;
  color: var(--text);
}
.pipeline-card-mono {
  font-family: var(--mono); font-size: 0.7rem;
  color: var(--gold-light); letter-spacing: 0.14em;
}
.pipeline-svg { width: 100%; height: auto; display: block; border-radius: 12px; }

.console-box {
  border: 1px solid var(--line-strong);
  border-radius: 18px;
  background: var(--paper-card-strong);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 24px 60px rgba(15, 18, 28, 0.10), inset 0 1px 0 rgba(255, 255, 255, 0.6);
  overflow: hidden;
}
.console-box-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px;
  background: rgba(201, 149, 42, 0.06);
  border-bottom: 1px solid var(--line);
}
.console-box-title {
  font-family: var(--serif); font-size: 1.15rem; font-weight: 500;
  color: var(--text);
}
.console-box-mono {
  font-family: var(--mono); font-size: 0.72rem;
  color: var(--gold-light); letter-spacing: 0.14em;
}
.console-section { padding: 24px 24px 8px; }
.console-section.btn-section { padding: 16px 24px 24px; }
.console-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
  font-family: var(--mono); font-size: 0.74rem; color: var(--text-muted);
}
.console-label { display: inline-flex; align-items: center; gap: 8px; color: var(--gold-light); }
.console-label-num {
  font-weight: 700; padding: 2px 7px;
  background: rgba(201, 149, 42, 0.14);
  border: 1px solid var(--line-strong);
  border-radius: 6px; color: var(--gold-light);
}
.console-meta { color: var(--text-muted); }

.upload-zone {
  position: relative;
  border: 1px dashed rgba(201, 149, 42, 0.45);
  border-radius: 12px;
  min-height: 180px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 250ms ease;
  background: rgba(255, 255, 255, 0.55);
}
.upload-zone.has-files { align-items: flex-start; }
.upload-zone:hover {
  border-color: var(--gold);
  background: rgba(231, 185, 72, 0.06);
  box-shadow: inset 0 0 0 1px rgba(231, 185, 72, 0.10);
}
.upload-zone.drag-over {
  border-color: var(--gold-light); border-style: solid;
  background: rgba(231, 185, 72, 0.10);
}
.upload-placeholder { text-align: center; padding: 24px; }
.upload-icon {
  width: 44px; height: 44px;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 14px;
  color: var(--gold-light);
  background: rgba(231, 185, 72, 0.06);
}
.upload-title {
  font-family: var(--serif); font-size: 1.1rem; font-weight: 500;
  color: var(--text); margin-bottom: 6px;
}
.upload-hint {
  font-family: var(--mono); font-size: 0.74rem; color: var(--text-muted);
}

.file-list { width: 100%; padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.file-item {
  display: flex; align-items: center; gap: 10px;
  background: rgba(255, 255, 255, 0.85);
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 10px;
  font-family: var(--mono); font-size: 0.82rem; color: var(--text);
}
.file-icon { color: var(--gold-light); display: inline-flex; }
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.remove-btn {
  background: transparent; border: none; cursor: pointer;
  font-size: 1.3rem; line-height: 1;
  color: var(--text-muted);
  width: 24px; height: 24px; border-radius: 6px;
  display: inline-flex; align-items: center; justify-content: center;
  transition: all 200ms ease;
}
.remove-btn:hover { color: #ef4444; background: rgba(239, 68, 68, 0.10); }

.upload-error {
  margin-top: 10px;
  font-family: var(--mono); font-size: 0.78rem; color: #f87171;
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.22);
  padding: 8px 12px; border-radius: 8px;
}

.console-divider {
  display: flex; align-items: center; padding: 0 24px;
}
.console-divider::before,
.console-divider::after {
  content: ''; flex: 1; height: 1px;
  background: var(--line);
}
.console-divider span {
  padding: 0 14px;
  font-family: var(--mono); font-size: 0.66rem;
  color: var(--gold-light); letter-spacing: 0.18em; text-transform: uppercase;
}

.input-wrapper {
  position: relative;
  border: 1px solid var(--line-strong);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  transition: border-color 200ms ease, box-shadow 200ms ease;
}
.input-wrapper:focus-within {
  border-color: var(--gold);
  box-shadow: 0 0 0 4px rgba(201, 149, 42, 0.10);
}
.code-input {
  width: 100%; border: none; background: transparent;
  padding: 18px 20px 30px;
  font-family: var(--mono); font-size: 0.92rem;
  line-height: 1.65; color: var(--text);
  resize: vertical; outline: none; min-height: 150px;
}
.code-input::placeholder { color: var(--text-faint); }
.model-badge {
  position: absolute; bottom: 8px; right: 14px;
  font-family: var(--mono); font-size: 0.68rem;
  color: var(--gold-light); opacity: 0.7;
  letter-spacing: 0.06em;
}

.start-engine-btn {
  width: 100%;
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px;
  background: linear-gradient(135deg, #c9952a 0%, #8a6519 100%);
  color: #0a0e1a;
  border: 1px solid rgba(231, 185, 72, 0.55);
  border-radius: 12px;
  font-family: var(--mono); font-size: 0.95rem; font-weight: 700;
  letter-spacing: 0.18em; text-transform: uppercase;
  cursor: pointer;
  transition: all 250ms ease;
  box-shadow: 0 12px 32px rgba(201, 149, 42, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.18);
  position: relative; overflow: hidden;
}
.start-engine-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 44px rgba(201, 149, 42, 0.40), inset 0 1px 0 rgba(255, 255, 255, 0.22);
  filter: brightness(1.08);
}
.start-engine-btn:not(:disabled):active { transform: translateY(0); }
.start-engine-btn:disabled {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.78), rgba(245, 242, 234, 0.78));
  color: rgba(20, 22, 30, 0.42);
  border: 1px dashed rgba(201, 149, 42, 0.45);
  cursor: not-allowed;
  box-shadow: 0 6px 18px rgba(20, 22, 30, 0.05);
}
.btn-arrow {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(20, 22, 30, 0.12);
  transition: transform 250ms ease;
}
.start-engine-btn:disabled .btn-arrow {
  background: rgba(20, 22, 30, 0.06);
  color: rgba(20, 22, 30, 0.32);
}
.start-engine-btn:not(:disabled):hover .btn-arrow { transform: translateX(4px); }

.btn-hint {
  margin: 12px 0 0;
  font-family: var(--mono); font-size: 0.72rem;
  color: var(--text-faint); text-align: center;
}

/* === HistoryDatabase wrapper (modo paper — sem overrides, herda estilo light original) === */
.history-wrap {
  position: relative; z-index: 1;
  margin-top: 60px;
  padding: 40px 0 24px;
  border-top: 1px solid var(--line);
}

/* === Footer === */
.footer {
  position: relative; z-index: 1;
  margin-top: 80px; padding: 40px;
  border-top: 1px solid var(--line);
}
.footer-inner {
  max-width: 1400px; margin: 0 auto;
  display: flex; justify-content: space-between; align-items: center;
}
.footer-brand {
  font-family: var(--mono); font-weight: 700;
  letter-spacing: 0.24em; color: var(--gold-deep); margin-right: 14px;
}
.footer-meta {
  font-family: var(--mono); font-size: 0.74rem;
  color: var(--text-muted); letter-spacing: 0.06em;
}

/* === Responsive === */
@media (max-width: 1100px) {
  .hero-section { grid-template-columns: 1fr; gap: 56px; }
  .dashboard-grid { grid-template-columns: 1fr; gap: 48px; }
  .main-content { padding: 60px 28px 40px; }
  .nav-meta { display: none; }
}

@media (max-width: 640px) {
  .main-content { padding: 40px 18px 24px; }
  .navbar { padding: 12px 12px 0; }
  .nav-inner { padding: 10px 14px; }
  .nav-brand-sub { display: none; }
  .github-link span:not(.arrow) { display: none; }
  .display-title { font-size: 2.2rem; }
  .hero-pillars { grid-template-columns: 1fr; }
  .metrics-row { grid-template-columns: 1fr; }
  .brand-card-footer { flex-direction: column; gap: 14px; }
  .kpi-divider { width: 100%; height: 1px; }
  .kpi { padding: 0; }
  .footer-inner { flex-direction: column; gap: 12px; text-align: center; }
}

/* === Selection + Focus (linha INTEIA) === */
.home-container :deep(::selection) { background: var(--gold); color: var(--ink); }
.home-container :focus-visible {
  outline: 2px solid var(--gold-light);
  outline-offset: 3px; border-radius: 2px;
}

/* prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
