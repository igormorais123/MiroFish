import service, { requestWithRetry } from './index'

const getApiBasePath = () => {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/mirofish')) return '/mirofish'
  return ''
}

const requestReportExport = async (path, options = {}) => {
  const response = await fetch(`${getApiBasePath()}${path}`, {
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  const payload = await response.json().catch(() => ({}))
  if (!response.ok || (payload.success === false && !options.allowFailurePayload)) {
    const error = new Error(payload.error || payload.message || `HTTP ${response.status}`)
    error.status = response.status
    error.data = payload
    throw error
  }
  return payload
}

/**
 * Iniciar geracao do relatorio
 * @param {Object} data - { simulation_id, force_regenerate? }
 */
export const generateReport = (data) => {
  return requestWithRetry(() => service.post('/api/report/generate', data), 3, 1000)
}

/**
 * Obter catalogo formal de poderes da missão
 * @param {Object} params - { categoria?, tipo? }
 */
export const getPowerCatalog = (params = {}) => {
  return service.get('/api/report/power-catalog', { params })
}

/**
 * Estimar impacto comercial dos poderes selecionados
 * @param {Object} payload - { selected_power_ids?, base_tokens?, base_value_brl? }
 */
export const estimatePowers = (payload) => {
  return service.post('/api/report/power-estimate', payload)
}

/**
 * Obter catalogo seguro de poderes e personas
 * @param {Object} params - { tipo?, q?, limit? }
 */
export const getPowerPersonaCatalog = (params = {}) => {
  return service.get('/api/report/power-persona-catalog', { params })
}

/**
 * Montar contexto de poderes e personas selecionados
 * @param {Object} payload - { selected_power_persona_ids?, tipo? }
 */
export const buildPowerPersonaContext = (payload) => {
  return service.post('/api/report/power-persona-context', payload)
}

/**
 * Obter status de geracao do relatorio
 * @param {string} reportId
 */
export const getReportStatus = (reportId) => {
  return service.get(`/api/report/generate/status`, { params: { report_id: reportId } })
}

/**
 * Obter logs do agente (incremental)
 * @param {string} reportId
 * @param {number} fromLine - A partir de qual linha obter
 */
export const getAgentLog = (reportId, fromLine = 0) => {
  return service.get(`/api/report/${reportId}/agent-log`, { params: { from_line: fromLine } })
}

/**
 * Obter logs do console (incremental)
 * @param {string} reportId
 * @param {number} fromLine - A partir de qual linha obter
 */
export const getConsoleLog = (reportId, fromLine = 0) => {
  return service.get(`/api/report/${reportId}/console-log`, { params: { from_line: fromLine } })
}

/**
 * Obter detalhes do relatorio
 * @param {string} reportId
 */
export const getReport = (reportId) => {
  return service.get(`/api/report/${reportId}`)
}

/**
 * Obter secoes geradas do relatorio
 * @param {string} reportId
 */
export const getReportSections = (reportId) => {
  return service.get(`/api/report/${reportId}/sections`)
}

/**
 * Listar artefatos de auditoria do relatorio
 * @param {string} reportId
 * @param {boolean} includeContent
 */
export const getReportArtifacts = (reportId, includeContent = false) => {
  return service.get(`/api/report/${reportId}/artifacts`, { params: { include_content: includeContent } })
}

export const getReportDeliveryPackage = (reportId) => {
  return service.get(`/api/report/${reportId}/delivery-package`)
}

export const getReportEvolutionReadiness = (reportId) => {
  return service.get(`/api/report/${reportId}/evolution-readiness`)
}

export const repairReportFinalization = (reportId) => {
  return service.post(`/api/report/${reportId}/finalization/repair`)
}

export const repairReportContent = (reportId) => {
  return service.post(`/api/report/${reportId}/content/repair`)
}

export const createExecutivePackage = (reportId) => {
  return service.post(`/api/report/${reportId}/executive-package`)
}

export const getExecutivePackageAttachmentUrl = (reportId, filename) => {
  const safeFilename = [
    'executive_summary.html',
    'evidence_annex.html',
    'executive_package_manifest.json'
  ].includes(filename) ? filename : ''
  if (!safeFilename) return ''
  return `${getApiBasePath()}/api/report/${encodeURIComponent(reportId)}/executive-package/${encodeURIComponent(safeFilename)}`
}

export const createReportExport = (reportId) => {
  return requestReportExport(`/api/report/${encodeURIComponent(reportId)}/exports`, {
    method: 'POST'
  })
}

export const getReportExports = (reportId) => {
  return requestReportExport(`/api/report/${encodeURIComponent(reportId)}/exports`)
}

export const verifyReportExportBundle = (reportId, exportId) => {
  return requestReportExport(
    `/api/report/${encodeURIComponent(reportId)}/exports/${encodeURIComponent(exportId)}/bundle/verify`,
    { method: 'POST', allowFailurePayload: true }
  )
}

export const getReportExportAttachmentUrl = (reportId, exportId, filename) => {
  const safeFilename = ['full_report.html', 'evidence_annex.html'].includes(filename) ? filename : ''
  if (!safeFilename) return ''
  return `${getApiBasePath()}/api/report/${encodeURIComponent(reportId)}/exports/${encodeURIComponent(exportId)}/${encodeURIComponent(safeFilename)}`
}

/**
 * Obter artefato especifico de auditoria do relatorio
 * @param {string} reportId
 * @param {string} artifactName
 */
export const getReportArtifact = (reportId, artifactName) => {
  return service.get(`/api/report/${reportId}/artifacts/${artifactName}`)
}

/**
 * Gerar manifesto final da missão
 * @param {string} reportId
 */
export const getMissionBundle = (reportId) => {
  return service.get(`/api/report/${reportId}/mission-bundle`)
}

/**
 * Conversar com o Report Agent
 * @param {Object} data - { simulation_id, message, chat_history? }
 */
export const chatWithReport = (data) => {
  return requestWithRetry(() => service.post('/api/report/chat', data), 3, 1000)
}
