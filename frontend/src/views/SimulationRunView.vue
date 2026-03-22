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
          <span class="step-num">Etapa 3/5</span>
          <span class="step-name">Início da simulação</span>
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
          :currentPhase="3"
          :isSimulating="isSimulating"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step3 Iniciar simulação -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step3Simulation
          :simulationId="currentSimulationId"
          :maxRounds="maxRounds"
          :minutesPerRound="minutesPerRound"
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, getSimulationConfig, stopSimulation, closeSimulationEnv, getEnvStatus } from '../api/simulation'

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
// Obter maxRounds dos parâmetros de query na inicialização, garantindo acesso imediato pelos componentes filhos
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds) : null)
const minutesPerRound = ref(30) // Padrao de 30 minutos por rodada
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
  if (currentStatus.value === 'completed') return 'Concluído'
  return 'Executando'
})

const isSimulating = computed(() => currentStatus.value === 'processing')

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('pt-BR', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
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

const handleGoBack = async () => {
  // Antes de voltar ao Step 2, encerrar a simulação em execução
  addLog('Preparando retorno para a etapa 2. Encerrando a simulação...')
  
  // Parar polling
  stopGraphRefresh()
  
  try {
    // Tentar primeiro encerrar o ambiente de simulação graciosamente
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('Encerrando o ambiente de simulação...')
      try {
        await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10
        })
        addLog('✓ Ambiente de simulação encerrado')
      } catch (closeErr) {
        addLog('Falha ao encerrar o ambiente. Tentando interrupção forçada...')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulação interrompida à força')
        } catch (stopErr) {
          addLog(`Falha na interrupção forçada: ${stopErr.message}`)
        }
      }
    } else {
      // Ambiente não está rodando, verificar se precisa parar o processo
      if (isSimulating.value) {
        addLog('Encerrando o processo da simulação...')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulação interrompida')
        } catch (err) {
          addLog(`Falha ao interromper a simulação: ${err.message}`)
        }
      }
    }
  } catch (err) {
    addLog(`Falha ao verificar o estado da simulação: ${err.message}`)
  }
  
  // Voltar ao Step 2 (configuração do ambiente)
  router.push({ name: 'Simulation', params: { simulationId: currentSimulationId.value } })
}

const handleNextStep = () => {
  // O componente Step3Simulation trata diretamente a geração do relatório e navegação de rota
  // Este metodo serve apenas como backup
  addLog('Entrando na etapa 4: geração de relatório')
}

// --- Data Logic ---
const loadSimulationData = async () => {
  try {
    addLog(`Carregando dados da simulação: ${currentSimulationId.value}`)
    
    // Obter informações da simulação
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // Obter simulation config para obter minutes_per_round
      try {
        const configRes = await getSimulationConfig(currentSimulationId.value)
        if (configRes.success && configRes.data?.time_config?.minutes_per_round) {
          minutesPerRound.value = configRes.data.time_config.minutes_per_round
          addLog(`Configuração de tempo: ${minutesPerRound.value} minutos por rodada`)
        }
      } catch (configErr) {
        addLog(`Falha ao obter a configuração de tempo. Usando padrão: ${minutesPerRound.value} min/rodada`)
      }
      
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
  // Durante simulação, atualização automatica não exibe loading em tela cheia para evitar cintilação
  // Exibir loading em atualização manual ou carregamento inicial
  if (!isSimulating.value) {
    graphLoading.value = true
  }
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      if (!isSimulating.value) {
        addLog('Dados do grafo carregados com sucesso')
      }
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

// --- Auto Refresh Logic ---
let graphRefreshTimer = null

const startGraphRefresh = () => {
  if (graphRefreshTimer) return
  addLog('Atualização automática do grafo iniciada (30s)')
  // Atualizar imediatamente uma vez, depois a cada 30 segundos
  graphRefreshTimer = setInterval(refreshGraph, 30000)
}

const stopGraphRefresh = () => {
  if (graphRefreshTimer) {
    clearInterval(graphRefreshTimer)
    graphRefreshTimer = null
    addLog('Atualização automática do grafo interrompida')
  }
}

watch(isSimulating, (newValue) => {
  if (newValue) {
    startGraphRefresh()
  } else {
    stopGraphRefresh()
  }
}, { immediate: true })

onMounted(() => {
  addLog('Tela de execução da simulação inicializada')
  
  // Registrar configuração de maxRounds (valor já obtido dos parâmetros de query na inicialização)
  if (maxRounds.value) {
    addLog(`Total de rodadas personalizado: ${maxRounds.value}`)
  }
  
  loadSimulationData()
})

onUnmounted(() => {
  stopGraphRefresh()
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

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
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

