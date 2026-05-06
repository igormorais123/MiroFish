<template>
  <div class="process-page">
    <!-- Barra superior -->
    <nav class="navbar">
      <div class="nav-brand" @click="goHome">
        <span class="brand-mark">IA</span>
        <span class="brand-copy">
          <span class="brand-name">INTEIA</span>
          <span class="brand-sub">MiroFish Lab</span>
        </span>
      </div>
      
      <!-- Indicador central de etapa -->
      <div class="nav-center">
        <div class="step-badge">ETAPA 01</div>
        <div class="step-name">Construção do grafo</div>
      </div>

      <div class="nav-status">
        <span class="status-dot" :class="statusClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </nav>

    <!-- Área de conteúdo principal -->
    <div class="main-content">
      <!-- Esquerda: visualização do grafo em tempo real -->
      <div class="left-panel" :class="{ 'full-screen': isFullScreen }">
        <div class="panel-header">
          <div class="header-left">
            <span class="header-deco">◆</span>
            <span class="header-title">Grafo de conhecimento em tempo real</span>
          </div>
          <div class="header-right">
            <template v-if="graphData">
              <span class="stat-item">{{ graphData.node_count || graphData.nodes?.length || 0 }} nós</span>
              <span class="stat-divider">|</span>
              <span class="stat-item">{{ graphData.edge_count || graphData.edges?.length || 0 }} relações</span>
              <span class="stat-divider">|</span>
            </template>
            <div class="action-buttons">
                <button class="action-btn" @click="refreshGraph" :disabled="graphLoading" title="Atualizar grafo">
                  <span class="icon-refresh" :class="{ 'spinning': graphLoading }">↻</span>
                </button>
                <button class="action-btn" @click="toggleFullScreen" :title="isFullScreen ? 'Sair da tela cheia' : 'Tela cheia'">
                  <span class="icon-fullscreen">{{ isFullScreen ? '↙' : '↗' }}</span>
                </button>
            </div>
          </div>
        </div>
        
        <div class="graph-container" ref="graphContainer">
          <!-- Visualização do grafo -->
          <div v-if="graphData" class="graph-view">
            <svg ref="graphSvg" class="graph-svg"></svg>
            <!-- Indicação de construção -->
            <div v-if="currentPhase === 1" class="graph-building-hint">
              <span class="building-dot"></span>
              Atualizando em tempo real...
            </div>
            
            <!-- Painel de detalhes de nós/arestas -->
            <div v-if="selectedItem" class="detail-panel">
              <div class="detail-panel-header">
                <span class="detail-title">{{ selectedItem.type === 'node' ? 'Detalhes do nó' : 'Relacionamento' }}</span>
                <span v-if="selectedItem.type === 'node'" class="detail-badge" :style="{ background: selectedItem.color }">
                  {{ selectedItem.entityType }}
                </span>
                <button class="detail-close" @click="closeDetailPanel">×</button>
              </div>
              
              <!-- Detalhes do nó -->
              <div v-if="selectedItem.type === 'node'" class="detail-content">
                <div class="detail-row">
                  <span class="detail-label">Nome:</span>
                  <span class="detail-value highlight">{{ selectedItem.data.name }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">UUID:</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">Criado em:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>
                
                <!-- Propriedades / atributos -->
                <div class="detail-section" v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0">
                  <span class="detail-label">Propriedades:</span>
                  <div class="properties-list">
                    <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                      <span class="property-key">{{ key }}:</span>
                      <span class="property-value">{{ value }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- Resumo -->
                <div class="detail-section" v-if="selectedItem.data.summary">
                  <span class="detail-label">Resumo:</span>
                  <p class="detail-summary">{{ selectedItem.data.summary }}</p>
                </div>
                
                <!-- Rótulos -->
                <div class="detail-row" v-if="selectedItem.data.labels?.length">
                  <span class="detail-label">Rótulos:</span>
                  <div class="detail-labels">
                    <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">{{ label }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Detalhes da aresta -->
              <div v-else class="detail-content">
                <!-- Exibição da relação -->
                <div class="edge-relation">
                  <span class="edge-source">{{ selectedItem.data.source_name || selectedItem.data.source_node_name }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-type">{{ selectedItem.data.name || selectedItem.data.fact_type || 'RELATED_TO' }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-target">{{ selectedItem.data.target_name || selectedItem.data.target_node_name }}</span>
                </div>
                
                <div class="detail-subtitle">Relacionamento</div>
                
                <div class="detail-row">
                  <span class="detail-label">UUID:</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Rótulo:</span>
                  <span class="detail-value">{{ selectedItem.data.name || selectedItem.data.fact_type || 'RELATED_TO' }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.fact_type">
                  <span class="detail-label">Tipo:</span>
                  <span class="detail-value">{{ selectedItem.data.fact_type }}</span>
                </div>
                
                <!-- Fato -->
                <div class="detail-section" v-if="selectedItem.data.fact">
                  <span class="detail-label">Fato:</span>
                  <p class="detail-summary">{{ selectedItem.data.fact }}</p>
                </div>
                
                <!-- Episódios -->
                <div class="detail-section" v-if="selectedItem.data.episodes?.length">
                  <span class="detail-label">Episódios:</span>
                  <div class="episodes-list">
                    <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">{{ ep }}</span>
                  </div>
                </div>
                
                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">Criado em:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.valid_at">
                  <span class="detail-label">Válido a partir de:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.valid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.invalid_at">
                  <span class="detail-label">Inválido em:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.invalid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.expired_at">
                  <span class="detail-label">Expirado em:</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.expired_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Estado de carregamento -->
          <div v-else-if="graphLoading" class="graph-loading">
            <div class="loading-animation">
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
            </div>
            <p class="loading-text">Carregando dados do grafo...</p>
          </div>
          
          <!-- Aguardando construção -->
          <div v-else-if="currentPhase < 1" class="graph-waiting">
            <div class="waiting-icon">
              <svg viewBox="0 0 100 100" class="network-icon">
                <circle cx="50" cy="20" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <circle cx="20" cy="60" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <circle cx="80" cy="60" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <circle cx="50" cy="80" r="8" fill="none" stroke="#000" stroke-width="1.5"/>
                <line x1="50" y1="28" x2="25" y2="54" stroke="#000" stroke-width="1"/>
                <line x1="50" y1="28" x2="75" y2="54" stroke="#000" stroke-width="1"/>
                <line x1="28" y1="60" x2="72" y2="60" stroke="#000" stroke-width="1" stroke-dasharray="4"/>
                <line x1="50" y1="72" x2="26" y2="66" stroke="#000" stroke-width="1"/>
                <line x1="50" y1="72" x2="74" y2="66" stroke="#000" stroke-width="1"/>
              </svg>
            </div>
            <p class="waiting-text">Aguardando geração da ontologia</p>
            <p class="waiting-hint">A construção do grafo começará automaticamente quando a geração terminar</p>
          </div>
          
          <!-- Em construção, mas ainda sem dados -->
          <div v-else-if="currentPhase === 1 && !graphData" class="graph-waiting">
            <div class="loading-animation">
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
            </div>
            <p class="waiting-text">Construindo o grafo</p>
            <p class="waiting-hint">Os dados aparecerão em instantes...</p>
          </div>
          
          <!-- Estado de erro -->
          <div v-else-if="error" class="graph-error">
            <span class="error-icon">⚠</span>
            <p>{{ error }}</p>
          </div>
        </div>
        
        <!-- Legenda do grafo -->
        <div v-if="graphData" class="graph-legend">
          <div class="legend-item" v-for="type in entityTypes" :key="type.name">
            <span class="legend-dot" :style="{ background: type.color }"></span>
            <span class="legend-label">{{ type.name }}</span>
            <span class="legend-count">{{ type.count }}</span>
          </div>
        </div>
      </div>

      <!-- Direita: detalhes do fluxo de construção -->
      <div class="right-panel" :class="{ 'hidden': isFullScreen }">
        <div class="panel-header dark-header">
          <span class="header-icon">▣</span>
          <span class="header-title">Fluxo de construção</span>
        </div>

        <div class="process-content">
          <!-- Fase 1: geração da ontologia -->
          <div class="process-phase" :class="{ 'active': currentPhase === 0, 'completed': currentPhase > 0 }">
            <div class="phase-header">
              <span class="phase-num">01</span>
              <div class="phase-info">
                <div class="phase-title">Geração da ontologia</div>
                <div class="phase-api">/api/graph/ontology/generate</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(0)">
                {{ getPhaseStatusText(0) }}
              </span>
            </div>
            
            <div class="phase-detail">
              <div class="detail-section">
                  <div class="detail-label">Descrição da API</div>
                <div class="detail-content">
                  Após o envio dos documentos, o LLM analisa o conteúdo e gera automaticamente uma ontologia adequada para a simulação de opinião pública (tipos de entidade + tipos de relação)
                </div>
              </div>
              
              <!-- Progresso da geração da ontologia -->
              <div class="detail-section" v-if="ontologyProgress && currentPhase === 0">
                <div class="detail-label">Progresso da geração</div>
                <div class="ontology-progress">
                  <div class="progress-spinner"></div>
                  <span class="progress-text">{{ ontologyProgress.message }}</span>
                </div>
              </div>
              
              <!-- Informações da ontologia gerada -->
              <div class="detail-section" v-if="projectData?.ontology">
                <div class="detail-label">Tipos de entidade gerados ({{ projectData.ontology.entity_types?.length || 0 }})</div>
                <div class="entity-tags">
                  <span 
                    v-for="entity in projectData.ontology.entity_types" 
                    :key="entity.name"
                    class="entity-tag"
                  >
                    {{ entity.name }}
                  </span>
                </div>
              </div>
              
              <div class="detail-section" v-if="projectData?.ontology">
                <div class="detail-label">Tipos de relação gerados ({{ ontologyRelationTypes.length }})</div>
                <div class="relation-list">
                  <div 
                    v-for="(rel, idx) in ontologyRelationTypes.slice(0, 5)" 
                    :key="idx"
                    class="relation-item"
                  >
                    <span class="rel-source">{{ rel.source_type || rel.source }}</span>
                    <span class="rel-arrow">→</span>
                    <span class="rel-name">{{ rel.name }}</span>
                    <span class="rel-arrow">→</span>
                    <span class="rel-target">{{ rel.target_type || rel.target }}</span>
                  </div>
                  <div v-if="ontologyRelationTypes.length > 5" class="relation-more">
                    +{{ ontologyRelationTypes.length - 5 }} relações adicionais...
                  </div>
                </div>
              </div>
              
              <!-- Estado de espera -->
              <div class="detail-section waiting-state" v-if="!projectData?.ontology && currentPhase === 0 && !ontologyProgress">
                <div class="waiting-hint">Aguardando geração da ontologia...</div>
              </div>
            </div>
          </div>

          <!-- Fase 2: construção do grafo -->
          <div class="process-phase" :class="{ 'active': currentPhase === 1, 'completed': currentPhase > 1 }">
            <div class="phase-header">
              <span class="phase-num">02</span>
              <div class="phase-info">
                <div class="phase-title">Construção do grafo</div>
                <div class="phase-api">/api/graph/build</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(1)">
                {{ getPhaseStatusText(1) }}
              </span>
            </div>
            
            <div class="phase-detail">
              <div class="detail-section">
                  <div class="detail-label">Descrição da API</div>
                <div class="detail-content">
                  Com base na ontologia gerada, os documentos são divididos em blocos e enviados à API da Zep para construir o grafo de conhecimento e extrair entidades e relações
                </div>
              </div>
              
              <!-- Aguardando conclusão da ontologia -->
              <div class="detail-section waiting-state" v-if="currentPhase < 1">
                <div class="waiting-hint">Aguardando a conclusão da ontologia...</div>
              </div>
              
              <!-- Progresso da construção -->
              <div class="detail-section" v-if="buildProgress && currentPhase >= 1">
                <div class="detail-label">Progresso da construção</div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: buildProgress.progress + '%' }"></div>
                </div>
                <div class="progress-info">
                  <span class="progress-message">{{ buildProgress.message }}</span>
                  <span class="progress-percent">{{ buildProgress.progress }}%</span>
                </div>
              </div>
              
              <div class="detail-section" v-if="graphData">
                <div class="detail-label">Resultado da construção</div>
                <div class="build-result">
                  <div class="result-item">
                    <span class="result-value">{{ graphData.node_count }}</span>
                    <span class="result-label">Nós de entidade</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ graphData.edge_count }}</span>
                    <span class="result-label">Arestas de relação</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ entityTypes.length }}</span>
                    <span class="result-label">Tipos de entidade</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Fase 3: concluído -->
          <div class="process-phase" :class="{ 'active': currentPhase === 2, 'completed': currentPhase > 2 }">
            <div class="phase-header">
              <span class="phase-num">03</span>
              <div class="phase-info">
                <div class="phase-title">Construção concluída</div>
                <div class="phase-api">Pronto para a próxima etapa</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(2)">
                {{ getPhaseStatusText(2) }}
              </span>
            </div>
          </div>

          <!-- Botão da próxima etapa -->
          <div class="next-step-section" v-if="currentPhase >= 2">
            <button class="next-step-btn" @click="goToNextStep" :disabled="currentPhase < 2">
              Ir para configuração do ambiente
              <span class="btn-arrow">→</span>
            </button>
          </div>
        </div>

        <!-- Painel de informações do projeto -->
        <div class="project-panel">
          <div class="project-header">
            <span class="project-icon">◇</span>
            <span class="project-title">Informações do projeto</span>
          </div>
          <div class="project-details" v-if="projectData">
            <div class="project-item">
              <span class="item-label">Nome do projeto</span>
              <span class="item-value">{{ projectData.name }}</span>
            </div>
            <div class="project-item">
              <span class="item-label">ID do projeto</span>
              <span class="item-value code">{{ projectData.project_id }}</span>
            </div>
            <div class="project-item" v-if="projectData.graph_id">
              <span class="item-label">ID do grafo</span>
              <span class="item-value code">{{ projectData.graph_id }}</span>
            </div>
            <div class="project-item">
              <span class="item-label">Objetivo da simulação</span>
              <span class="item-value">{{ projectData.simulation_requirement || '-' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { generateOntology, getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload'
import * as d3 from 'd3'

const route = useRoute()
const router = useRouter()

// ID atual do projeto (pode mudar de 'new' para o ID real)
const currentProjectId = ref(route.params.projectId)

// Estado
const loading = ref(true)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const buildProgress = ref(null)
const ontologyProgress = ref(null) // progresso da geração da ontologia
const currentPhase = ref(-1) // -1: upload, 0: ontologia, 1: grafo, 2: concluído
const selectedItem = ref(null) // nó ou aresta selecionada
const isFullScreen = ref(false)

// Referências DOM
const graphContainer = ref(null)
const graphSvg = ref(null)

// Temporizador de polling
let pollTimer = null

// Propriedades computadas
const statusClass = computed(() => {
  if (error.value) return 'error'
  if (currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (error.value) return 'Falha na construção'
  if (currentPhase.value >= 2) return 'Construção concluída'
  if (currentPhase.value === 1) return 'Construindo o grafo'
  if (currentPhase.value === 0) return 'Gerando ontologia'
  return 'Inicializando'
})

const entityTypes = computed(() => {
  if (!graphData.value?.nodes) return []
  
  const typeMap = {}
  const colors = ['#d4a017', '#0f2747', '#2f5d8a', '#5e7a34', '#b55d2f', '#8a1c1c']
  
  graphData.value.nodes.forEach(node => {
    const type = node.labels?.find(l => l !== 'Entity') || 'Entity'
    if (!typeMap[type]) {
      typeMap[type] = { name: type, count: 0, color: colors[Object.keys(typeMap).length % colors.length] }
    }
    typeMap[type].count++
  })
  
  return Object.values(typeMap)
})

const ontologyRelationTypes = computed(() => {
  const ontology = projectData.value?.ontology
  if (!ontology) return []
  const relations = ontology.relation_types || ontology.edge_types || []
  return relations.map((rel) => {
    const firstPair = rel.source_targets?.[0] || {}
    return {
      ...rel,
      source_type: rel.source_type || firstPair.source || '',
      target_type: rel.target_type || firstPair.target || ''
    }
  })
})

// Metodos
const goHome = () => {
  router.push('/')
}

const goToNextStep = () => {
  // TODO: entrar na etapa de configuração do ambiente
  alert('A funcionalidade de configuração do ambiente ainda está em desenvolvimento.')
}

const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value
  // Wait for transition to finish then re-render graph
  setTimeout(() => {
    renderGraph()
  }, 350) 
}

// Fechar painel de detalhes
const closeDetailPanel = () => {
  selectedItem.value = null
}

// Formatar data
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('pt-BR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// Selecionar nó
const selectNode = (nodeData, color) => {
  selectedItem.value = {
    type: 'node',
    data: nodeData,
    color: color,
    entityType: nodeData.labels?.find(l => l !== 'Entity' && l !== 'Node') || 'Entidade'
  }
}

// Selecionar aresta
const selectEdge = (edgeData) => {
  selectedItem.value = {
    type: 'edge',
    data: edgeData
  }
}

const getPhaseStatusClass = (phase) => {
  if (currentPhase.value > phase) return 'completed'
  if (currentPhase.value === phase) return 'active'
  return 'pending'
}

const getPhaseStatusText = (phase) => {
  if (currentPhase.value > phase) return 'Concluído'
  if (currentPhase.value === phase) {
    if (phase === 1 && buildProgress.value) {
      return `${buildProgress.value.progress}%`
    }
    return 'Em andamento'
  }
  return 'Aguardando'
}

// Inicialização - tratar novo projeto ou carregar projeto existente
const initProject = async () => {
  const paramProjectId = route.params.projectId
  
  if (paramProjectId === 'new') {
    // Novo projeto: obter dados pendentes de upload da store
    await handleNewProject()
  } else {
    // Carregar projeto existente
    currentProjectId.value = paramProjectId
    await loadProject()
  }
}

// Tratar novo projeto - chamar API ontology/generate
const handleNewProject = async () => {
  const pending = getPendingUpload()
  const pendingFiles = pending.files || []
  const requirement = (pending.simulationRequirement || '').trim()
  
  if (!pending.isPending || (!requirement && pendingFiles.length === 0)) {
    currentPhase.value = -1
    ontologyProgress.value = null
    error.value = 'Nenhum objetivo de simulação encontrado. Volte para a página inicial, descreva o cenário e inicie novamente.'
    loading.value = false
    return
  }
  
  try {
    loading.value = true
    currentPhase.value = 0 // etapa de geração da ontologia
    ontologyProgress.value = {
      message: pendingFiles.length > 0
        ? 'Enviando arquivos e analisando documentos...'
        : 'Gerando ontologia a partir do objetivo informado...'
    }
    
    // Construir FormData
    const formDataObj = new FormData()
    pendingFiles.forEach(file => {
      formDataObj.append('files', file)
    })
    formDataObj.append('simulation_requirement', requirement)
    
    // Chamar API de geração de ontologia
    const response = await generateOntology(formDataObj)
    
    if (response.success) {
      // Limpar dados pendentes de upload
      clearPendingUpload()
      
      // Atualizar ID e dados do projeto
      currentProjectId.value = response.data.project_id
      projectData.value = response.data
      
      // Atualizar URL (sem recarregar página)
      router.replace({
        name: 'Process',
        params: { projectId: response.data.project_id }
      })
      
      ontologyProgress.value = null
      
      // Iniciar construção do grafo automaticamente
      await startBuildGraph()
    } else {
      error.value = response.error || 'Falha na geração da ontologia'
      ontologyProgress.value = null
      currentPhase.value = -1
    }
  } catch (err) {
    console.error('Handle new project error:', err)
    error.value = 'Falha ao inicializar o projeto: ' + (err.message || 'erro desconhecido')
    ontologyProgress.value = null
    currentPhase.value = -1
  } finally {
    loading.value = false
  }
}

// Carregar dados de projeto existente
const loadProject = async () => {
  try {
    loading.value = true
    const response = await getProject(currentProjectId.value)
    
    if (response.success) {
      projectData.value = response.data
      updatePhaseByStatus(response.data.status)
      
      // Iniciar construção do grafo automaticamente
      if (response.data.status === 'ontology_generated' && !response.data.graph_id) {
        await startBuildGraph()
      }
      
      // Continuar polling de tarefas em construção
      if (response.data.status === 'graph_building' && response.data.graph_build_task_id) {
        currentPhase.value = 1
        startPollingTask(response.data.graph_build_task_id)
      }
      
      // Carregar grafo concluído
      if (response.data.status === 'graph_completed' && response.data.graph_id) {
        currentPhase.value = 2
        await loadGraph(response.data.graph_id)
      }
    } else {
      error.value = response.error || 'Falha ao carregar o projeto'
    }
  } catch (err) {
    console.error('Load project error:', err)
    error.value = 'Falha ao carregar o projeto: ' + (err.message || 'erro desconhecido')
  } finally {
    loading.value = false
  }
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
    case 'ontology_generated':
      currentPhase.value = 0
      break
    case 'graph_building':
      currentPhase.value = 1
      break
    case 'graph_completed':
      currentPhase.value = 2
      break
    case 'failed':
      error.value = projectData.value?.error || 'Falha no processamento'
      break
  }
}

// Iniciar construção do grafo
const startBuildGraph = async () => {
  try {
    currentPhase.value = 1
    // Definir progresso inicial
    buildProgress.value = {
      progress: 0,
      message: 'Iniciando a construção do grafo...'
    }
    
    const response = await buildGraph({ project_id: currentProjectId.value })
    
    if (response.success) {
      buildProgress.value.message = 'A tarefa de construção do grafo foi iniciada...'
      
      // Salvar task_id para polling
      const taskId = response.data.task_id
      
      // Iniciar polling de dados do grafo (independente do polling de status da tarefa)
      startGraphPolling()
      
      // Iniciar polling de status da tarefa
      startPollingTask(taskId)
    } else {
      error.value = response.error || 'Falha ao iniciar a construção do grafo'
      buildProgress.value = null
    }
  } catch (err) {
    console.error('Build graph error:', err)
    error.value = 'Falha ao iniciar a construção do grafo: ' + (err.message || 'erro desconhecido')
    buildProgress.value = null
  }
}

// Temporizador de polling de dados do grafo
let graphPollTimer = null

// Iniciar polling de dados do grafo
const startGraphPolling = () => {
  // Obter uma vez imediatamente
  fetchGraphData()
  
  // Obter dados do grafo automaticamente a cada 10 segundos
  graphPollTimer = setInterval(async () => {
    await fetchGraphData()
  }, 10000)
}

// Atualizar grafo manualmente
const refreshGraph = async () => {
  graphLoading.value = true
  await fetchGraphData()
  graphLoading.value = false
}

// Parar polling de dados do grafo
const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
  }
}

// Obter dados do grafo
const fetchGraphData = async () => {
  try {
    // Obter informações do projeto primeiro para obter graph_id
    const projectResponse = await getProject(currentProjectId.value)
    
    if (projectResponse.success && projectResponse.data.graph_id) {
      const graphId = projectResponse.data.graph_id
      projectData.value = projectResponse.data
      
      // Obter dados do grafo
      const graphResponse = await getGraphData(graphId)
      
      if (graphResponse.success && graphResponse.data) {
        const newData = graphResponse.data
        const newNodeCount = newData.node_count || newData.nodes?.length || 0
        const oldNodeCount = graphData.value?.node_count || graphData.value?.nodes?.length || 0
        
        console.log('Fetching graph data, nodes:', newNodeCount, 'edges:', newData.edge_count || newData.edges?.length || 0)
        
        // Atualizar renderização quando os dados mudam
        if (newNodeCount !== oldNodeCount || !graphData.value) {
          graphData.value = newData
          await nextTick()
          renderGraph()
        }
      }
    }
  } catch (err) {
    console.log('Graph data fetch:', err.message || 'not ready')
  }
}

// Polling de status da tarefa
const startPollingTask = (taskId) => {
  // Executar uma consulta imediatamente
  pollTaskStatus(taskId)
  
  // Depois fazer polling periodico
  pollTimer = setInterval(() => {
    pollTaskStatus(taskId)
  }, 2000)
}

// Consultar status da tarefa
const pollTaskStatus = async (taskId) => {
  try {
    const response = await getTaskStatus(taskId)
    
    if (response.success) {
      const task = response.data
      
      // Atualizar exibição de progresso
      buildProgress.value = {
        progress: task.progress || 0,
        message: task.message || 'Processando...'
      }
      
      console.log('Task status:', task.status, 'Progress:', task.progress)
      
      if (task.status === 'completed') {
        console.log('Construção do grafo concluída, carregando dados completos...')
        
        stopPolling()
        stopGraphPolling()
        currentPhase.value = 2
        
        // Atualizar exibição de progresso para estado concluído
        buildProgress.value = {
          progress: 100,
          message: 'Construção concluída, carregando o grafo...'
        }
        
        // Recarregar dados do projeto para obter graph_id
        const projectResponse = await getProject(currentProjectId.value)
        if (projectResponse.success) {
          projectData.value = projectResponse.data
          
          // Carregar dados completos do grafo por fim
          if (projectResponse.data.graph_id) {
            console.log('Carregando grafo completo:', projectResponse.data.graph_id)
            await loadGraph(projectResponse.data.graph_id)
            console.log('Carregamento do grafo concluído')
          }
        }
        
        // Limpar exibição de progresso
        buildProgress.value = null
      } else if (task.status === 'failed') {
        stopPolling()
        stopGraphPolling()
        error.value = 'Falha na construção do grafo: ' + (task.error || 'erro desconhecido')
        buildProgress.value = null
      }
    }
  } catch (err) {
    console.error('Poll task error:', err)
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// Carregar dados do grafo
const loadGraph = async (graphId) => {
  try {
    graphLoading.value = true
    const response = await getGraphData(graphId)
    
    if (response.success) {
      graphData.value = response.data
      await nextTick()
      renderGraph()
    }
  } catch (err) {
    console.error('Load graph error:', err)
  } finally {
    graphLoading.value = false
  }
}

// Renderizar grafo (D3.js)
const renderGraph = () => {
  if (!graphSvg.value || !graphData.value) {
    console.log('Cannot render: svg or data missing')
    return
  }
  
  const container = graphContainer.value
  if (!container) {
    console.log('Cannot render: container missing')
    return
  }
  
  // Obter dimensoes do container
  const rect = container.getBoundingClientRect()
  const width = rect.width || 800
  const height = (rect.height || 600) - 60
  
  if (width <= 0 || height <= 0) {
    console.log('Cannot render: invalid dimensions', width, height)
    return
  }
  
  console.log('Rendering graph:', width, 'x', height)
  
  const svg = d3.select(graphSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
  
  svg.selectAll('*').remove()
  
  // Processar dados dos nós
  const nodesData = graphData.value.nodes || []
  const edgesData = graphData.value.edges || []
  
  if (nodesData.length === 0) {
    console.log('No nodes to render')
    // Exibir estado vazio
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', '#999')
      .text('Aguardando dados do grafo...')
    return
  }
  
  // Criar mapeamento de nós para busca de nomes
  const nodeMap = {}
  nodesData.forEach(n => {
    nodeMap[n.uuid] = n
  })
  
  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || 'Sem nome',
    type: n.labels?.find(l => l !== 'Entity' && l !== 'Node') || 'Entity',
    rawData: n // Salvar dados originais
  }))
  
  // Criar conjunto de IDs de nós para filtrar arestas válidas
  const nodeIds = new Set(nodes.map(n => n.id))
  
  const edges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || 'RELATED_TO',
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name || 'Desconhecido',
        target_name: nodeMap[e.target_node_uuid]?.name || 'Desconhecido'
      }
    }))
  
  console.log('Nodes:', nodes.length, 'Edges:', edges.length)
  
  // Mapeamento de cores
  const types = [...new Set(nodes.map(n => n.type))]
  const colorScale = d3.scaleOrdinal()
    .domain(types)
    .range(['#d4a017', '#0f2747', '#2f5d8a', '#5e7a34', '#b55d2f', '#8a1c1c', '#3c4858', '#8c6f3f'])
  
  // Layout de forca direcionada
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(100).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(40))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05))
  
  // Adicionar funcionalidade de zoom
  const g = svg.append('g')
  
  svg.call(d3.zoom()
    .extent([[0, 0], [width, height]])
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    }))
  
  // Desenhar arestas (incluindo linhas largas transparentes clicaveis)
  const linkGroup = g.append('g')
    .attr('class', 'links')
    .selectAll('g')
    .data(edges)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectEdge(d.rawData)
    })
  
  // Linha fina visivel
  const link = linkGroup.append('line')
    .attr('stroke', '#ccc')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.6)
  
  // Linha larga transparente para clique
  linkGroup.append('line')
    .attr('stroke', 'transparent')
    .attr('stroke-width', 10)
  
  // Rotulos das arestas
  const linkLabel = g.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(edges)
    .enter()
    .append('text')
    .attr('font-size', '9px')
    .attr('fill', '#999')
    .attr('text-anchor', 'middle')
    .text(d => d.type.length > 15 ? d.type.substring(0, 12) + '...' : d.type)
  
  // Desenhar nos
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d.rawData, colorScale(d.type))
    })
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
  
  node.append('circle')
    .attr('r', 10)
    .attr('fill', d => colorScale(d.type))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('class', 'node-circle')
  
  node.append('text')
    .attr('dx', 14)
    .attr('dy', 4)
    .text(d => d.name?.substring(0, 12) || '')
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('font-family', 'JetBrains Mono, monospace')
  
  // Clicar em área vazia para fechar painel de detalhes
  svg.on('click', () => {
    closeDetailPanel()
  })
  
  simulation.on('tick', () => {
    // Atualizar posição de todas as arestas (incluindo linhas visíveis e área de clique transparente)
    linkGroup.selectAll('line')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)
    
    // Atualizar posição dos rótulos das arestas
    linkLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 5)
    
    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })
  
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }
  
  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }
  
  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
}

