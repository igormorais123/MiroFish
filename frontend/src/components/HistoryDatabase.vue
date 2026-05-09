<template>
  <div 
    class="history-database"
    :class="{ 'no-projects': projects.length === 0 && !loading }"
    ref="historyContainer"
  >
    <!-- Decoração de fundo: linhas de grade técnicas (exibidas apenas quando há projetos) -->
    <div v-if="projects.length > 0 || loading" class="tech-grid-bg">
      <div class="grid-pattern"></div>
      <div class="gradient-overlay"></div>
    </div>

    <!-- Área do título -->
    <div class="section-header">
      <div class="section-line"></div>
      <span class="section-title">Histórico de simulações</span>
      <div class="section-line"></div>
    </div>

    <!-- Container de cartões (exibido apenas quando há projetos) -->
    <div v-if="projects.length > 0" class="cards-container" :class="{ expanded: isExpanded }" :style="containerStyle">
      <div 
        v-for="(project, index) in projects" 
        :key="project.simulation_id"
        class="project-card"
        :class="{ expanded: isExpanded, hovering: hoveringCard === index }"
        :style="getCardStyle(index)"
        @mouseenter="hoveringCard = index"
        @mouseleave="hoveringCard = null"
        @click="navigateToProject(project)"
      >
        <!-- Cabeçalho do cartão: simulation_id e status de disponibilidade -->
        <div class="card-header">
          <span class="card-id">{{ formatSimulationId(project.simulation_id) }}</span>
          <div class="card-status-icons">
            <span 
              class="status-icon" 
              :class="{ available: project.project_id, unavailable: !project.project_id }"
              title="Construção do grafo"
            >◇</span>
            <span 
              class="status-icon available" 
              title="Configuração do ambiente"
            >◈</span>
            <span 
              class="status-icon" 
              :class="{ available: project.report_id, unavailable: !project.report_id }"
              title="Relatório analítico"
            >◆</span>
          </div>
        </div>

        <!-- Área da lista de arquivos -->
        <div class="card-files-wrapper">
          <!-- Decoração de canto - estilo visor -->
          <div class="corner-mark top-left-only"></div>
          
          <!-- Lista de arquivos -->
          <div class="files-list" v-if="project.files && project.files.length > 0">
            <div 
              v-for="(file, fileIndex) in project.files.slice(0, 3)" 
              :key="fileIndex"
              class="file-item"
            >
              <span class="file-tag" :class="getFileType(file.filename)">{{ getFileTypeLabel(file.filename) }}</span>
              <span class="file-name">{{ truncateFilename(file.filename, 20) }}</span>
            </div>
            <!-- Se há mais arquivos, exibir indicador -->
            <div v-if="project.files.length > 3" class="files-more">
              +{{ project.files.length - 3 }} arquivos
            </div>
          </div>
          <!-- Placeholder sem arquivos -->
          <div class="files-empty" v-else>
            <span class="empty-file-icon">◇</span>
            <span class="empty-file-text">Sem arquivos</span>
          </div>
        </div>

        <!-- Titulo do cartão (primeiros 20 caracteres do requisito de simulação) -->
        <h3 class="card-title">{{ getSimulationTitle(project.simulation_requirement) }}</h3>

        <!-- Descrição do cartão (requisito de simulação completo) -->
        <p class="card-desc">{{ truncateText(project.simulation_requirement, 55) }}</p>

        <!-- Rodapé do cartão -->
        <div class="card-footer">
          <div class="card-datetime">
            <span class="card-date">{{ formatDate(project.created_at) }}</span>
            <span class="card-time">{{ formatTime(project.created_at) }}</span>
          </div>
          <span class="card-progress" :class="getProgressClass(project)">
            <span class="status-dot">●</span> {{ formatRounds(project) }}
          </span>
        </div>
        
        <!-- Linha decorativa inferior (expande ao passar o mouse) -->
        <div class="card-bottom-line"></div>
      </div>
    </div>

    <!-- Estado de carregamento -->
    <div v-if="loading" class="loading-state">
      <span class="loading-spinner"></span>
      <span class="loading-text">Carregando...</span>
    </div>

    <div v-if="historyError && !loading" class="history-error" role="alert">
      <span>{{ historyError }}</span>
      <button type="button" class="history-retry" @click.stop="loadHistory">
        Tentar novamente
      </button>
    </div>

    <!-- Modal de detalhes do histórico de replay -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="selectedProject" class="modal-overlay" @click.self="closeModal">
          <div class="modal-content">
            <!-- Cabeçalho do modal -->
            <div class="modal-header">
              <div class="modal-title-section">
                <span class="modal-id">{{ formatSimulationId(selectedProject.simulation_id) }}</span>
                <span class="modal-progress" :class="getProgressClass(selectedProject)">
                  <span class="status-dot">●</span> {{ formatRounds(selectedProject) }}
                </span>
                <span class="modal-create-time">{{ formatDate(selectedProject.created_at) }} {{ formatTime(selectedProject.created_at) }}</span>
              </div>
              <button class="modal-close" @click="closeModal">×</button>
            </div>

            <!-- Conteúdo do modal -->
            <div class="modal-body">
              <!-- Requisito de simulação -->
              <div class="modal-section">
                <div class="modal-label">Objetivo da simulação</div>
                <div class="modal-requirement">{{ selectedProject.simulation_requirement || 'Nenhum' }}</div>
              </div>

              <!-- Lista de arquivos -->
              <div class="modal-section">
                <div class="modal-label">Arquivos vinculados</div>
                <div class="modal-files" v-if="selectedProject.files && selectedProject.files.length > 0">
                  <div v-for="(file, index) in selectedProject.files" :key="index" class="modal-file-item">
                    <span class="file-tag" :class="getFileType(file.filename)">{{ getFileTypeLabel(file.filename) }}</span>
                    <span class="modal-file-name">{{ file.filename }}</span>
                  </div>
                </div>
                <div class="modal-empty" v-else>Nenhum arquivo vinculado</div>
              </div>
            </div>

            <!-- Divisor de replay da simulação -->
            <div class="modal-divider">
              <span class="divider-line"></span>
              <span class="divider-text">Revisitar execução</span>
              <span class="divider-line"></span>
            </div>

            <!-- Botões de navegação -->
            <div class="modal-actions">
              <button 
                class="modal-btn btn-project" 
                @click="goToProject"
                :disabled="!selectedProject.project_id"
              >
                <span class="btn-step">Etapa 1</span>
                <span class="btn-icon">◇</span>
                <span class="btn-text">Construção do grafo</span>
              </button>
              <button 
                class="modal-btn btn-simulation" 
                @click="goToSimulation"
              >
                <span class="btn-step">Etapa 2</span>
                <span class="btn-icon">◈</span>
                <span class="btn-text">Configuração do ambiente</span>
              </button>
              <button 
                class="modal-btn btn-report" 
                @click="goToReport"
                :disabled="!selectedProject.report_id"
              >
                <span class="btn-step">Etapa 4</span>
                <span class="btn-icon">◆</span>
                <span class="btn-text">Relatório analítico</span>
              </button>
            </div>
            <!-- Aviso de replay indisponível -->
            <div class="modal-playback-hint">
              <span class="hint-text">As etapas 3 "Início da simulação" e 5 "Interação profunda" precisam ser abertas com a execução ativa e não suportam replay histórico.</span>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getSimulationHistory } from '../api/simulation'

