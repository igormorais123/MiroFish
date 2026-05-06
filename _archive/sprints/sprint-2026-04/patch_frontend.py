"""Patch Step4Report.vue to use real cost data from API."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/opt/mirofish-inteia/frontend/src/components/Step4Report.vue"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import for getReportCosts
content = content.replace(
    "import { getAgentLog, getConsoleLog } from '../api/report'",
    "import { getAgentLog, getConsoleLog, getReportCosts } from '../api/report'"
)
print("1. Added import")

# 2. Replace hardcoded costEstimates
old_block = """// Estimativa de custos por etapa
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
const primaryModel = ref('mirofish-smart')"""

new_block = """// Custos reais de tokens por etapa (carregados da API)
const costData = ref(null)
const costLoading = ref(false)

const STAGE_LABELS = {
  graphrag: 'Construção do Grafo (GraphRAG)',
  profiles: 'Geração de Perfis',
  simulation: 'Simulação OASIS',
  report: 'Relatório ReACT',
  helena: 'Helena Strategos (análise final)',
}

const costEstimates = computed(() => {
  if (!costData.value) {
    return [
      { name: 'Construção do Grafo (GraphRAG)', tokens: 0, cost: 0, model: 'BestFREE' },
      { name: 'Geração de Perfis', tokens: 0, cost: 0, model: 'BestFREE' },
      { name: 'Simulação OASIS', tokens: 0, cost: 0, model: 'BestFREE' },
      { name: 'Relatório ReACT', tokens: 0, cost: 0, model: '' },
      { name: 'Helena Strategos (análise final)', tokens: 0, cost: 0, model: '' },
    ]
  }
  const stages = costData.value.stages || {}
  return Object.entries(STAGE_LABELS).map(([key, label]) => {
    const s = stages[key] || {}
    return {
      name: label + (s.total_requests ? ` (${s.total_requests} chamadas)` : ''),
      tokens: s.total_tokens || 0,
      cost: s.cost_usd || 0,
      model: s.model || '',
    }
  })
})

const totalTokens = computed(() => costEstimates.value.reduce((sum, s) => sum + s.tokens, 0))
const totalCost = computed(() => costEstimates.value.reduce((sum, s) => sum + s.cost, 0))
const primaryModel = computed(() => {
  if (!costData.value) return ''
  const report = costData.value.stages?.report
  return report?.model || ''
})

const fetchCosts = async () => {
  if (!props.reportId || costLoading.value) return
  costLoading.value = true
  try {
    const res = await getReportCosts(props.reportId)
    if (res.data?.success) {
      costData.value = res.data.data
    }
  } catch (err) {
    console.warn('Failed to fetch costs:', err)
  } finally {
    costLoading.value = false
  }
}"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print("2. Replaced cost block with API-driven version")
else:
    print("2. WARN: old cost block not found — trying line-by-line match")
    # Try to find and replace by key markers
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if '// Estimativa de custos por etapa' in line:
            start_idx = i
        if start_idx and "primaryModel = ref(" in line:
            end_idx = i + 1
            break
    if start_idx and end_idx:
        lines[start_idx:end_idx] = new_block.split('\n')
        content = '\n'.join(lines)
        print("2. Replaced cost block (line-by-line match)")
    else:
        print(f"2. ERROR: Could not find cost block (start={start_idx}, end={end_idx})")

# 3. Add fetchCosts call when report is complete
# Find where isComplete is set to true and add fetchCosts
if 'fetchCosts()' not in content:
    content = content.replace(
        "isComplete.value = true",
        "isComplete.value = true\n      fetchCosts()",
        1  # Only first occurrence
    )
    print("3. Added fetchCosts() call on report complete")
else:
    print("3. fetchCosts already present")

# 4. Add model display in cost panel (show which model was used)
# In the cost-values div, add model info
old_values = """<div class="cost-values">
                    <span class="cost-tokens">{{ formatTokens(stage.tokens) }} tokens</span>
                    <span class="cost-usd">${{ stage.cost.toFixed(4) }}</span>
                  </div>"""

new_values = """<div class="cost-values">
                    <span class="cost-tokens">{{ formatTokens(stage.tokens) }} tokens</span>
                    <span class="cost-usd">${{ stage.cost.toFixed(4) }}</span>
                    <span v-if="stage.model" class="cost-model">{{ stage.model }}</span>
                  </div>"""

if old_values in content:
    content = content.replace(old_values, new_values)
    print("4. Added model display in cost panel")
else:
    print("4. SKIP: cost-values pattern not found exactly")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("\nFrontend patched!")