// Observar mudanças nos dados do grafo
watch(graphData, () => {
  if (graphData.value) {
    nextTick(() => renderGraph())
  }
})

// Ciclo de vida
onMounted(() => {
  initProject()
})

onUnmounted(() => {
  stopPolling()
  stopGraphPolling()
})
</script>

<style scoped>
/* Variaveis */
:root {
  --inteia-navy: #0f2747;
  --inteia-navy-soft: #173b69;
  --inteia-amber: #d4a017;
  --inteia-paper: #f7f2e8;
  --inteia-paper-strong: #fffaf0;
  --inteia-ink: #1f2937;
  --inteia-line: rgba(15, 39, 71, 0.12);
  --inteia-muted: #6b7280;
}

.process-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(212, 160, 23, 0.12), transparent 28%),
    linear-gradient(180deg, var(--inteia-paper-strong) 0%, var(--inteia-paper) 100%);
  font-family: 'Space Grotesk', 'Noto Sans SC', sans-serif;
  overflow: hidden; /* Prevent body scroll in fullscreen */
}

/* Barra de navegação */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: linear-gradient(135deg, var(--inteia-navy) 0%, var(--inteia-navy-soft) 100%);
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 10;
  position: relative;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.brand-mark {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--inteia-amber) 0%, #f2c14a 100%);
  color: var(--inteia-navy);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: 0 8px 20px rgba(212, 160, 23, 0.25);
}