const router = useRouter()
const route = useRoute()

// Estado
const projects = ref([])
const loading = ref(true)
const historyError = ref('')
const isExpanded = ref(false)
const hoveringCard = ref(null)
const historyContainer = ref(null)
const selectedProject = ref(null)  // Projeto selecionado atualmente (para o modal)
let observer = null
let isAnimating = false  // Trava de animação para evitar cintilação
let expandDebounceTimer = null  // Temporizador de debounce
let pendingState = null  // Registra o estado-alvo pendente de execução

// Configuração do layout de cartões - ajustado para proporção mais larga
const CARDS_PER_ROW = 4
const CARD_WIDTH = 280  
const CARD_HEIGHT = 280 
const CARD_GAP = 24

// Calculo dinâmico do estilo de altura do container
const containerStyle = computed(() => {
  if (!isExpanded.value) {
    // Estado recolhido: altura fixa
    return { minHeight: '420px' }
  }
  
  // Estado expandido: calcula a altura dinâmicamente com base na quantidade de cartões
  const total = projects.value.length
  if (total === 0) {
    return { minHeight: '280px' }
  }
  
  const rows = Math.ceil(total / CARDS_PER_ROW)
  // Calcula a altura necessária: linhas * altura do cartão + (linhas-1) * espaçamento + margem inferior
  const expandedHeight = rows * CARD_HEIGHT + (rows - 1) * CARD_GAP + 10
  
  return { minHeight: `${expandedHeight}px` }
})

