"""Add print, share and cost calculator features to Step4Report.vue"""
import sys

filepath = sys.argv[1] if len(sys.argv) > 1 else "/opt/mirofish-inteia/frontend/src/components/Step4Report.vue"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ============================================================
# 1. Add action toolbar after header-divider (print, share, cost)
# ============================================================

old_header_divider = '            <div class="header-divider"></div>'

new_header_with_toolbar = '''            <div class="header-divider"></div>

            <!-- Toolbar: Imprimir, Compartilhar, Custos -->
            <div v-if="isComplete" class="report-toolbar">
              <button class="toolbar-btn" @click="handlePrint" title="Imprimir relatório">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="6 9 6 2 18 2 18 9"></polyline>
                  <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                  <rect x="6" y="14" width="12" height="8"></rect>
                </svg>
                <span>Imprimir</span>
              </button>

              <div class="toolbar-divider"></div>

              <button class="toolbar-btn" @click="shareWhatsApp" title="Compartilhar via WhatsApp">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                <span>WhatsApp</span>
              </button>

              <button class="toolbar-btn" @click="shareLink" title="Copiar link">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                </svg>
                <span>Link</span>
              </button>

              <button class="toolbar-btn" @click="shareEmail" title="Enviar por e-mail">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <span>E-mail</span>
              </button>

              <div class="toolbar-divider"></div>

              <button class="toolbar-btn" :class="{ active: showCostPanel }" @click="showCostPanel = !showCostPanel" title="Custos estimados">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
                <span>Custos</span>
              </button>
            </div>

            <!-- Painel de Custos -->
            <div v-if="showCostPanel && isComplete" class="cost-panel">
              <div class="cost-header">
                <span class="cost-title">Estimativa de Tokens e Custos</span>
                <button class="cost-close" @click="showCostPanel = false">&times;</button>
              </div>
              <div class="cost-grid">
                <div class="cost-row" v-for="(stage, idx) in costEstimates" :key="idx">
                  <div class="cost-stage">
                    <span class="cost-stage-num">{{ String(idx + 1).padStart(2, '0') }}</span>
                    <span class="cost-stage-name">{{ stage.name }}</span>
                  </div>
                  <div class="cost-values">
                    <span class="cost-tokens">{{ formatTokens(stage.tokens) }} tokens</span>
                    <span class="cost-usd">US$ {{ stage.cost.toFixed(4) }}</span>
                  </div>
                </div>
              </div>
              <div class="cost-total">
                <span>Total estimado</span>
                <span class="cost-total-value">
                  <span class="cost-tokens">{{ formatTokens(totalTokens) }} tokens</span>
                  <span class="cost-usd">US$ {{ totalCost.toFixed(4) }}</span>
                </span>
              </div>
              <div class="cost-note">
                Valores estimados com base nos modelos utilizados via OmniRoute.
                Modelo principal: {{ primaryModel || 'mirofish-smart' }}
              </div>
            </div>'''

if old_header_divider in content:
    content = content.replace(old_header_divider, new_header_with_toolbar, 1)
    changes += 1
    print("FEATURE 1: Added toolbar (print, share, cost)")

# ============================================================
# 2. Add JavaScript methods and state for new features
# ============================================================

# Find the script section to add state and methods
old_is_complete = "const isComplete = ref(false)"