.brand-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.05;
}

.brand-name {
  font-size: 0.94rem;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.brand-sub {
  font-size: 0.58rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 12px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.step-badge {
  background: linear-gradient(135deg, var(--inteia-amber) 0%, #f2c14a 100%);
  color: var(--inteia-navy);
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  border-radius: 2px;
}

.step-name {
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  color: #fff;
}

.nav-status {
  display: flex;
  align-items: center;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  margin-right: 8px;
}

.status-dot.processing {
  background: var(--inteia-amber);
  animation: pulse 1.5s infinite;
}

.status-dot.completed {
  background: #1A936F;
}

.status-dot.error {
  background: #C5283D;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.55);
}

/* Área de conteúdo principal */
.main-content {
  display: flex;
  height: calc(100vh - 56px);
  position: relative;
}

/* Painel esquerdo - 50% padrão */
.left-panel {
  width: 50%;
  flex: none; /* Fixed width initially */
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--inteia-line);
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 250, 240, 0.72);
  z-index: 5;
}

.left-panel.full-screen {
  width: 100%;
  border-right: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--inteia-line);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  height: 50px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-deco {
  color: #FF6B35;
  font-size: 0.8rem;
}

.header-title {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.75rem;
  color: #666;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-val {
  font-weight: 600;
  color: #333;
}

.stat-divider {
  color: #eee;
}

.action-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
  border-radius: 2px;
}