// Obter estilo do cartão
const getCardStyle = (index) => {
  const total = projects.value.length
  
  if (isExpanded.value) {
    // Estado expandido: layout em grade
    const transition = 'transform 700ms cubic-bezier(0.23, 1, 0.32, 1), opacity 700ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.3s ease, border-color 0.3s ease'

    const col = index % CARDS_PER_ROW
    const row = Math.floor(index / CARDS_PER_ROW)
    
    // Calcula a quantidade de cartões na linha atual, garantindo centralizacao
    const currentRowStart = row * CARDS_PER_ROW
    const currentRowCards = Math.min(CARDS_PER_ROW, total - currentRowStart)
    
    const rowWidth = currentRowCards * CARD_WIDTH + (currentRowCards - 1) * CARD_GAP
    
    const startX = -(rowWidth / 2) + (CARD_WIDTH / 2)
    const colInRow = index % CARDS_PER_ROW
    const x = startX + colInRow * (CARD_WIDTH + CARD_GAP)
    
    // Expande para baixo, aumentando o espaçamento com o título
    const y = 20 + row * (CARD_HEIGHT + CARD_GAP)

    return {
      transform: `translate(${x}px, ${y}px) rotate(0deg) scale(1)`,
      zIndex: 100 + index,
      opacity: 1,
      transition: transition
    }
  } else {
    // Estado recolhido: empilhamento em leque
    const transition = 'transform 700ms cubic-bezier(0.23, 1, 0.32, 1), opacity 700ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.3s ease, border-color 0.3s ease'

    const centerIndex = (total - 1) / 2
    const offset = index - centerIndex
    
    const x = offset * 35
    // Ajusta a posição inicial, próximo ao título com espaçamento adequado
    const y = 25 + Math.abs(offset) * 8
    const r = offset * 3
    const s = 0.95 - Math.abs(offset) * 0.05
    
    return {
      transform: `translate(${x}px, ${y}px) rotate(${r}deg) scale(${s})`,
      zIndex: 10 + index,
      opacity: 1,
      transition: transition
    }
  }
}

// Obter classe de estilo com base no progresso das rodadas
const getProgressClass = (simulation) => {
  const current = simulation.current_round || 0
  const total = simulation.total_rounds || 0
  
  if (total === 0 || current === 0) {
    // Nao iniciado
    return 'not-started'
  } else if (current >= total) {
    // Concluido
    return 'completed'
  } else {
    // Em andamento
    return 'in-progress'
  }
}

// Formatar data (exibir apenas a parte da data)
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toISOString().slice(0, 10)
  } catch {
    return dateStr?.slice(0, 10) || ''
  }
}

// Formatar hora (exibir hora:minuto)
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  } catch {
    return ''
  }
}

// Truncar texto
const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
}

// Gerar título a partir do requisito de simulação (primeiros 20 caracteres)
const getSimulationTitle = (requirement) => {
  if (!requirement) return 'Simulação sem nome'
  const title = requirement.slice(0, 20)
  return requirement.length > 20 ? title + '...' : title
}

