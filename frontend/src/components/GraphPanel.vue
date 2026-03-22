<template>
  <div class="graph-panel">
    <div class="panel-header">
      <span class="panel-title">Visualização do grafo</span>
      <!-- Barra de ferramentas superior (canto superior direito interno) -->
      <div class="header-tools">
        <button class="tool-btn" @click="$emit('refresh')" :disabled="loading" title="Atualizar grafo">
          <span class="icon-refresh" :class="{ 'spinning': loading }">↻</span>
          <span class="btn-text">Atualizar</span>
        </button>
        <button class="tool-btn" @click="$emit('toggle-maximize')" title="Maximizar/restaurar">
          <span class="icon-maximize">⛶</span>
        </button>
      </div>
    </div>
    
    <div class="graph-container" ref="graphContainer">
      <!-- Visualização do grafo -->
      <div v-if="graphData" class="graph-view">
        <svg ref="graphSvg" class="graph-svg"></svg>
        
        <!-- Aviso de construção/simulação em andamento -->
        <div v-if="currentPhase === 1 || isSimulating" class="graph-building-hint">
          <div class="memory-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="memory-icon">
              <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-4.04z" />
              <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-4.04z" />
            </svg>
          </div>
          {{ isSimulating ? 'Memória de curto e longo prazo do GraphRAG sendo atualizada em tempo real' : 'Atualizando em tempo real...' }}
        </div>
        
        <!-- Aviso após o término da simulação -->
        <div v-if="showSimulationFinishedHint" class="graph-building-hint finished-hint">
          <div class="hint-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="hint-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
          <span class="hint-text">Ainda há conteúdo em processamento. Atualize o grafo manualmente em instantes.</span>
          <button class="hint-close-btn" @click="dismissFinishedHint" title="Fechar aviso">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <!-- Painel de detalhes de nos/arestas -->
        <div v-if="selectedItem" class="detail-panel">
          <div class="detail-panel-header">
            <span class="detail-title">{{ selectedItem.type === 'node' ? 'Detalhes do nó' : 'Relacionamento' }}</span>
            <span v-if="selectedItem.type === 'node'" class="detail-type-badge" :style="{ background: selectedItem.color, color: '#fff' }">
              {{ traduzirLabel(selectedItem.entityType) }}
            </span>
            <button class="detail-close" @click="closeDetailPanel">×</button>
          </div>
          
          <!-- Detalhes do no -->
          <div v-if="selectedItem.type === 'node'" class="detail-content">
            <div class="detail-row">
              <span class="detail-label">Nome:</span>
              <span class="detail-value">{{ selectedItem.data.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">UUID:</span>
              <span class="detail-value uuid-text">{{ selectedItem.data.uuid }}</span>
            </div>
            <div class="detail-row" v-if="selectedItem.data.created_at">
              <span class="detail-label">Criado em:</span>
              <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
            </div>
            
            <!-- Properties -->
            <div class="detail-section" v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0">
              <div class="section-title">Propriedades:</div>
              <div class="properties-list">
                <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                  <span class="property-key">{{ key }}:</span>
                  <span class="property-value">{{ value || 'Nenhum' }}</span>
                </div>
              </div>
            </div>
            
            <!-- Summary -->
            <div class="detail-section" v-if="selectedItem.data.summary">
              <div class="section-title">Resumo:</div>
              <div class="summary-text">{{ selectedItem.data.summary }}</div>
            </div>
            
            <!-- Labels -->
            <div class="detail-section" v-if="selectedItem.data.labels && selectedItem.data.labels.length > 0">
              <div class="section-title">Rótulos:</div>
              <div class="labels-list">
                <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">
                  {{ traduzirLabel(label) }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- Detalhes da aresta -->
          <div v-else class="detail-content">
            <!-- Detalhes do grupo de auto-relações -->
            <template v-if="selectedItem.data.isSelfLoopGroup">
              <div class="edge-relation-header self-loop-header">
                {{ selectedItem.data.source_name }} - Autorrelações
                <span class="self-loop-count">{{ selectedItem.data.selfLoopCount }} itens</span>
              </div>
              
              <div class="self-loop-list">
                <div 
                  v-for="(loop, idx) in selectedItem.data.selfLoopEdges" 
                  :key="loop.uuid || idx" 
                  class="self-loop-item"
                  :class="{ expanded: expandedSelfLoops.has(loop.uuid || idx) }"
                >
                  <div 
                    class="self-loop-item-header"
                    @click="toggleSelfLoop(loop.uuid || idx)"
                  >
                    <span class="self-loop-index">#{{ idx + 1 }}</span>
                    <span class="self-loop-name">{{ traduzirNome(loop.name || loop.fact_type || 'RELACIONADO') }}</span>
                    <span class="self-loop-toggle">{{ expandedSelfLoops.has(loop.uuid || idx) ? '−' : '+' }}</span>
                  </div>
                  
                  <div class="self-loop-item-content" v-show="expandedSelfLoops.has(loop.uuid || idx)">
                    <div class="detail-row" v-if="loop.uuid">
                      <span class="detail-label">UUID:</span>
                      <span class="detail-value uuid-text">{{ loop.uuid }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact">
                      <span class="detail-label">Fato:</span>
                      <span class="detail-value fact-text">{{ loop.fact }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact_type">
                      <span class="detail-label">Tipo:</span>
                      <span class="detail-value">{{ loop.fact_type }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.created_at">
                      <span class="detail-label">Criado em:</span>
                      <span class="detail-value">{{ formatDateTime(loop.created_at) }}</span>
                    </div>
                    <div v-if="loop.episodes && loop.episodes.length > 0" class="self-loop-episodes">
                      <span class="detail-label">Episódios:</span>
                      <div class="episodes-list compact">
                        <span v-for="ep in loop.episodes" :key="ep" class="episode-tag small">{{ ep }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
            
            <!-- Detalhes da aresta normal -->
            <template v-else>
              <div class="edge-relation-header">
                {{ selectedItem.data.source_name }} → {{ traduzirNome(selectedItem.data.name || 'RELACIONADO_A') }} → {{ selectedItem.data.target_name }}
              </div>
              
              <div class="detail-row">
                <span class="detail-label">UUID:</span>
                <span class="detail-value uuid-text">{{ selectedItem.data.uuid }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Rótulo:</span>
                <span class="detail-value">{{ traduzirNome(selectedItem.data.name || 'RELACIONADO_A') }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Tipo:</span>
                <span class="detail-value">{{ traduzirNome(selectedItem.data.fact_type || 'Desconhecido') }}</span>
              </div>
              <div class="detail-row" v-if="selectedItem.data.fact">
                <span class="detail-label">Fato:</span>
                <span class="detail-value fact-text">{{ selectedItem.data.fact }}</span>
              </div>
              
              <!-- Episodes -->
              <div class="detail-section" v-if="selectedItem.data.episodes && selectedItem.data.episodes.length > 0">
                <div class="section-title">Episódios:</div>
                <div class="episodes-list">
                  <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">
                    {{ ep }}
                  </span>
                </div>
              </div>
              
              <div class="detail-row" v-if="selectedItem.data.created_at">
                <span class="detail-label">Criado em:</span>
                <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
              </div>
              <div class="detail-row" v-if="selectedItem.data.valid_at">
                <span class="detail-label">Válido a partir de:</span>
                <span class="detail-value">{{ formatDateTime(selectedItem.data.valid_at) }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>
      
      <!-- Estado de carregamento -->
      <div v-else-if="loading" class="graph-state">
        <div class="loading-spinner"></div>
        <p>Carregando dados do grafo...</p>
      </div>
      
      <!-- Estado de espera/vazio -->
      <div v-else class="graph-state">
        <div class="empty-icon">❖</div>
        <p class="empty-text">Aguardando a geração da ontologia...</p>
      </div>
    </div>

    <!-- Legenda inferior (canto inferior esquerdo) -->
    <div v-if="graphData && entityTypes.length" class="graph-legend">
      <span class="legend-title">Tipos de entidade</span>
      <div class="legend-items">
        <div class="legend-item" v-for="type in entityTypes" :key="type.name">
          <span class="legend-dot" :style="{ background: type.color }"></span>
          <span class="legend-label">{{ traduzirLabel(type.name) }}</span>
        </div>
      </div>
    </div>
    
    <!-- Interruptor de exibição de rótulos das arestas -->
    <div v-if="graphData" class="edge-labels-toggle">
      <label class="toggle-switch">
        <input type="checkbox" v-model="showEdgeLabels" />
        <span class="slider"></span>
      </label>
      <span class="toggle-label">Mostrar rótulos das arestas</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  graphData: Object,
  loading: Boolean,
  currentPhase: Number,
  isSimulating: Boolean
})

const emit = defineEmits(['refresh', 'toggle-maximize'])

const graphContainer = ref(null)
const graphSvg = ref(null)
const selectedItem = ref(null)
const showEdgeLabels = ref(true) // Exibir rótulos das arestas por padrão
const expandedSelfLoops = ref(new Set()) // Itens de auto-relação expandidos
const showSimulationFinishedHint = ref(false) // Aviso após o término da simulação
const wasSimulating = ref(false) // Rastrear se estava em simulação anteriormente

// Fechar aviso de término da simulação
const dismissFinishedHint = () => {
  showSimulationFinishedHint.value = false
}

// Observar mudanças em isSimulating para detectar término da simulação
watch(() => props.isSimulating, (newValue, oldValue) => {
  if (wasSimulating.value && !newValue) {
    // Transição de simulação para nao-simulação, exibir aviso de término
    showSimulationFinishedHint.value = true
  }
  wasSimulating.value = newValue
}, { immediate: true })

// Alternar estado expandido/recolhido de itens de auto-relação
const toggleSelfLoop = (id) => {
  const newSet = new Set(expandedSelfLoops.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  expandedSelfLoops.value = newSet
}

// Calcular tipos de entidade para a legenda
const entityTypes = computed(() => {
  if (!props.graphData?.nodes) return []
  const typeMap = {}
  // Paleta de cores estetica
  const colors = ['#d4a017', '#0f2747', '#2f5d8a', '#5e7a34', '#b55d2f', '#8a1c1c', '#4f7cac', '#8c6f3f', '#3f7d58', '#d97706']
  
  props.graphData.nodes.forEach(node => {
    const type = node.labels?.find(l => l !== 'Entity') || 'Entity'
    if (!typeMap[type]) {
      typeMap[type] = { name: type, count: 0, color: colors[Object.keys(typeMap).length % colors.length] }
    }
    typeMap[type].count++
  })
  return Object.values(typeMap)
})

// Traduzir labels de tipo de entidade
const traduzirLabel = (label) => {
  const mapa = {
    'Entity': 'Entidade',
    'Relation': 'Relação',
    'Episode': 'Episódio',
    'Fact': 'Fato',
    'Node': 'Nó',
  }
  return mapa[label] || label
}

// Traduzir nomes UPPER_SNAKE_CASE de relações
const traduzirNome = (nome) => {
  const mapa = {
    'SUPPORTS': 'APOIA',
    'OPPOSES': 'SE_OPOE_A',
    'COMPETES': 'COMPETE',
    'COMPETES_WITH': 'COMPETE_COM',
    'COLLABORATES_WITH': 'COLABORA_COM',
    'WORKS_FOR': 'TRABALHA_PARA',
    'STUDIES_AT': 'ESTUDA_EM',
    'AFFILIATED_WITH': 'AFILIADO_A',
    'REPRESENTS': 'REPRESENTA',
    'REGULATES': 'REGULAMENTA',
    'REPORTS_ON': 'REPORTA_SOBRE',
    'COMMENTS_ON': 'COMENTA_SOBRE',
    'RESPONDS_TO': 'RESPONDE_A',
    'HAS_MARGINAL_BENEFIT': 'TEM_BENEFICIO_MARGINAL',
    'HAS_APPROVAL_RATE': 'TEM_TAXA_APROVACAO',
    'DECIDES': 'DECIDE',
    'PROPOSED': 'PROPOE',
  }
  return mapa[nome] || nome
}

// Formatar hora
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('pt-BR', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: false
    })
  } catch {
    return dateStr
  }
}

const closeDetailPanel = () => {
  selectedItem.value = null
  expandedSelfLoops.value = new Set() // Redefinir estado de expansao
}

let currentSimulation = null
let linkLabelsRef = null
let linkLabelBgRef = null

const renderGraph = () => {
  if (!graphSvg.value || !props.graphData) return
  
  // Parar simulação anterior
  if (currentSimulation) {
    currentSimulation.stop()
  }
  
  const container = graphContainer.value
  const width = container.clientWidth
  const height = container.clientHeight
  
  const svg = d3.select(graphSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    
  svg.selectAll('*').remove()
  
  const nodesData = props.graphData.nodes || []
  const edgesData = props.graphData.edges || []
  
  if (nodesData.length === 0) return

  // Prep data
  const nodeMap = {}
  nodesData.forEach(n => nodeMap[n.uuid] = n)
  
  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || 'Unnamed',
    type: n.labels?.find(l => l !== 'Entity') || 'Entity',
    rawData: n
  }))
  
  const nodeIds = new Set(nodes.map(n => n.id))
  
  // Processar dados de arestas, calcular quantidade e indices de arestas entre pares de nos
  const edgePairCount = {}
  const selfLoopEdges = {} // Arestas de auto-relação agrupadas por nó
  const tempEdges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
  
  // Contar arestas entre cada par de nós e coletar auto-relações
  tempEdges.forEach(e => {
    if (e.source_node_uuid === e.target_node_uuid) {
      // Auto-relação - coletar no array
      if (!selfLoopEdges[e.source_node_uuid]) {
        selfLoopEdges[e.source_node_uuid] = []
      }
      selfLoopEdges[e.source_node_uuid].push({
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name,
        target_name: nodeMap[e.target_node_uuid]?.name
      })
    } else {
      const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
      edgePairCount[pairKey] = (edgePairCount[pairKey] || 0) + 1
    }
  })
  
  // Registrar a aresta atual sendo processada para cada par de nos
  const edgePairIndex = {}
  const processedSelfLoopNodes = new Set() // Nós de auto-relação já processados
  
  const edges = []
  
  tempEdges.forEach(e => {
    const isSelfLoop = e.source_node_uuid === e.target_node_uuid
    
    if (isSelfLoop) {
      // Aresta de auto-relação - adicionar apenas uma auto-relação consolidada por nó
      if (processedSelfLoopNodes.has(e.source_node_uuid)) {
        return // Ja processado, pular
      }
      processedSelfLoopNodes.add(e.source_node_uuid)
      
      const allSelfLoops = selfLoopEdges[e.source_node_uuid]
      const nodeName = nodeMap[e.source_node_uuid]?.name || 'Desconhecido'
      
      edges.push({
        source: e.source_node_uuid,
        target: e.target_node_uuid,
        type: 'SELF_LOOP',
        name: `Self Relations (${allSelfLoops.length})`,
        curvature: 0,
        isSelfLoop: true,
        rawData: {
          isSelfLoopGroup: true,
          source_name: nodeName,
          target_name: nodeName,
          selfLoopCount: allSelfLoops.length,
          selfLoopEdges: allSelfLoops // Armazenar informações detalhadas de todas as arestas de auto-relação
        }
      })
      return
    }
    
    const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
    const totalCount = edgePairCount[pairKey]
    const currentIndex = edgePairIndex[pairKey] || 0
    edgePairIndex[pairKey] = currentIndex + 1
    
    // Verificar se a direção da aresta e consistente com a direção padronizada (UUID origem < UUID destino)
    const isReversed = e.source_node_uuid > e.target_node_uuid
    
    // Calcular curvatura: dispersar quando há multiplas arestas, linha reta para aresta unica
    let curvature = 0
    if (totalCount > 1) {
      // Distribuir curvatura uniformemente, garantindo distincao clara
      // O intervalo de curvatura aumenta com a quantidade de arestas
      const curvatureRange = Math.min(1.2, 0.6 + totalCount * 0.15)
      curvature = ((currentIndex / (totalCount - 1)) - 0.5) * curvatureRange * 2
      
      // Se a direção da aresta e oposta a direção padronizada, inverter curvatura
      // Isso garante distribuição uniforme no mesmo referêncial, sem sobreposição por direção
      if (isReversed) {
        curvature = -curvature
      }
    }
    
    edges.push({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || 'RELATED',
      name: e.name || e.fact_type || 'RELATED',
      curvature,
      isSelfLoop: false,
      pairIndex: currentIndex,
      pairTotal: totalCount,
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name,
        target_name: nodeMap[e.target_node_uuid]?.name
      }
    })
  })
    
  // Color scale
  const colorMap = {}
  entityTypes.value.forEach(t => colorMap[t.name] = t.color)
  const getColor = (type) => colorMap[type] || '#999'

  // Simulation - Ajustar espaçamento entre nós dinâmicamente com base na quantidade de arestas
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(d => {
      // Ajustar distancia dinâmicamente com base na quantidade de arestas entre este par de nos
      // Distancia base 150, acrescimo de 40 por aresta adicional
      const baseDistance = 150
      const edgeCount = d.pairTotal || 1
      return baseDistance + (edgeCount - 1) * 50
    }))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide(50))
    // Adicionar gravidade em direção ao centro para agrupar nós isolados na área central
    .force('x', d3.forceX(width / 2).strength(0.04))
    .force('y', d3.forceY(height / 2).strength(0.04))
  
  currentSimulation = simulation

  const g = svg.append('g')
  
  // Zoom
  svg.call(d3.zoom().extent([[0, 0], [width, height]]).scaleExtent([0.1, 4]).on('zoom', (event) => {
    g.attr('transform', event.transform)
  }))

  // Links - usar path para suportar curvas
  const linkGroup = g.append('g').attr('class', 'links')
  
  // Calcular caminho da curva
  const getLinkPath = (d) => {
    const sx = d.source.x, sy = d.source.y
    const tx = d.target.x, ty = d.target.y
    
    // Detectar auto-relação
    if (d.isSelfLoop) {
      // Auto-relação: desenhar arco do nó de volta para si mesmo
      const loopRadius = 30
      // Partir do lado direito do nó e voltar em círculo
      const x1 = sx + 8  // Deslocamento do ponto inicial
      const y1 = sy - 4
      const x2 = sx + 8  // Deslocamento do ponto final
      const y2 = sy + 4
      // Usar arco circular para desenhar auto-relação (sweep-flag=1 sentido horario)
      return `M${x1},${y1} A${loopRadius},${loopRadius} 0 1,1 ${x2},${y2}`
    }
    
    if (d.curvature === 0) {
      // Linha reta
      return `M${sx},${sy} L${tx},${ty}`
    }
    
    // Calcular ponto de controle da curva - ajustar dinâmicamente com base na quantidade e distancia
    const dx = tx - sx, dy = ty - sy
    const dist = Math.sqrt(dx * dx + dy * dy)
    // Deslocamento perpendicular a direção da conexao, calculado proporcionalmente para visibilidade
    // Quanto mais arestas, maior a proporção de deslocamento em relação a distancia
    const pairTotal = d.pairTotal || 1
    const offsetRatio = 0.25 + pairTotal * 0.05 // Base 25%, acrescimo de 5% por aresta adicional
    const baseOffset = Math.max(35, dist * offsetRatio)
    const offsetX = -dy / dist * d.curvature * baseOffset
    const offsetY = dx / dist * d.curvature * baseOffset
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    
    return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`
  }
  
  // Calcular ponto medio da curva (para posicionamento de rótulos)
  const getLinkMidpoint = (d) => {
    const sx = d.source.x, sy = d.source.y
    const tx = d.target.x, ty = d.target.y
    
    // Detectar auto-relação
    if (d.isSelfLoop) {
      // Posição do rótulo de auto-relação: lado direito do nó
      return { x: sx + 70, y: sy }
    }
    
    if (d.curvature === 0) {
      return { x: (sx + tx) / 2, y: (sy + ty) / 2 }
    }
    
    // Ponto medio da curva de Bezier quadratica t=0.5
    const dx = tx - sx, dy = ty - sy
    const dist = Math.sqrt(dx * dx + dy * dy)
    const pairTotal = d.pairTotal || 1
    const offsetRatio = 0.25 + pairTotal * 0.05
    const baseOffset = Math.max(35, dist * offsetRatio)
    const offsetX = -dy / dist * d.curvature * baseOffset
    const offsetY = dx / dist * d.curvature * baseOffset
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    
    // Formula da curva de Bezier quadratica B(t) = (1-t)^2*P0 + 2(1-t)tP1 + t^2*P2, t=0.5
    const midX = 0.25 * sx + 0.5 * cx + 0.25 * tx
    const midY = 0.25 * sy + 0.5 * cy + 0.25 * ty
    
    return { x: midX, y: midY }
  }
  
  const link = linkGroup.selectAll('path')
    .data(edges)
    .enter().append('path')
    .attr('stroke', '#C0C0C0')
    .attr('stroke-width', 1.5)
    .attr('fill', 'none')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      // Redefinir estilo da aresta selecionada anteriormente
      linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
      linkLabelBg.attr('fill', 'rgba(255,255,255,0.95)')
      linkLabels.attr('fill', '#666')
      // Destacar a aresta selecionada atualmente
      d3.select(event.target).attr('stroke', '#3498db').attr('stroke-width', 3)
      
      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })

  // Link labels background (Fundo branco torna o texto mais legivel)
  const linkLabelBg = linkGroup.selectAll('rect')
    .data(edges)
    .enter().append('rect')
    .attr('fill', 'rgba(255,255,255,0.95)')
    .attr('rx', 3)
    .attr('ry', 3)
    .style('cursor', 'pointer')
    .style('pointer-events', 'all')
    .style('display', showEdgeLabels.value ? 'block' : 'none')
    .on('click', (event, d) => {
      event.stopPropagation()
      linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
      linkLabelBg.attr('fill', 'rgba(255,255,255,0.95)')
      linkLabels.attr('fill', '#666')
      // Destacar a aresta correspondente
      link.filter(l => l === d).attr('stroke', '#3498db').attr('stroke-width', 3)
      d3.select(event.target).attr('fill', 'rgba(52, 152, 219, 0.1)')
      
      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })

  // Link labels
  const linkLabels = linkGroup.selectAll('text')
    .data(edges)
    .enter().append('text')
    .text(d => traduzirNome(d.name))
    .attr('font-size', '9px')
    .attr('fill', '#666')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .style('cursor', 'pointer')
    .style('pointer-events', 'all')
    .style('font-family', 'system-ui, sans-serif')
    .style('display', showEdgeLabels.value ? 'block' : 'none')
    .on('click', (event, d) => {
      event.stopPropagation()
      linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
      linkLabelBg.attr('fill', 'rgba(255,255,255,0.95)')
      linkLabels.attr('fill', '#666')
      // Destacar a aresta correspondente
      link.filter(l => l === d).attr('stroke', '#3498db').attr('stroke-width', 3)
      d3.select(event.target).attr('fill', '#3498db')
      
      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })
  
  // Salvar referência para controle externo de visibilidade
  linkLabelsRef = linkLabels
  linkLabelBgRef = linkLabelBg

  // Nodes group
  const nodeGroup = g.append('g').attr('class', 'nodes')
  
  // Node circles
  const node = nodeGroup.selectAll('circle')
    .data(nodes)
    .enter().append('circle')
    .attr('r', 10)
    .attr('fill', d => getColor(d.type))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2.5)
    .style('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        // Apenas registrar posição, não reiniciar simulação (distinguir clique de arrasto)
        d.fx = d.x
        d.fy = d.y
        d._dragStartX = event.x
        d._dragStartY = event.y
        d._isDragging = false
      })
      .on('drag', (event, d) => {
        // Detectar se realmente comecou a arrastar (movimento acima do limiar)
        const dx = event.x - d._dragStartX
        const dy = event.y - d._dragStartY
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (!d._isDragging && distance > 3) {
          // Reiniciar simulação apenas no primeiro arrasto detectado
          d._isDragging = true
          simulation.alphaTarget(0.3).restart()
        }
        
        if (d._isDragging) {
          d.fx = event.x
          d.fy = event.y
        }
      })
      .on('end', (event, d) => {
        // Permitir parada gradual da simulação apenas se houve arrasto real
        if (d._isDragging) {
          simulation.alphaTarget(0)
        }
        d.fx = null
        d.fy = null
        d._isDragging = false
      })
    )
    .on('click', (event, d) => {
      event.stopPropagation()
      // Redefinir estilo de todos os nos
      node.attr('stroke', '#fff').attr('stroke-width', 2.5)
      linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
      // Destacar no selecionado
      d3.select(event.target).attr('stroke', '#d4a017').attr('stroke-width', 4)
      // Destacar arestas conectadas a este nó
      link.filter(l => l.source.id === d.id || l.target.id === d.id)
        .attr('stroke', '#d4a017')
        .attr('stroke-width', 2.5)
      
      selectedItem.value = {
        type: 'node',
        data: d.rawData,
        entityType: d.type,
        color: getColor(d.type)
      }
    })
    .on('mouseenter', (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).attr('stroke', '#333').attr('stroke-width', 3)
      }
    })
    .on('mouseleave', (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).attr('stroke', '#fff').attr('stroke-width', 2.5)
      }
    })

  // Node Labels
  const nodeLabels = nodeGroup.selectAll('text')
    .data(nodes)
    .enter().append('text')
    .text(d => d.name.length > 8 ? d.name.substring(0, 8) + '…' : d.name)
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('font-weight', '500')
    .attr('dx', 14)
    .attr('dy', 4)
    .style('pointer-events', 'none')
    .style('font-family', 'system-ui, sans-serif')

  simulation.on('tick', () => {
    // Atualizar caminho da curva
    link.attr('d', d => getLinkPath(d))
    
    // Atualizar posição dos rótulos das arestas (sem rotação, exibição horizontal mais clara)
    linkLabels.each(function(d) {
      const mid = getLinkMidpoint(d)
      d3.select(this)
        .attr('x', mid.x)
        .attr('y', mid.y)
        .attr('transform', '') // Remover rotação, manter horizontal
    })
    
    // Atualizar fundo dos rótulos das arestas
    linkLabelBg.each(function(d, i) {
      const mid = getLinkMidpoint(d)
      const textEl = linkLabels.nodes()[i]
      const bbox = textEl.getBBox()
      d3.select(this)
        .attr('x', mid.x - bbox.width / 2 - 4)
        .attr('y', mid.y - bbox.height / 2 - 2)
        .attr('width', bbox.width + 8)
        .attr('height', bbox.height + 4)
        .attr('transform', '') // Remover rotação
    })

    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)

    nodeLabels
      .attr('x', d => d.x)
      .attr('y', d => d.y)
  })
  
  // Clicar em área vazia para fechar painel de detalhes
  svg.on('click', () => {
    selectedItem.value = null
    node.attr('stroke', '#fff').attr('stroke-width', 2.5)
    linkGroup.selectAll('path').attr('stroke', '#C0C0C0').attr('stroke-width', 1.5)
    linkLabelBg.attr('fill', 'rgba(255,255,255,0.95)')
    linkLabels.attr('fill', '#666')
  })
}

watch(() => props.graphData, () => {
  nextTick(renderGraph)
}, { deep: true })

// Observar interruptor de exibição de rótulos das arestas
watch(showEdgeLabels, (newVal) => {
  if (linkLabelsRef) {
    linkLabelsRef.style('display', newVal ? 'block' : 'none')
  }
  if (linkLabelBgRef) {
    linkLabelBgRef.style('display', newVal ? 'block' : 'none')
  }
})

const handleResize = () => {
  nextTick(renderGraph)
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (currentSimulation) {
    currentSimulation.stop()
  }
})
</script>

<style scoped>
.graph-panel {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #f7f2e8;
  background-image:
    radial-gradient(rgba(15, 39, 71, 0.12) 1.2px, transparent 1.2px),
    radial-gradient(circle at top right, rgba(212, 160, 23, 0.14), transparent 28%);
  background-size: 24px 24px;
  overflow: hidden;
}

.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 16px 20px;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, rgba(247, 242, 232, 0.95), rgba(247, 242, 232, 0));
  pointer-events: none;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f2747;
  pointer-events: auto;
}

.header-tools {
  pointer-events: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.tool-btn {
  height: 32px;
  padding: 0 12px;
  border: 1px solid rgba(15, 39, 71, 0.12);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  color: #4b5563;
  transition: all 0.2s;
  box-shadow: 0 10px 24px rgba(15, 39, 71, 0.08);
  font-size: 13px;
}

.tool-btn:hover {
  background: rgba(212, 160, 23, 0.12);
  color: #0f2747;
  border-color: rgba(212, 160, 23, 0.45);
}

.tool-btn .btn-text {
  font-size: 12px;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.graph-container {
  width: 100%;
  height: 100%;
}

.graph-view, .graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.graph-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.2;
}

/* Entity Types Legend - Bottom Left */
.graph-legend {
  position: absolute;
  bottom: 24px;
  left: 24px;
  background: rgba(255, 250, 240, 0.96);
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid rgba(15, 39, 71, 0.1);
  box-shadow: 0 12px 32px rgba(15, 39, 71, 0.1);
  z-index: 10;
}

.legend-title {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #0f2747;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  max-width: 320px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #4b5563;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  white-space: nowrap;
}

/* Edge Labels Toggle - Top Right */
.edge-labels-toggle {
  position: absolute;
  top: 60px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.92);
  padding: 8px 14px;
  border-radius: 20px;
  border: 1px solid rgba(15, 39, 71, 0.12);
  box-shadow: 0 10px 24px rgba(15, 39, 71, 0.08);
  z-index: 10;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(15, 39, 71, 0.18);
  border-radius: 22px;
  transition: 0.3s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: 0.3s;
}

input:checked + .slider {
  background-color: #d4a017;
}

input:checked + .slider:before {
  transform: translateX(18px);
}

.toggle-label {
  font-size: 12px;
  color: #4b5563;
}

/* Detail Panel - Right Side */
.detail-panel {
  position: absolute;
  top: 60px;
  right: 20px;
  width: 320px;
  max-height: calc(100% - 100px);
  background: rgba(255, 250, 240, 0.98);
  border: 1px solid rgba(15, 39, 71, 0.12);
  border-radius: 10px;
  box-shadow: 0 20px 40px rgba(15, 39, 71, 0.14);
  overflow: hidden;
  font-family: 'Noto Sans SC', system-ui, sans-serif;
  font-size: 13px;
  z-index: 20;
  display: flex;
  flex-direction: column;
}

.detail-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: linear-gradient(180deg, rgba(15, 39, 71, 0.05), rgba(255, 255, 255, 0.9));
  border-bottom: 1px solid rgba(15, 39, 71, 0.08);
  flex-shrink: 0;
}

.detail-title {
  font-weight: 600;
  color: #0f2747;
  font-size: 14px;
}

.detail-type-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  margin-left: auto;
  margin-right: 12px;
}

.detail-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #6b7280;
  line-height: 1;
  padding: 0;
  transition: color 0.2s;
}

.detail-close:hover {
  color: #1f2937;
}

.detail-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.detail-row {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-label {
  color: #888;
  font-size: 12px;
  font-weight: 500;
  min-width: 80px;
}

.detail-value {
  color: #333;
  flex: 1;
  word-break: break-word;
}

.detail-value.uuid-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #6b7280;
}

.detail-value.fact-text {
  line-height: 1.5;
  color: #444;
}

.detail-section {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(15, 39, 71, 0.08);
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 10px;
}

.properties-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.property-item {
  display: flex;
  gap: 8px;
}

.property-key {
  color: #888;
  font-weight: 500;
  min-width: 90px;
}

.property-value {
  color: #333;
  flex: 1;
}

.summary-text {
  line-height: 1.6;
  color: #444;
  font-size: 12px;
}

.labels-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.label-tag {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(212, 160, 23, 0.08);
  border: 1px solid rgba(212, 160, 23, 0.2);
  border-radius: 16px;
  font-size: 11px;
  color: #4b5563;
}

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-tag {
  display: inline-block;
  padding: 6px 10px;
  background: rgba(15, 39, 71, 0.04);
  border: 1px solid rgba(15, 39, 71, 0.08);
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #4b5563;
  word-break: break-all;
}

/* Edge relation header */
.edge-relation-header {
  background: rgba(15, 39, 71, 0.05);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  font-weight: 500;
  color: #0f2747;
  line-height: 1.5;
  word-break: break-word;
}

/* Building hint */
.graph-building-hint {
  position: absolute;
  bottom: 160px; /* Moved up from 80px */
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 39, 71, 0.84);
  backdrop-filter: blur(8px);
  color: #fff;
  padding: 10px 20px;
  border-radius: 30px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-weight: 500;
  letter-spacing: 0.5px;
  z-index: 100;
}

.memory-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  animation: breathe 2s ease-in-out infinite;
}

.memory-icon {
  width: 18px;
  height: 18px;
  color: #f2c14a;
}

@keyframes breathe {
  0%, 100% { opacity: 0.7; transform: scale(1); filter: drop-shadow(0 0 2px rgba(212, 160, 23, 0.3)); }
  50% { opacity: 1; transform: scale(1.15); filter: drop-shadow(0 0 8px rgba(212, 160, 23, 0.55)); }
}

/* Estilo do aviso após término da simulação */
.graph-building-hint.finished-hint {
  background: rgba(15, 39, 71, 0.84);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.finished-hint .hint-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.finished-hint .hint-icon {
  width: 18px;
  height: 18px;
  color: #FFF;
}

.finished-hint .hint-text {
  flex: 1;
  white-space: nowrap;
}

.hint-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #FFF;
  transition: all 0.2s;
  margin-left: 8px;
  flex-shrink: 0;
}

.hint-close-btn:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: scale(1.1);
}

/* Loading spinner */
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(15, 39, 71, 0.12);
  border-top-color: #d4a017;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

/* Self-loop styles */
.self-loop-header {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #E8F5E9 0%, #F1F8E9 100%);
  border: 1px solid #C8E6C9;
}

.self-loop-count {
  margin-left: auto;
  font-size: 11px;
  color: #666;
  background: rgba(255,255,255,0.8);
  padding: 2px 8px;
  border-radius: 10px;
}

.self-loop-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.self-loop-item {
  background: #FAFAFA;
  border: 1px solid #EAEAEA;
  border-radius: 8px;
}

.self-loop-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #F5F5F5;
  cursor: pointer;
  transition: background 0.2s;
}

.self-loop-item-header:hover {
  background: #EEEEEE;
}

.self-loop-item.expanded .self-loop-item-header {
  background: #E8E8E8;
}

.self-loop-index {
  font-size: 10px;
  font-weight: 600;
  color: #888;
  background: #E0E0E0;
  padding: 2px 6px;
  border-radius: 4px;
}

.self-loop-name {
  font-size: 12px;
  font-weight: 500;
  color: #333;
  flex: 1;
}

.self-loop-toggle {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: #888;
  background: #E0E0E0;
  border-radius: 4px;
  transition: all 0.2s;
}

.self-loop-item.expanded .self-loop-toggle {
  background: #D0D0D0;
  color: #666;
}

.self-loop-item-content {
  padding: 12px;
  border-top: 1px solid #EAEAEA;
}

.self-loop-item-content .detail-row {
  margin-bottom: 8px;
}

.self-loop-item-content .detail-label {
  font-size: 11px;
  min-width: 60px;
}

.self-loop-item-content .detail-value {
  font-size: 12px;
}

.self-loop-episodes {
  margin-top: 8px;
}

.episodes-list.compact {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 4px;
}

.episode-tag.small {
  padding: 3px 6px;
  font-size: 9px;
}
</style>