.action-btn:hover:not(:disabled) {
  background: #F5F5F5;
  color: #000;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.icon-refresh, .icon-fullscreen {
  font-size: 1rem;
  line-height: 1;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Container do grafo */
.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.graph-loading,
.graph-waiting,
.graph-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.loading-animation {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
}

.loading-ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
  animation: ring-rotate 1.5s linear infinite;
}

.loading-ring:nth-child(1) {
  width: 80px;
  height: 80px;
  border-top-color: #000;
}

.loading-ring:nth-child(2) {
  width: 60px;
  height: 60px;
  top: 10px;
  left: 10px;
  border-right-color: #FF6B35;
  animation-delay: 0.2s;
}

.loading-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  top: 20px;
  left: 20px;
  border-bottom-color: #666;
  animation-delay: 0.4s;
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

.loading-text,
.waiting-text {
  font-size: 0.9rem;
  color: #333;
  margin: 0 0 8px;
}

.waiting-hint {
  font-size: 0.8rem;
  color: #999;
  margin: 0;
}

.waiting-icon {
  margin-bottom: 20px;
}

.network-icon {
  width: 100px;
  height: 100px;
  opacity: 0.6;
}

.graph-view {
  width: 100%;
  height: 100%;
  position: relative;
}

.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.graph-building-hint {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 107, 53, 0.1);
  border: 1px solid #FF6B35;
  font-size: 0.8rem;
  color: #FF6B35;
}