new_state = """const isComplete = ref(false)
const showCostPanel = ref(false)
const linkCopied = ref(false)

// Estimativa de custos por etapa
const costEstimates = computed(() => {
  const sections = reportOutline.value?.sections || []
  const sectionCount = sections.length

  // Estimativas baseadas em modelos OmniRoute
  // BestFREE (DeepSeek): ~$0 | mirofish-smart: ~$0.003/1K tokens
  const stages = [
    { name: 'Construção do Grafo (GraphRAG)', tokens: 427 * 800, cost: 0 },  // BestFREE
    { name: 'Geração de Perfis (21 agentes)', tokens: 21 * 2000, cost: 0 },  // BestFREE
    { name: 'Simulação OASIS (120 rodadas)', tokens: 120 * 3000, cost: 0 },  // BestFREE
    { name: `Relatório ReACT (${sectionCount} seções)`, tokens: sectionCount * 12000, cost: sectionCount * 12000 * 0.000003 },
    { name: 'Helena Strategos (análise final)', tokens: 15000, cost: 15000 * 0.000015 },  // opus-tasks
  ]
  return stages
})

const totalTokens = computed(() => costEstimates.value.reduce((sum, s) => sum + s.tokens, 0))
const totalCost = computed(() => costEstimates.value.reduce((sum, s) => sum + s.cost, 0))
const primaryModel = ref('mirofish-smart')

const formatTokens = (n) => {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(0) + 'K'
  return String(n)
}

// Impressão formatada
const handlePrint = () => {
  const printContent = document.querySelector('.report-content-wrapper')
  if (!printContent) return

  const printWindow = window.open('', '_blank')
  const title = reportOutline.value?.title || 'Relatório MiroFish'

  printWindow.document.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    @page {
      size: A4;
      margin: 2.5cm 2cm;
    }

    body {
      font-family: 'Inter', sans-serif;
      font-size: 11pt;
      line-height: 1.7;
      color: #1a1a1a;
      background: white;
    }

    .print-header {
      text-align: center;
      margin-bottom: 2em;
      padding-bottom: 1.5em;
      border-bottom: 2px solid #c9952a;
    }

    .print-brand {
      font-size: 10pt;
      letter-spacing: 4px;
      text-transform: uppercase;
      color: #c9952a;
      margin-bottom: 0.5em;
    }

    .print-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 22pt;
      font-weight: 700;
      color: #111;
      line-height: 1.2;
      margin-bottom: 0.5em;
    }

    .print-summary {
      font-size: 10pt;
      color: #555;
      max-width: 80%;
      margin: 0 auto;
      font-style: italic;
    }

    .print-meta {
      margin-top: 1em;
      font-size: 8pt;
      color: #888;
    }

    h2 {
      font-family: 'Cormorant Garamond', serif;
      font-size: 16pt;
      font-weight: 600;
      color: #1a1a1a;
      margin: 1.5em 0 0.8em;
      padding-bottom: 0.3em;
      border-bottom: 1px solid #e5e5e5;
      page-break-after: avoid;
    }

    p { margin-bottom: 0.8em; text-align: justify; }

    strong { color: #111; }

    blockquote {
      margin: 1em 0;
      padding: 0.8em 1.2em;
      border-left: 3px solid #c9952a;
      background: #faf8f3;
      font-style: italic;
      color: #333;
      page-break-inside: avoid;
    }

    ul, ol { margin: 0.5em 0 0.8em 1.5em; }
    li { margin-bottom: 0.3em; }

    .print-footer {
      margin-top: 3em;
      padding-top: 1em;
      border-top: 1px solid #ddd;
      font-size: 8pt;
      color: #999;
      text-align: center;
    }

    .print-footer a { color: #c9952a; text-decoration: none; }

    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .no-print { display: none !important; }
    }
  </style>
</head>
<body>
  <div class="print-header">
    <div class="print-brand">INTEIA &middot; MiroFish Lab</div>
    <div class="print-title">${title}</div>
    <div class="print-summary">${reportOutline.value?.summary || ''}</div>
    <div class="print-meta">Gerado em ${new Date().toLocaleDateString('pt-BR')} &middot; Simulação ${props.simulationId || ''}</div>
  </div>
  ${Array.from(document.querySelectorAll('.report-section-item')).map((s, i) => {
    const titleEl = s.querySelector('.section-title')
    const contentEl = s.querySelector('.generated-content')
    if (!contentEl) return ''
    return '<h2>' + (titleEl?.textContent || 'Seção ' + (i+1)) + '</h2>' + contentEl.innerHTML
  }).join('')}
  <div class="print-footer">
    Relatório gerado por <a href="https://inteia.com.br">INTEIA</a> MiroFish Lab &middot; Simulação de cenários com agentes sintéticos
  </div>
</body>
</html>`)
  printWindow.document.close()
  setTimeout(() => { printWindow.print() }, 500)
}

// Compartilhamento
const getShareText = () => {
  const title = reportOutline.value?.title || 'Relatório MiroFish'
  const summary = reportOutline.value?.summary || ''
  return title + '\\n\\n' + summary + '\\n\\nGerado por INTEIA MiroFish Lab'
}

const getShareUrl = () => {
  return window.location.href
}

const shareWhatsApp = () => {
  const text = encodeURIComponent(getShareText() + '\\n\\n' + getShareUrl())
  window.open('https://wa.me/?text=' + text, '_blank')
}

const shareLink = async () => {
  try {
    await navigator.clipboard.writeText(getShareUrl())
    linkCopied.value = true
    setTimeout(() => { linkCopied.value = false }, 2000)
  } catch {
    // Fallback
    const input = document.createElement('input')
    input.value = getShareUrl()
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    linkCopied.value = true
    setTimeout(() => { linkCopied.value = false }, 2000)
  }
}

const shareEmail = () => {
  const subject = encodeURIComponent(reportOutline.value?.title || 'Relatório MiroFish')
  const body = encodeURIComponent(getShareText() + '\\n\\n' + getShareUrl())
  window.location.href = 'mailto:?subject=' + subject + '&body=' + body
}"""

