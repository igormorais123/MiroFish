import service, { requestWithRetry } from './index'

/**
 * Gerar ontologia (upload de documentos e requisito de simulacao)
 * @param {Object} data - Contem files, simulation_requirement, project_name etc.
 * @returns {Promise}
 */
export function generateOntology(formData) {
  return requestWithRetry(() => 
    service({
      url: '/api/graph/ontology/generate',
      method: 'post',
      data: formData
    })
  , 1)
}

/**
 * Construir grafo
 * @param {Object} data - Contem project_id, graph_name etc.
 * @returns {Promise}
 */
export function buildGraph(data) {
  return requestWithRetry(() =>
    service({
      url: '/api/graph/build',
      method: 'post',
      data
    })
  )
}

/**
 * Consultar status da tarefa
 * @param {String} taskId - ID da tarefa
 * @returns {Promise}
 */
export function getTaskStatus(taskId) {
  return service({
    url: `/api/graph/task/${taskId}`,
    method: 'get'
  })
}

/**
 * Obter dados do grafo
 * @param {String} graphId - ID do grafo
 * @returns {Promise}
 */
export function getGraphData(graphId) {
  return service({
    url: `/api/graph/data/${graphId}`,
    method: 'get'
  })
}

/**
 * Obter informacoes do projeto
 * @param {String} projectId - ID do projeto
 * @returns {Promise}
 */
export function getProject(projectId) {
  return service({
    url: `/api/graph/project/${projectId}`,
    method: 'get'
  })
}