.building-dot {
  width: 8px;
  height: 8px;
  background: #FF6B35;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

/* Painel de detalhes de nos/arestas */
.detail-panel {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 320px;
  max-height: calc(100% - 32px);
  background: #fff;
  border: 1px solid #E0E0E0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.detail-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #FAFAFA;
  border-bottom: 1px solid #E0E0E0;
}

.detail-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
}

.detail-badge {
  padding: 2px 10px;
  font-size: 0.75rem;
  color: #fff;
  border-radius: 2px;
}

.detail-close {
  margin-left: auto;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #999;
  cursor: pointer;
  transition: color 0.2s;
}

.detail-close:hover {
  color: #333;
}

.detail-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.detail-label {
  font-size: 0.8rem;
  color: #999;
  min-width: 70px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 0.85rem;
  color: #333;
  word-break: break-word;
}

.detail-value.uuid {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-summary {
  margin: 8px 0 0 0;
  font-size: 0.85rem;
  color: #333;
  line-height: 1.6;
  padding: 10px;
  background: #F9F9F9;
  border-left: 3px solid #FF6B35;
}

.detail-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.label-tag {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: #F0F0F0;
  border: 1px solid #E0E0E0;
  color: #666;
}

/* Exibição de relações da aresta */
.edge-relation {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #F9F9F9;
  border: 1px solid #E0E0E0;
}

.edge-source,
.edge-target {
  font-size: 0.85rem;
  font-weight: 500;
  color: #333;
}

.edge-arrow {
  color: #999;
}

.edge-type {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: #FF6B35;
  color: #fff;
}

.detail-value.highlight {
  font-weight: 600;
  color: #000;
}

.detail-subtitle {
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
  margin: 16px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #E0E0E0;
}

/* Lista de propriedades */
.properties-list {
  margin-top: 8px;
  padding: 10px;
  background: #F9F9F9;
  border: 1px solid #E0E0E0;
}

.property-item {
  display: flex;
  margin-bottom: 6px;
  font-size: 0.85rem;
}

.property-item:last-child {
  margin-bottom: 0;
}

.property-key {
  color: #666;
  margin-right: 8px;
  font-family: 'JetBrains Mono', monospace;
}

.property-value {
  color: #333;
  word-break: break-word;
}

/* Lista de episodios */
.episodes-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-tag {
  display: block;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-family: 'JetBrains Mono', monospace;
  background: #F0F0F0;
  border: 1px solid #E0E0E0;
  color: #666;
  word-break: break-all;
}

.error-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 10px;
}