if old_is_complete in content:
    content = content.replace(old_is_complete, new_state, 1)
    changes += 1
    print("FEATURE 2: Added state and methods (print, share, cost)")

# ============================================================
# 3. Add CSS for new features
# ============================================================

# Find the end of the style section to add new styles
css_addition = """

/* ============================================ */
/* Toolbar: Print, Share, Cost                  */
/* ============================================ */

.report-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 0;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.04);
  color: #aaa;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: rgba(201, 149, 42, 0.12);
  border-color: rgba(201, 149, 42, 0.3);
  color: #c9952a;
}

.toolbar-btn.active {
  background: rgba(201, 149, 42, 0.15);
  border-color: #c9952a;
  color: #c9952a;
}

.toolbar-btn svg { flex-shrink: 0; }

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: rgba(255,255,255,0.08);
  margin: 0 4px;
}

/* Cost Panel */
.cost-panel {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(201, 149, 42, 0.2);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  font-size: 12px;
}

.cost-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.cost-title {
  font-weight: 600;
  color: #c9952a;
  font-size: 13px;
}

.cost-close {
  background: none;
  border: none;
  color: #666;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
}

.cost-close:hover { color: #aaa; }

.cost-grid { display: flex; flex-direction: column; gap: 8px; }

.cost-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: rgba(255,255,255,0.03);
  border-radius: 4px;
}

.cost-stage {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cost-stage-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #555;
}

.cost-stage-name { color: #bbb; }

.cost-values {
  display: flex;
  gap: 16px;
  align-items: center;
}

.cost-tokens {
  font-family: 'JetBrains Mono', monospace;
  color: #888;
  font-size: 11px;
}

.cost-usd {
  font-family: 'JetBrains Mono', monospace;
  color: #c9952a;
  font-weight: 600;
  min-width: 80px;
  text-align: right;
}

.cost-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255,255,255,0.08);
  font-weight: 600;
  color: #ddd;
}

.cost-total-value {
  display: flex;
  gap: 16px;
  align-items: center;
}

.cost-note {
  margin-top: 10px;
  font-size: 10px;
  color: #555;
  font-style: italic;
}

/* Print-specific */
@media print {
  .report-toolbar,
  .cost-panel,
  .right-panel,
  .next-step-btn,
  .workflow-steps-container,
  .system-logs { display: none !important; }

  .left-panel {
    width: 100% !important;
    max-width: 100% !important;
    overflow: visible !important;
  }

  .report-content-wrapper {
    padding: 0 !important;
  }
}"""

# Find </style> tag and insert before it
if "</style>" in content:
    content = content.replace("</style>", css_addition + "\n</style>", 1)
    changes += 1
    print("FEATURE 3: Added CSS for toolbar, cost panel, print")

with open(filepath, "w") as f:
    f.write(content)

print(f"\nTotal: {changes} features added")