// Formatar exibição do simulation_id (primeiros 6 caracteres)
const formatSimulationId = (simulationId) => {
  if (!simulationId) return 'SIM_UNKNOWN'
  const prefix = simulationId.replace('sim_', '').slice(0, 6)
  return `SIM_${prefix.toUpperCase()}`
}

// Formatar exibição de rodadas (rodada atual/total de rodadas)
const formatRounds = (simulation) => {
  const current = simulation.current_round || 0
  const total = simulation.total_rounds || 0
  if (total === 0) return 'Não iniciado'
  return `${current}/${total} rodadas`
}

// Obter tipo de arquivo (para estilização)
const getFileType = (filename) => {
  if (!filename) return 'other'
  const ext = filename.split('.').pop()?.toLowerCase()
  const typeMap = {
    'pdf': 'pdf',
    'doc': 'doc', 'docx': 'doc',
    'xls': 'xls', 'xlsx': 'xls', 'csv': 'xls',
    'ppt': 'ppt', 'pptx': 'ppt',
    'txt': 'txt', 'md': 'txt', 'json': 'code',
    'jpg': 'img', 'jpeg': 'img', 'png': 'img', 'gif': 'img',
    'zip': 'zip', 'rar': 'zip', '7z': 'zip'
  }
  return typeMap[ext] || 'other'
}

// Obter texto do rótulo do tipo de arquivo
const getFileTypeLabel = (filename) => {
  if (!filename) return 'FILE'
  const ext = filename.split('.').pop()?.toUpperCase()
  return ext || 'FILE'
}

// Truncar nome do arquivo (preservando a extensao)
const truncateFilename = (filename, maxLength) => {
  if (!filename) return 'Arquivo desconhecido'
  if (filename.length <= maxLength) return filename
  
  const ext = filename.includes('.') ? '.' + filename.split('.').pop() : ''
  const nameWithoutExt = filename.slice(0, filename.length - ext.length)
  const truncatedName = nameWithoutExt.slice(0, maxLength - ext.length - 3) + '...'
  return truncatedName + ext
}

// Abrir modal de detalhes do projeto
const navigateToProject = (simulation) => {
  selectedProject.value = simulation
}

// Fechar modal
const closeModal = () => {
  selectedProject.value = null
}

// Navegar para a página de construção do grafo (Project)
const goToProject = () => {
  if (selectedProject.value?.project_id) {
    router.push({
      name: 'Process',
      params: { projectId: selectedProject.value.project_id }
    })
    closeModal()
  }
}

// Navegar para a página de configuração do ambiente (Simulation)
const goToSimulation = () => {
  if (selectedProject.value?.simulation_id) {
    router.push({
      name: 'Simulation',
      params: { simulationId: selectedProject.value.simulation_id }
    })
    closeModal()
  }
}

// Navegar para a página de relatório analitico (Report)
const goToReport = () => {
  if (selectedProject.value?.report_id) {
    router.push({
      name: 'Report',
      params: { reportId: selectedProject.value.report_id }
    })
    closeModal()
  }
}

// Carregar projetos históricos
const loadHistory = async () => {
  try {
    loading.value = true
    historyError.value = ''
    const response = await getSimulationHistory(20, { includeReports: true, includeRuntime: false })
    if (response.success) {
      projects.value = response.data || []
    }
  } catch (error) {
    console.error('Falha ao carregar o histórico de projetos:', error)
    projects.value = []
    historyError.value = 'Histórico indisponível no momento.'
  } finally {
    loading.value = false
  }
}