/* Legenda do grafo */
.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 24px;
  border-top: 1px solid #E0E0E0;
  background: #FAFAFA;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  color: #333;
}

.legend-count {
  color: #999;
}

/* Painel direito - 50% padrão */
.right-panel {
  width: 50%;
  flex: none;
  display: flex;
  flex-direction: column;
  background: #fff;
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease, transform 0.3s ease;
  overflow: hidden;
  opacity: 1;
}

.right-panel.hidden {
  width: 0;
  opacity: 0;
  transform: translateX(20px);
  pointer-events: none;
}

.right-panel .panel-header.dark-header {
  background: #000;
  color: #fff;
  border-bottom: none;
}

.right-panel .header-icon {
  color: #FF6B35;
  margin-right: 8px;
}

/* Conteúdo do fluxo */
.process-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Fases do fluxo */
.process-phase {
  margin-bottom: 24px;
  border: 1px solid #E0E0E0;
  opacity: 0.5;
  transition: all 0.3s;
}

.process-phase.active,
.process-phase.completed {
  opacity: 1;
}

.process-phase.active {
  border-color: #FF6B35;
}

.process-phase.completed {
  border-color: #1A936F;
}

.phase-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #FAFAFA;
  border-bottom: 1px solid #E0E0E0;
}

.process-phase.active .phase-header {
  background: #FFF5F2;
}

