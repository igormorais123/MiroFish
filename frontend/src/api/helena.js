import service, { API_TIMEOUTS } from './index'

const authConfig = (token, extra = {}) => ({
  ...extra,
  headers: {
    ...(extra.headers || {}),
    'X-Internal-Token': token
  }
})

export const getHelenaStatus = () => service.get('/api/helena/status')

export const openHelenaSession = token => (
  service.post('/api/helena/session', {}, authConfig(token))
)

export const getHelenaContext = (token, context) => (
  service.post('/api/helena/context', { context }, authConfig(token))
)

export const planHelenaCommand = (token, command, context, idempotencyKey) => (
  service.post(
    '/api/helena/commands/plan',
    { command, context },
    authConfig(token, {
      timeout: API_TIMEOUTS.slow,
      headers: { 'Idempotency-Key': idempotencyKey }
    })
  )
)

export const executeHelenaCommand = (token, commandId, approvalToken) => (
  service.post(
    `/api/helena/commands/${encodeURIComponent(commandId)}/execute`,
    { approval_token: approvalToken || null },
    authConfig(token)
  )
)

export const completeHelenaCommand = (
  token,
  commandId,
  executionTicket,
  success,
  result,
  error
) => (
  service.post(
    `/api/helena/commands/${encodeURIComponent(commandId)}/complete`,
    {
      execution_ticket: executionTicket,
      success,
      result,
      error: error || null
    },
    authConfig(token)
  )
)

export const cancelHelenaCommand = (token, commandId) => (
  service.post(
    `/api/helena/commands/${encodeURIComponent(commandId)}/cancel`,
    {},
    authConfig(token)
  )
)

export const listHelenaCommands = (token, limit = 20) => (
  service.get('/api/helena/commands', authConfig(token, { params: { limit } }))
)

export const runInternalPreset = (token, payload) => (
  service.post(
    '/api/internal/v1/run-preset',
    payload,
    authConfig(token, { timeout: API_TIMEOUTS.normal })
  )
)