// Inicializar IntersectionObserver
const initObserver = () => {
  if (observer) {
    observer.disconnect()
  }
  
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const shouldExpand = entry.isIntersecting
        
        // Atualizar estado-alvo pendente (registrar o estado mais recente independente de animação)
        pendingState = shouldExpand
        
        // Limpar temporizador de debounce anterior (nova intenção de rolagem sobrescreve a antiga)
        if (expandDebounceTimer) {
          clearTimeout(expandDebounceTimer)
          expandDebounceTimer = null
        }
        
        // Se está animando, apenas registrar o estado e processar após o término
        if (isAnimating) return
        
        // Se o estado-alvo e igual ao estado atual, não precisa processar
        if (shouldExpand === isExpanded.value) {
          pendingState = null
          return
        }
        
        // Usar debounce para atrasar mudança de estado, evitando cintilação rápida
        // Atraso menor ao expandir (50ms), maior ao recolher (200ms) para estabilidade
        const delay = shouldExpand ? 50 : 200
        
        expandDebounceTimer = setTimeout(() => {
          // Verificar se está animando
          if (isAnimating) return
          
          // Verificar se o estado pendente ainda precisa ser executado (pode ter sido sobrescrito)
          if (pendingState === null || pendingState === isExpanded.value) return
          
          // Ativar trava de animação
          isAnimating = true
          isExpanded.value = pendingState
          pendingState = null
          
          // Desbloquear após animação e verificar se há mudanças de estado pendentes
          setTimeout(() => {
            isAnimating = false
            
            // Após o término da animação, verificar se há novos estados pendentes
            if (pendingState !== null && pendingState !== isExpanded.value) {
              // Aguardar um breve momento antes de executar, evitando troca muito rápida
              expandDebounceTimer = setTimeout(() => {
                if (pendingState !== null && pendingState !== isExpanded.value) {
                  isAnimating = true
                  isExpanded.value = pendingState
                  pendingState = null
                  setTimeout(() => {
                    isAnimating = false
                  }, 750)
                }
              }, 100)
            }
          }, 750)
        }, delay)
      })
    },
    {
      // Usar múltiplos limiares para detecção mais suave
      threshold: [0.4, 0.6, 0.8],
      // Ajustar rootMargin, encolher parte inferior da viewport, exigindo mais rolagem para expandir
      rootMargin: '0px 0px -150px 0px'
    }
  )
  
  // Iniciar observação
  if (historyContainer.value) {
    observer.observe(historyContainer.value)
  }
}

// Observar mudanças de rota e recarregar dados ao voltar para a página inicial
watch(() => route.path, (newPath) => {
  if (newPath === '/') {
    loadHistory()
  }
})

onMounted(async () => {
  // Garantir que o DOM esteja renderizado antes de carregar dados
  await nextTick()
  await loadHistory()
  
  // Inicializar observer após renderização do DOM
  setTimeout(() => {
    initObserver()
  }, 100)
})

// Se usar keep-alive, recarregar dados ao ativar o componente
onActivated(() => {
  loadHistory()
})

onUnmounted(() => {
  // Limpar Intersection Observer
  if (observer) {
    observer.disconnect()
    observer = null
  }
  // Limpar temporizador de debounce
  if (expandDebounceTimer) {
    clearTimeout(expandDebounceTimer)
    expandDebounceTimer = null
  }
})
</script>

<style scoped>
/* Container */
.history-database {
  position: relative;
  width: 100%;
  min-height: 280px;
  margin-top: 40px;
  padding: 35px 0 40px;
  overflow: visible;
}

/* Exibição simplificada quando não há projetos */
.history-database.no-projects {
  min-height: auto;
  padding: 40px 0 20px;
}

/* Fundo de grade técnica */
.tech-grid-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

/* Usar padrão de fundo CSS para criar grade quadrada com espaçamento fixo */
.grid-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(to right, rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  background-size: 50px 50px;
  /* Posicionar a partir do canto superior esquerdo, expandir apenas na parte inferior ao mudar a altura */
  background-position: top left;
}

.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    linear-gradient(to right, rgba(255, 255, 255, 0.9) 0%, transparent 15%, transparent 85%, rgba(255, 255, 255, 0.9) 100%),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.8) 0%, transparent 20%, transparent 80%, rgba(255, 255, 255, 0.8) 100%);
  pointer-events: none;
}