.process-phase.completed .phase-header {
  background: #F2FAF6;
}

.phase-num {
  font-size: 1.5rem;
  font-weight: 700;
  color: #ddd;
  line-height: 1;
}

.process-phase.active .phase-num {
  color: #FF6B35;
}

.process-phase.completed .phase-num {
  color: #1A936F;
}

.phase-info {
  flex: 1;
}

.phase-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.phase-api {
  font-size: 0.75rem;
  color: #999;
  font-family: 'JetBrains Mono', monospace;
}

.phase-status {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: #eee;
  color: #666;
}

.phase-status.active {
  background: #FF6B35;
  color: #fff;
}

.phase-status.completed {
  background: #1A936F;
  color: #fff;
}

/* Detalhes da fase */
.phase-detail {
  padding: 16px;
}

/* Tags de entidade */
.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: #F5F5F5;
  border: 1px solid #E0E0E0;
  color: #333;
}

/* Lista de relações */
.relation-list {
  font-size: 0.8rem;
}

.relation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed #eee;
}

.relation-item:last-child {
  border-bottom: none;
}

.rel-source,
.rel-target {
  color: #333;
}

.rel-arrow {
  color: #ccc;
}

.rel-name {
  color: #FF6B35;
  font-weight: 500;
}

.relation-more {
  padding-top: 8px;
  color: #999;
  font-size: 0.75rem;
}

