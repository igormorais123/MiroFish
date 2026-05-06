import service, { requestWithRetry } from './index'

/**
 * Criar simulacao
 * @param {Object} data - { project_id, graph_id?, enable_twitter?, enable_reddit? }
 */
export const createSimulation = (data) => {
  return requestWithRetry(() => service.post('/api/simulation/create', data), 3, 1000)
}

/**
 * Preparar ambiente de simulacao (tarefa assincrona)
 * @param {Object} data - { simulation_id, entity_types?, use_llm_for_profiles?, parallel_profile_count?, force_regenerate? }
 */
export const prepareSimulation = (data) => {
  return requestWithRetry(() => service.post('/api/simulation/prepare', data), 3, 1000)
}

/**
 * Consultar progresso da tarefa de preparacao
 * @param {Object} data - { task_id?, simulation_id? }
 */
export const getPrepareStatus = (data) => {
  return service.post('/api/simulation/prepare/status', data)
}

/**
 * Obter status da simulacao
 * @param {string} simulationId
 */
export const getSimulation = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}`)
}

/**
 * Obter Agent Profiles da simulacao
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 */
export const getSimulationProfiles = (simulationId, platform = 'reddit') => {
  return service.get(`/api/simulation/${simulationId}/profiles`, { params: { platform } })
}

/**
 * Obter Agent Profiles em geracao em tempo real
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 */
export const getSimulationProfilesRealtime = (simulationId, platform = 'reddit') => {
  return service.get(`/api/simulation/${simulationId}/profiles/realtime`, { params: { platform } })
}

/**
 * Obter configuracao da simulacao
 * @param {string} simulationId
 */
export const getSimulationConfig = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}/config`)
}

/**
 * Obter configuracao da simulacao em geracao em tempo real
 * @param {string} simulationId
 * @returns {Promise} Retorna informacoes de configuracao, incluindo metadados e conteudo
 */
export const getSimulationConfigRealtime = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}/config/realtime`)
}

/**
 * Obter escolhas de poderes e personas da missao
 * @param {string} simulationId
 */
export const getMissionSelection = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}/mission-selection`)
}

/**
 * Salvar escolhas de poderes e personas da missao
 * @param {string} simulationId
 * @param {Object} data - { selected_power_ids?, selected_power_persona_ids?, modo_custo? }
 */
export const saveMissionSelection = (simulationId, data) => {
  return service.post(`/api/simulation/${simulationId}/mission-selection`, data)
}

/**
 * Listar todas as simulacoes
 * @param {string} projectId - Opcional, filtrar por ID do projeto
 */
export const listSimulations = (projectId) => {
  const params = projectId ? { project_id: projectId } : {}
  return service.get('/api/simulation/list', { params })
}

/**
 * Iniciar simulacao
 * @param {Object} data - { simulation_id, platform?, max_rounds?, enable_graph_memory_update? }
 */
export const startSimulation = (data) => {
  return service.post('/api/simulation/start', data)
}

/**
 * Parar simulacao
 * @param {Object} data - { simulation_id }
 */
export const stopSimulation = (data) => {
  return service.post('/api/simulation/stop', data)
}

/**
 * Obter status em tempo real da execucao da simulacao
 * @param {string} simulationId
 */
export const getRunStatus = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}/run-status`)
}

/**
 * Obter status detalhado da execucao (incluindo acoes recentes)
 * @param {string} simulationId
 */
export const getRunStatusDetail = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}/run-status/detail`)
}

/**
 * Obter leitura consolidada de qualidade da simulacao
 * @param {string} simulationId
 * @param {Object} params - { require_completed? }
 */
export const getSimulationQuality = (simulationId, params = {}) => {
  return service.get(`/api/simulation/${simulationId}/quality`, { params })
}

export const getSimulationReadiness = (simulationId, params = {}) => {
  return service.get(`/api/simulation/${simulationId}/readiness`, { params })
}

/**
 * Obter postagens da simulacao
 * @param {string} simulationId
 * @param {string} platform - 'reddit' | 'twitter'
 * @param {number} limit - Quantidade de retorno
 * @param {number} offset - Deslocamento
 */
export const getSimulationPosts = (simulationId, platform = 'reddit', limit = 50, offset = 0) => {
  return service.get(`/api/simulation/${simulationId}/posts`, {
    params: { platform, limit, offset }
  })
}

/**
 * Obter timeline da simulacao (agregada por rodada)
 * @param {string} simulationId
 * @param {number} startRound - Rodada inicial
 * @param {number} endRound - Rodada final
 */
export const getSimulationTimeline = (simulationId, startRound = 0, endRound = null) => {
  const params = { start_round: startRound }
  if (endRound !== null) {
    params.end_round = endRound
  }
  return service.get(`/api/simulation/${simulationId}/timeline`, { params })
}

/**
 * Obter estatisticas dos agentes
 * @param {string} simulationId
 */
export const getAgentStats = (simulationId) => {
  return service.get(`/api/simulation/${simulationId}/agent-stats`)
}

/**
 * Obter historico de acoes da simulacao
 * @param {string} simulationId
 * @param {Object} params - { limit, offset, platform, agent_id, round_num }
 */
export const getSimulationActions = (simulationId, params = {}) => {
  return service.get(`/api/simulation/${simulationId}/actions`, { params })
}

/**
 * Encerrar ambiente de simulacao (saida graciosa)
 * @param {Object} data - { simulation_id, timeout? }
 */
export const closeSimulationEnv = (data) => {
  return service.post('/api/simulation/close-env', data)
}

/**
 * Obter status do ambiente de simulacao
 * @param {Object} data - { simulation_id }
 */
export const getEnvStatus = (data) => {
  return service.post('/api/simulation/env-status', data)
}

/**
 * Entrevistar agentes em lote
 * @param {Object} data - { simulation_id, interviews: [{ agent_id, prompt }] }
 */
export const interviewAgents = (data) => {
  return requestWithRetry(() => service.post('/api/simulation/interview/batch', data), 3, 1000)
}

/**
 * Obter lista historica de simulacoes (com detalhes do projeto)
 * Usado para exibicao de projetos historicos na pagina inicial
 * @param {number} limit - Limite de quantidade de retorno
 */
export const getSimulationHistory = (limit = 20) => {
  return service.get('/api/simulation/history', { params: { limit } })
}