/* Área do título */
.section-header {
  position: relative;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 24px;
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  padding: 0 40px;
}

.section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(15, 39, 71, 0.14), transparent);
  max-width: 300px;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #0f2747;
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* Container de cartões */
.cards-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 0 40px;
  transition: min-height 700ms cubic-bezier(0.23, 1, 0.32, 1);
  /* min-height calculado dinâmicamente pelo JS, adaptavel a quantidade de cartões */
}

/* Cartao de projeto */
.project-card {
  position: absolute;
  width: 280px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 39, 71, 0.1);
  border-radius: 14px;
  padding: 14px;
  cursor: pointer;
  box-shadow: 0 18px 34px rgba(15, 39, 71, 0.08);
  transition: box-shadow 0.3s ease, border-color 0.3s ease, transform 700ms cubic-bezier(0.23, 1, 0.32, 1), opacity 700ms cubic-bezier(0.23, 1, 0.32, 1);
}

.project-card:hover {
  box-shadow: 0 24px 40px rgba(15, 39, 71, 0.14);
  border-color: rgba(212, 160, 23, 0.34);
  z-index: 1000 !important;
}

.project-card.hovering {
  z-index: 1000 !important;
}

/* Cabeçalho do cartão */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(15, 39, 71, 0.08);
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.7rem;
}

.card-id {
  color: #4b5563;
  letter-spacing: 0.5px;
  font-weight: 500;
}

