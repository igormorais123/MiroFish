<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand-lockup" @click="router.push('/')">
          <div class="brand-mark">IA</div>
          <div class="brand-copy">
            <div class="brand">INTEIA</div>
            <div class="brand-sub">MiroFish Lab</div>
          </div>
        </div>
      </div>
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: 'Grafo', split: 'Dividido', workbench: 'Painel' }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <div class="workflow-step">
          <span class="step-num">Etapa 2/5</span>
          <span class="step-name">Configuração do ambiente</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Área -->
    <main class="content-area">
      <!-- Left Panel: Graph -->
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="2"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step2 Configuração do ambiente -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step2EnvSetup
          :simulationId="currentSimulationId"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, stopSimulation, getEnvStatus, closeSimulationEnv } from '../api/simulation'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref('split')

// Data State
const currentSimulationId = ref(route.params.simulationId)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Erro'
  if (currentStatus.value === 'completed') return 'Pronto'
  return 'Preparando'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('pt-BR', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleGoBack = () => {
  // Voltar para a página process
  if (projectData.value?.project_id) {
    router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
  } else {
    router.push('/')
  }
}

const handleNextStep = (params = {}) => {
  addLog('Entrando na etapa 3: início da simulação')
  
  // Registrar configuração de rodadas da simulação
  if (params.maxRounds) {
    addLog(`Total de rodadas personalizado: ${params.maxRounds}`)
  } else {
    addLog('Usando o total de rodadas definido automaticamente')
  }
  
  // Construir parâmetros de rota
  const routeParams = {
    name: 'SimulationRun',
    params: { simulationId: currentSimulationId.value }
  }
  
  // Se há rodadas personalizadas, passar via parâmetros de query
  if (params.maxRounds) {
    routeParams.query = { maxRounds: params.maxRounds }
  }
  
  // Navegar para a página Step 3
  router.push(routeParams)
}

// --- Data Logic ---

/**
 * Verificar e encerrar simulação em execução
 * Quando o usuário volta do Step 3 para o Step 2, presume-se que deseja sair da simulação
 */
const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return
  
  try {
    // Verificar primeiro se o ambiente de simulação está ativo
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('Ambiente de simulação em execução detectado. Encerrando...')
      
      // Tentar encerrar o ambiente de simulação graciosamente
      try {
        const closeRes = await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10  // Timeout de 10 segundos
        })
        
        if (closeRes.success) {
          addLog('✓ Ambiente de simulação encerrado')
        } else {
          addLog(`Falha ao encerrar o ambiente de simulação: ${closeRes.error || 'erro desconhecido'}`)
          // Se o encerramento gracioso falhar, tentar parada forçada
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(`Erro ao encerrar o ambiente de simulação: ${closeErr.message}`)
        // Se o encerramento gracioso gerar exceção, tentar parada forçada
        await forceStopSimulation()
      }
    } else {
      // Ambiente não está rodando, mas o processo pode existir, verificar status da simulação
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog('A simulação ainda está marcada como ativa. Interrompendo...')
        await forceStopSimulation()
      }
    }
  } catch (err) {
    // Falha na verificação do ambiente não afeta o fluxo subsequente
    console.warn('Falha ao verificar status da simulação:', err)
  }
}

/**
 * Parar simulação forçadamente
 */
const forceStopSimulation = async () => {
  try {
    const stopRes = await stopSimulation({ simulation_id: currentSimulationId.value })
    if (stopRes.success) {
      addLog('✓ Simulação interrompida à força')
    } else {
      addLog(`Falha ao interromper a simulação: ${stopRes.error || 'erro desconhecido'}`)
    }
  } catch (err) {
    addLog(`Erro ao interromper a simulação: ${err.message}`)
  }
}

const loadSimulationData = async () => {
  try {
    addLog(`Carregando dados da simulação: ${currentSimulationId.value}`)
    
    // Obter informações da simulação
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // Obter informações do projeto
      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(`Projeto carregado: ${projRes.data.project_id}`)
          
          // Obter dados do grafo
          if (projRes.data.graph_id) {
            await loadGraph(projRes.data.graph_id)
          }
        }
      }
    } else {
      addLog(`Falha ao carregar dados da simulação: ${simRes.error || 'erro desconhecido'}`)
    }
  } catch (err) {
    addLog(`Erro ao carregar: ${err.message}`)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('Dados do grafo carregados com sucesso')
    }
  } catch (err) {
    addLog(`Falha ao carregar o grafo: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

onMounted(async () => {
  addLog('Tela de configuração do ambiente inicializada')
  
  // Verificar e encerrar simulação em execução (quando o usuário volta do Step 3)
  await checkAndStopRunningSimulation()
  
  // Carregar dados da simulação
  loadSimulationData()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f7f3ea 0%, #f1ece3 100%);
  overflow: hidden;
  font-family: 'Inter', 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid rgba(11, 20, 38, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: linear-gradient(135deg, rgba(8, 17, 31, 0.98) 0%, rgba(19, 33, 58, 0.98) 100%);
  z-index: 100;
  position: relative;
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #d69e2e 0%, #b97d13 100%);
  color: #fff;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 14px;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 15px;
  letter-spacing: 0.18em;
  color: #fff;
}

.brand-sub {
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(214, 158, 46, 0.92);
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.view-switcher {
  display: flex;
  background: rgba(255,255,255,0.08);
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.7);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: linear-gradient(135deg, #d69e2e 0%, #b97d13 100%);
  color: #fff;
  box-shadow: 0 8px 18px rgba(185, 125, 19, 0.22);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: rgba(214, 158, 46, 0.86);
}

.step-name {
  font-weight: 700;
  color: #fff;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: rgba(255,255,255,0.16);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255,255,255,0.72);
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #d69e2e; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid rgba(11, 20, 38, 0.08);
}
</style>