/* Progresso da geração de ontologia */
.ontology-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #FFF5F2;
  border: 1px solid #FFE0D6;
}

.progress-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #FFE0D6;
  border-top-color: #FF6B35;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.progress-text {
  font-size: 0.85rem;
  color: #333;
}

/* Estado de espera */
.waiting-state {
  padding: 16px;
  background: #F9F9F9;
  border: 1px dashed #E0E0E0;
  text-align: center;
}

.waiting-hint {
  font-size: 0.85rem;
  color: #999;
}

/* Barra de progresso */
.progress-bar {
  height: 6px;
  background: #E0E0E0;
  margin-bottom: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #FF6B35;
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
}

.progress-message {
  color: #666;
}

.progress-percent {
  color: #FF6B35;
  font-weight: 600;
}

/* Resultado da construção */
.build-result {
  display: flex;
  gap: 16px;
}

.result-item {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: #F5F5F5;
}

.result-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #000;
  margin-bottom: 4px;
}

.result-label {
  font-size: 0.7rem;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Botao de proxima etapa */
.next-step-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #E0E0E0;
}

.next-step-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: #000;
  color: #fff;
  border: none;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
}

.next-step-btn:hover:not(:disabled) {
  background: #FF6B35;
}

.next-step-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 1.2rem;
}

/* Painel de informações do projeto */
.project-panel {
  border-top: 1px solid #E0E0E0;
  background: #FAFAFA;
}

.project-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-bottom: 1px solid #E0E0E0;
}

.project-icon {
  color: #FF6B35;
}

.project-title {
  font-size: 0.85rem;
  font-weight: 600;
}

.project-details {
  padding: 16px 24px;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px dashed #E0E0E0;
  font-size: 0.8rem;
}

.project-item:last-child {
  border-bottom: none;
}

.item-label {
  color: #999;
  flex-shrink: 0;
}

.item-value {
  color: #333;
  text-align: right;
  max-width: 60%;
  word-break: break-all;
}

.item-value.code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
}

/* Responsivo */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100% !important;
    border-right: none;
    border-bottom: 1px solid #E0E0E0;
    height: 50vh;
  }
  
  .right-panel {
    width: 100% !important;
    height: 50vh;
    opacity: 1 !important;
    transform: none !important;
  }
  
  .right-panel.hidden {
      display: none;
  }
}
</style>