/* Grupo de icones de status de funcionalidade */
.card-status-icons {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-icon {
  font-size: 0.75rem;
  transition: all 0.2s ease;
  cursor: default;
}

.status-icon.available {
  opacity: 1;
}

/* Cores para diferentes funcionalidades */
.status-icon:nth-child(1).available { color: #3B82F6; } /* Construção do grafo - azul */
.status-icon:nth-child(2).available { color: #F59E0B; } /* Configuração do ambiente - laranja */
.status-icon:nth-child(3).available { color: #10B981; } /* Relatório analitico - verde */

.status-icon.unavailable {
  color: #D1D5DB;
  opacity: 0.5;
}

/* Exibição de progresso das rodadas */
.card-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.5px;
  font-weight: 600;
  font-size: 0.65rem;
}

.status-dot {
  font-size: 0.5rem;
}

/* Cores de status de progresso */
.card-progress.completed { color: #5e7a34; }
.card-progress.in-progress { color: #b8860b; }
.card-progress.not-started { color: #8b95a7; }
.card-status.pending { color: #9CA3AF; }

/* Área da lista de arquivos */
.card-files-wrapper {
  position: relative;
  width: 100%;
  min-height: 48px;
  max-height: 110px;
  margin-bottom: 12px;
  padding: 8px 10px;
  background: linear-gradient(135deg, rgba(15, 39, 71, 0.04) 0%, rgba(212, 160, 23, 0.08) 100%);
  border-radius: 10px;
  border: 1px solid rgba(15, 39, 71, 0.08);
  overflow: hidden;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* Indicador de mais arquivos */
.files-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3px 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #4b5563;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 3px;
  letter-spacing: 0.3px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 3px;
  transition: all 0.2s ease;
}

.file-item:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateX(2px);
  border-color: #e5e7eb;
}

/* Estilo minimalista de rótulo de arquivo */
.file-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 16px;
  padding: 0 4px;
  border-radius: 2px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.55rem;
  font-weight: 600;
  line-height: 1;
  text-transform: uppercase;
  letter-spacing: 0.2px;
  flex-shrink: 0;
  min-width: 28px;
}

/* Esquema de cores de baixa saturação - paleta Morandi */
.file-tag.pdf { background: #f2e6e6; color: #a65a5a; }
.file-tag.doc { background: #e6eff5; color: #5a7ea6; }
.file-tag.xls { background: #e6f2e8; color: #5aa668; }
.file-tag.ppt { background: #f5efe6; color: #a6815a; }
.file-tag.txt { background: #f0f0f0; color: #757575; }
.file-tag.code { background: #eae6f2; color: #815aa6; }
.file-tag.img { background: #e6f2f2; color: #5aa6a6; }
.file-tag.zip { background: #f2f0e6; color: #a69b5a; }
.file-tag.other { background: #f3f4f6; color: #6b7280; }

.file-name {
  font-family: 'Inter', sans-serif;
  font-size: 0.7rem;
  color: #4b5563;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.1px;
}

/* Placeholder sem arquivos */
.files-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 48px;
  color: #8b95a7;
}

.empty-file-icon {
  font-size: 1rem;
  opacity: 0.5;
}

.empty-file-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.5px;
}

/* Efeito na área de arquivos ao passar o mouse */
.project-card:hover .card-files-wrapper {
  border-color: #d1d5db;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
}

/* Decoração de canto */
.corner-mark.top-left-only {
  position: absolute;
  top: 6px;
  left: 6px;
  width: 8px;
  height: 8px;
  border-top: 1.5px solid rgba(15, 39, 71, 0.28);
  border-left: 1.5px solid rgba(15, 39, 71, 0.28);
  pointer-events: none;
  z-index: 10;
}

/* Titulo do cartão */
.card-title {
  font-family: 'Inter', -apple-system, sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 6px 0;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s ease;
}

.project-card:hover .card-title {
  color: #2563EB;
}

/* Descrição do cartão */
.card-desc {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  color: #6B7280;
  margin: 0 0 16px 0;
  line-height: 1.5;
  height: 34px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* Rodapé do cartão */
.card-footer {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #F3F4F6;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #9CA3AF;
  font-weight: 500;
}

/* Combinação de data e hora */
.card-datetime {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Exibição de progresso de rodadas no rodapé */
.card-footer .card-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.5px;
  font-weight: 600;
  font-size: 0.65rem;
}

.card-footer .status-dot {
  font-size: 0.5rem;
}

/* Cores de status de progresso - rodapé */
.card-footer .card-progress.completed { color: #10B981; }
.card-footer .card-progress.in-progress { color: #F59E0B; }
.card-footer .card-progress.not-started { color: #9CA3AF; }

/* Linha decorativa inferior */
.card-bottom-line {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  width: 0;
  background-color: #000;
  transition: width 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 20;
}

.project-card:hover .card-bottom-line {
  width: 100%;
}

/* Estado vazio */
.empty-state, .loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 48px;
  color: #9CA3AF;
}

.history-error {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 12px;
  max-width: 520px;
  margin: 24px auto 0;
  padding: 16px 18px;
  border: 1px solid rgba(239, 68, 68, 0.28);
  border-radius: 8px;
  background: rgba(127, 29, 29, 0.12);
  color: #FCA5A5;
  font-size: 14px;
  line-height: 1.45;
  text-align: center;
}

.history-retry {
  border: 1px solid rgba(252, 165, 165, 0.45);
  border-radius: 6px;
  background: rgba(252, 165, 165, 0.08);
  color: #FECACA;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 12px;
  cursor: pointer;
}

.history-retry:hover {
  background: rgba(252, 165, 165, 0.16);
}

.empty-icon {
  font-size: 2rem;
  opacity: 0.5;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #E5E7EB;
  border-top-color: #6B7280;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsivo */
@media (max-width: 1200px) {
  .project-card {
    width: 240px;
  }
}

@media (max-width: 768px) {
  .cards-container {
    padding: 0 20px;
  }
  .project-card {
    width: 200px;
  }
}

/* ===== Estilo do modal de detalhes do histórico de replay ===== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: rgba(255, 255, 255, 0.94);
  width: 560px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  border: 1px solid rgba(15, 39, 71, 0.1);
  border-radius: 16px;
  box-shadow: 0 24px 44px rgba(15, 39, 71, 0.16);
}

/* Transição de animação */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-leave-active .modal-content {
  transition: all 0.2s ease-in;
}

.modal-enter-from .modal-content {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

.modal-leave-to .modal-content {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

/* Cabeçalho do modal */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  border-bottom: 1px solid rgba(15, 39, 71, 0.08);
  background: rgba(255, 255, 255, 0.92);
}

.modal-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.modal-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
  font-weight: 600;
  color: #0f2747;
  letter-spacing: 0.5px;
}

.modal-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(15, 39, 71, 0.06);
}

.modal-progress.completed { color: #5e7a34; background: rgba(94, 122, 52, 0.1); }
.modal-progress.in-progress { color: #b8860b; background: rgba(212, 160, 23, 0.12); }
.modal-progress.not-started { color: #8b95a7; background: rgba(15, 39, 71, 0.06); }

.modal-create-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #8b95a7;
  letter-spacing: 0.3px;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  color: #8b95a7;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  border-radius: 6px;
}

.modal-close:hover {
  background: rgba(212, 160, 23, 0.12);
  color: #0f2747;
}

/* Conteúdo do modal */
.modal-body {
  padding: 24px 32px;
}

.modal-section {
  margin-bottom: 24px;
}

.modal-section:last-child {
  margin-bottom: 0;
}

.modal-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
  font-weight: 500;
}

.modal-requirement {
  font-size: 0.95rem;
  color: #374151;
  line-height: 1.6;
  padding: 16px;
  background: rgba(15, 39, 71, 0.04);
  border: 1px solid rgba(15, 39, 71, 0.08);
  border-radius: 8px;
}

.modal-files {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 200px;
  overflow-y: auto;
  padding-right: 4px;
}

/* Estilo personalizado da barra de rolagem */
.modal-files::-webkit-scrollbar {
  width: 4px;
}

.modal-files::-webkit-scrollbar-track {
  background: rgba(15, 39, 71, 0.06);
  border-radius: 2px;
}

.modal-files::-webkit-scrollbar-thumb {
  background: rgba(15, 39, 71, 0.2);
  border-radius: 2px;
}

.modal-files::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 39, 71, 0.34);
}

.modal-file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(15, 39, 71, 0.1);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.modal-file-item:hover {
  border-color: rgba(212, 160, 23, 0.24);
  box-shadow: 0 10px 20px rgba(15, 39, 71, 0.08);
}

.modal-file-name {
  font-size: 0.85rem;
  color: #374151;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.modal-empty {
  font-size: 0.85rem;
  color: #8b95a7;
  padding: 16px;
  background: rgba(15, 39, 71, 0.04);
  border: 1px dashed rgba(15, 39, 71, 0.12);
  border-radius: 6px;
  text-align: center;
}

/* Divisor de replay da simulação */
.modal-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 32px 0;
  background: rgba(255, 255, 255, 0.92);
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(15, 39, 71, 0.14), transparent);
}

.divider-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #8b95a7;
  letter-spacing: 2px;
  text-transform: uppercase;
  white-space: nowrap;
}

/* Botões de navegação */
.modal-actions {
  display: flex;
  gap: 16px;
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.92);
}

.modal-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 1px solid rgba(15, 39, 71, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.modal-btn:hover:not(:disabled) {
  border-color: rgba(212, 160, 23, 0.34);
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(15, 39, 71, 0.12);
}

.modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(15, 39, 71, 0.04);
}

.btn-step {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  font-weight: 500;
  color: #8b95a7;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.btn-icon {
  font-size: 1.4rem;
  line-height: 1;
  transition: color 0.2s ease;
}

.btn-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #0f2747;
}

.modal-btn.btn-project .btn-icon { color: #3B82F6; }
.modal-btn.btn-simulation .btn-icon { color: #b8860b; }
.modal-btn.btn-report .btn-icon { color: #5e7a34; }

.modal-btn:hover:not(:disabled) .btn-text {
  color: #0f2747;
}

/* Aviso de replay indisponível */
.modal-playback-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 32px 20px;
  background: rgba(255, 255, 255, 0.92);
}

.hint-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #8b95a7;
  letter-spacing: 0.3px;
  text-align: center;
  line-height: 1.5;
}
</style>
