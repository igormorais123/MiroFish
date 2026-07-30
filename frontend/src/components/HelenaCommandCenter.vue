<template>
  <div class="helena-root" :class="{ 'is-open': isOpen }">
    <button
      v-if="!isOpen"
      class="helena-launcher"
      type="button"
      aria-label="Abrir IA Friend Helena"
      title="IA Friend Helena · Alt+H"
      @click="openPanel"
    >
      <span class="launcher-orbit" aria-hidden="true"></span>
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3a5 5 0 0 0-4.6 7H6a3 3 0 0 0 0 6h1.4a5 5 0 0 0 9.2 0H18a3 3 0 1 0 0-6h-1.4A5 5 0 0 0 12 3Z" />
        <path d="M9 12h6M12 9v6" />
      </svg>
      <span class="launcher-label">
        <strong>IA Friend</strong>
        <small>Helena · Alt+H</small>
      </span>
    </button>

    <section
      v-else
      ref="panelRef"
      class="helena-panel"
      role="dialog"
      aria-labelledby="helena-title"
      @keydown.esc="closePanel"
    >
      <header class="helena-header">
        <div class="helena-identity">
          <div class="helena-mark" aria-hidden="true">H</div>
          <div>
            <p class="eyebrow">IA FRIEND · CONTEXTO VIVO</p>
            <h2 id="helena-title">Helena</h2>
          </div>
        </div>
        <div class="header-actions">
          <span class="availability" :class="availabilityClass">
            <span class="status-dot" aria-hidden="true"></span>
            {{ availabilityLabel }}
          </span>
          <button
            class="icon-button"
            type="button"
            aria-label="Fechar IA Friend Helena"
            @click="closePanel"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m6 6 12 12M18 6 6 18" />
            </svg>
          </button>
        </div>
      </header>

      <div class="context-strip">
        <span class="phase-chip">{{ phaseLabel }}</span>
        <span class="context-id">{{ contextIdentifier }}</span>
        <button
          v-if="authenticated"
          class="text-button"
          type="button"
          @click="refreshContext"
        >
          Atualizar
        </button>
      </div>
      <div class="next-step-strip">
        <span>PRÓXIMA AÇÃO</span>
        <p>{{ contextualNextStep }}</p>
      </div>

      <main class="helena-body">
        <div v-if="loadingStatus" class="center-state" aria-live="polite">
          <span class="spinner" aria-hidden="true"></span>
          Verificando o console…
        </div>

        <div v-else-if="!status.available" class="empty-state" role="status">
          <div class="empty-icon" aria-hidden="true">!</div>
          <h3>Console indisponível</h3>
          <p>
            O backend precisa de <code>INTERNAL_API_TOKEN</code> e
            <code>HELENA_CONTROL_ENABLED=true</code>.
          </p>
        </div>

        <form v-else-if="!authenticated" class="auth-card" @submit.prevent="authenticate">
          <div class="security-lock" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <rect x="5" y="10" width="14" height="10" rx="2" />
              <path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v2" />
            </svg>
          </div>
          <div>
            <h3>Acesso restrito</h3>
            <p>O token fica somente na memória desta aba e é apagado ao recarregar.</p>
          </div>
          <label for="helena-token">Token interno</label>
          <div class="input-row">
            <input
              id="helena-token"
              ref="tokenInputRef"
              v-model="tokenDraft"
              :type="showToken ? 'text' : 'password'"
              autocomplete="off"
              spellcheck="false"
              placeholder="Cole o token operacional"
              required
            />
            <button
              class="reveal-button"
              type="button"
              :aria-label="showToken ? 'Ocultar token' : 'Mostrar token'"
              @click="showToken = !showToken"
            >
              {{ showToken ? 'Ocultar' : 'Mostrar' }}
            </button>
          </div>
          <button class="primary-button" type="submit" :disabled="busy || !tokenDraft.trim()">
            <span v-if="busy" class="spinner small" aria-hidden="true"></span>
            Desbloquear Helena
          </button>
          <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
        </form>

        <template v-else>
          <section class="command-workspace">
            <div class="workspace-heading">
              <div>
                <p class="eyebrow">OBJETIVO EM LINGUAGEM NATURAL</p>
                <h3>Que resultado você precisa agora?</h3>
              </div>
              <button class="text-button danger" type="button" @click="lockSession">
                Bloquear
              </button>
            </div>

            <label class="sr-only" for="helena-command">Comando para Helena</label>
            <textarea
              id="helena-command"
              ref="commandInputRef"
              v-model="command"
              rows="4"
              maxlength="4000"
              placeholder="Ex.: Confira o lastro documental, mostre as lacunas e proponha a próxima ação segura."
              :disabled="busy || executionState === 'executing'"
              @keydown.ctrl.enter.prevent="requestPlan"
            ></textarea>
            <div class="command-suggestions" aria-label="Comandos sugeridos">
              <button
                v-for="suggestion in commandSuggestions"
                :key="suggestion.label"
                type="button"
                :disabled="busy || executionState === 'executing'"
                @click="command = suggestion.command"
              >
                <span>{{ suggestion.label }}</span>
                <small>{{ suggestion.hint }}</small>
              </button>
            </div>
            <div class="composer-footer">
              <span>Plano primeiro · Ctrl+Enter</span>
              <span>{{ command.length }}/4000</span>
            </div>
            <button
              class="primary-button"
              type="button"
              :disabled="busy || !command.trim() || executionState === 'executing'"
              @click="requestPlan"
            >
              <span v-if="busy && executionState === 'planning'" class="spinner small" aria-hidden="true"></span>
              {{ executionState === 'planning' ? 'Helena está planejando…' : 'Criar plano seguro' }}
            </button>
          </section>

          <section v-if="currentCommand" class="plan-card" aria-live="polite">
            <div class="plan-header">
              <div>
                <p class="eyebrow">PLANO VALIDADO</p>
                <h3>{{ currentCommand.plan.summary }}</h3>
              </div>
              <span class="risk-badge" :class="`risk-${currentCommand.plan.risk}`">
                {{ riskLabel(currentCommand.plan.risk) }}
              </span>
            </div>
            <p class="plan-rationale">{{ currentCommand.plan.rationale }}</p>
            <ol class="action-list">
              <li v-for="(action, index) in currentCommand.plan.actions" :key="`${action.tool}-${index}`">
                <span class="action-index">{{ String(index + 1).padStart(2, '0') }}</span>
                <div>
                  <strong>{{ action.description }}</strong>
                  <span>{{ toolLabel(action.tool) }}</span>
                </div>
                <span v-if="action.mutates" class="mutation-tag">altera estado</span>
                <span v-else class="read-tag">leitura</span>
              </li>
            </ol>

            <div v-if="executionState === 'executing'" class="execution-progress">
              <div class="progress-copy">
                <span>{{ progressMessage }}</span>
                <strong v-if="progressValue !== null">{{ progressValue }}%</strong>
              </div>
              <div class="progress-track" aria-hidden="true">
                <span :style="{ width: `${progressValue ?? 12}%` }"></span>
              </div>
            </div>

            <div v-if="executionLogs.length" class="activity-log">
              <p class="eyebrow">ATIVIDADE</p>
              <ul>
                <li v-for="entry in executionLogs.slice(-6)" :key="entry.id">
                  <time>{{ entry.time }}</time>
                  <span>{{ entry.message }}</span>
                </li>
              </ul>
            </div>

            <div v-if="executionResult" class="result-card" :class="{ failed: executionState === 'failed' }">
              <strong>
                {{
                  executionState === 'completed'
                    ? 'Concluído'
                    : executionState === 'cancelled'
                      ? 'Cancelado com segurança'
                      : 'Execução falhou'
                }}
              </strong>
              <p>{{ executionResult }}</p>
            </div>

            <div
              v-if="currentCommand.status === 'pending_approval' && executionState !== 'executing'"
              class="approval-notice"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3 3.5 7v5c0 4.8 3.6 8 8.5 9 4.9-1 8.5-4.2 8.5-9V7L12 3Z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
              <p>
                Revise o plano. A aprovação é válida uma vez e expira automaticamente.
              </p>
            </div>

            <div class="plan-actions">
              <button
                v-if="['pending_approval', 'ready'].includes(currentCommand.status)"
                class="primary-button"
                :class="{ 'high-risk': currentCommand.plan.risk === 'high' }"
                type="button"
                :disabled="busy"
                @click="approveAndExecute"
              >
                {{ currentCommand.plan.requires_approval ? 'Aprovar e executar' : 'Executar plano' }}
              </button>
              <button
                v-if="['pending_approval', 'ready'].includes(currentCommand.status)"
                class="secondary-button"
                type="button"
                :disabled="busy"
                @click="cancelPlan"
              >
                Cancelar
              </button>
              <button
                v-if="['completed', 'failed', 'cancelled'].includes(currentCommand.status)"
                class="secondary-button"
                type="button"
                @click="resetComposer"
              >
                Novo comando
              </button>
            </div>
          </section>

          <details class="audit-section" @toggle="loadHistory">
            <summary>
              <span>Trilha de auditoria</span>
              <span>{{ commandHistory.length ? `${commandHistory.length} registros` : 'abrir' }}</span>
            </summary>
            <div v-if="historyBusy" class="audit-loading">Carregando…</div>
            <ul v-else-if="commandHistory.length" class="audit-list">
              <li v-for="item in commandHistory" :key="item.command_id">
                <span class="audit-status" :class="`status-${item.status}`"></span>
                <div>
                  <strong>{{ item.plan?.summary || 'Comando Helena' }}</strong>
                  <span>{{ formatDate(item.created_at) }} · {{ statusLabel(item.status) }}</span>
                </div>
              </li>
            </ul>
            <p v-else class="audit-empty">Nenhum comando registrado.</p>
          </details>

          <p v-if="errorMessage" class="error-message sticky-error" role="alert">
            {{ errorMessage }}
          </p>
        </template>
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  cancelHelenaCommand,
  completeHelenaCommand,
  executeHelenaCommand,
  getHelenaContext,
  getHelenaStatus,
  listHelenaCommands,
  openHelenaSession,
  planHelenaCommand
} from '../api/helena'
import { createDefaultHelenaDependencies } from '../services/helenaDependencies'
import { executeHelenaPlan } from '../services/helenaExecutor'

const route = useRoute()
const router = useRouter()

const isOpen = ref(false)
const loadingStatus = ref(false)
const status = ref({ enabled: false, available: false })
const authenticated = ref(false)
const sessionToken = ref('')
const tokenDraft = ref('')
const showToken = ref(false)
const command = ref('')
const currentCommand = ref(null)
const approvalToken = ref('')
const executionState = ref('idle')
const executionLogs = ref([])
const executionResult = ref('')
const progressMessage = ref('')
const progressValue = ref(null)
const errorMessage = ref('')
const busy = ref(false)
const commandHistory = ref([])
const historyBusy = ref(false)
const resolvedContext = ref(null)
const panelRef = ref(null)
const tokenInputRef = ref(null)
const commandInputRef = ref(null)

const routeContext = computed(() => ({
  route_name: String(route.name || 'Home'),
  path: route.fullPath,
  project_id: route.params.projectId === 'new' ? null : route.params.projectId,
  simulation_id: route.params.simulationId,
  report_id: route.params.reportId
}))

const phaseLabels = {
  Home: 'Visão geral',
  Process: 'Fase 1–2 · Lastro e grafo',
  Simulation: 'Fase 3 · Gate de método',
  SimulationRun: 'Fase 3 · Execução aplicável',
  Report: 'Fase 4 · Produtos e relatório',
  Interaction: 'Fase 5 · Cocriação'
}

const phaseLabel = computed(() => phaseLabels[String(route.name)] || 'MiroFish')
const nextSteps = {
  Home: 'Envie os autos e descreva a peça, tese ou decisão que precisa apoiar.',
  Process: 'Confira a proveniência do grafo antes de avançar para qualquer conclusão.',
  Simulation: 'Valide se o domínio comporta simulação; matéria judicial permanece documental por padrão.',
  SimulationRun: 'Acompanhe somente a execução autorizada e preserve os recibos de auditoria.',
  Report: 'Revise cronologia, omissões, cobertura de teses, contradições e lacunas.',
  Interaction: 'Converta achados verificados em orientação, mantendo hipótese e fato separados.'
}
const contextualNextStep = computed(() => (
  nextSteps[String(route.name)] || 'Inspecione o contexto atual e peça um plano antes de agir.'
))
const contextIdentifier = computed(() => {
  const context = resolvedContext.value || routeContext.value
  return context.report_id || context.simulation_id || context.project_id || 'sem processo ativo'
})
const availabilityClass = computed(() => {
  if (authenticated.value) return 'is-online'
  if (status.value.available) return 'is-locked'
  return 'is-offline'
})
const availabilityLabel = computed(() => {
  if (authenticated.value) return 'Operacional'
  if (status.value.available) return 'Bloqueada'
  return 'Indisponível'
})

const commandSuggestions = [
  {
    label: 'Inspecionar o caso',
    hint: 'estado + lacunas + próximo passo',
    command: 'Inspecione o contexto atual. Resuma o que está comprovado, o que falta e qual é a próxima ação segura, sem alterar o processo.'
  },
  {
    label: 'Conferir lastro',
    hint: 'evento + página + trecho',
    command: 'Confira o lastro documental dos achados atuais. Aponte referências verificáveis e separe fatos, inferências e itens não verificados.'
  },
  {
    label: 'Coordenar até a peça',
    hint: 'plano completo com gates',
    command: 'Planeje a análise jurídica até uma base de petição revisável, respeitando os gates de proveniência, aplicabilidade e aprovação humana.'
  }
]

const openPanel = async () => {
  isOpen.value = true
  if (!status.value.enabled && !loadingStatus.value) await loadStatus()
  await nextTick()
  if (authenticated.value) commandInputRef.value?.focus()
  else tokenInputRef.value?.focus()
}

const closePanel = () => {
  isOpen.value = false
}

const loadStatus = async () => {
  loadingStatus.value = true
  errorMessage.value = ''
  try {
    const response = await getHelenaStatus()
    status.value = response.data
  } catch (error) {
    status.value = { enabled: false, available: false }
    errorMessage.value = error.message
  } finally {
    loadingStatus.value = false
  }
}

const authenticate = async () => {
  busy.value = true
  errorMessage.value = ''
  try {
    const candidate = tokenDraft.value.trim()
    await openHelenaSession(candidate)
    sessionToken.value = candidate
    tokenDraft.value = ''
    showToken.value = false
    authenticated.value = true
    await refreshContext()
    await nextTick()
    commandInputRef.value?.focus()
  } catch (error) {
    sessionToken.value = ''
    authenticated.value = false
    errorMessage.value = error.message || 'Falha ao autenticar'
  } finally {
    busy.value = false
  }
}

const lockSession = () => {
  sessionToken.value = ''
  tokenDraft.value = ''
  authenticated.value = false
  currentCommand.value = null
  approvalToken.value = ''
  commandHistory.value = []
  resolvedContext.value = null
  executionLogs.value = []
  executionResult.value = ''
  errorMessage.value = ''
  nextTick(() => tokenInputRef.value?.focus())
}

const refreshContext = async () => {
  if (!sessionToken.value) return
  try {
    const response = await getHelenaContext(sessionToken.value, routeContext.value)
    resolvedContext.value = response.data
  } catch (error) {
    errorMessage.value = error.message
  }
}

const requestPlan = async () => {
  if (!command.value.trim() || busy.value) return
  busy.value = true
  executionState.value = 'planning'
  errorMessage.value = ''
  executionResult.value = ''
  executionLogs.value = []
  progressValue.value = null
  try {
    await refreshContext()
    const idempotencyKey = crypto.randomUUID()
    const response = await planHelenaCommand(
      sessionToken.value,
      command.value.trim(),
      routeContext.value,
      idempotencyKey
    )
    currentCommand.value = response.data
    approvalToken.value = response.data.approval_token || ''
    executionState.value = 'planned'
  } catch (error) {
    executionState.value = 'failed'
    errorMessage.value = error.message || 'Helena nao conseguiu criar o plano'
  } finally {
    busy.value = false
  }
}

const addExecutionLog = (message, progress = null) => {
  progressMessage.value = message
  if (Number.isFinite(progress)) {
    progressValue.value = Math.max(0, Math.min(100, Math.round(progress)))
  }
  executionLogs.value.push({
    id: `${Date.now()}-${executionLogs.value.length}`,
    time: new Date().toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }),
    message
  })
}

const summarizeResult = result => {
  const runtime = result?.runtime || {}
  const last = result?.receipts?.at(-1)?.result || {}
  const response = last.response || last.message || last.task?.message
  if (response) return String(response).slice(0, 1200)
  const ids = [runtime.project_id, runtime.simulation_id, runtime.report_id].filter(Boolean)
  return ids.length
    ? `Fluxo atualizado: ${ids.join(' · ')}`
    : 'O plano foi executado e auditado com sucesso.'
}

const approveAndExecute = async () => {
  if (!currentCommand.value || busy.value) return
  busy.value = true
  executionState.value = 'executing'
  errorMessage.value = ''
  executionResult.value = ''
  progressValue.value = 1
  addExecutionLog('Aprovação validada; iniciando execução', 1)

  let executionTicket = ''
  try {
    const startResponse = await executeHelenaCommand(
      sessionToken.value,
      currentCommand.value.command_id,
      approvalToken.value
    )
    approvalToken.value = ''
    executionTicket = startResponse.data.execution_ticket
    currentCommand.value = startResponse.data.command
    const dependencies = createDefaultHelenaDependencies({
      router,
      token: sessionToken.value
    })
    const runtime = {
      ...(currentCommand.value.context || resolvedContext.value || routeContext.value)
    }
    const result = await executeHelenaPlan(
      startResponse.data.actions,
      runtime,
      dependencies,
      addExecutionLog
    )
    const completeResponse = await completeHelenaCommand(
      sessionToken.value,
      currentCommand.value.command_id,
      executionTicket,
      true,
      result,
      null
    )
    currentCommand.value = completeResponse.data
    executionState.value = 'completed'
    progressValue.value = 100
    progressMessage.value = 'Concluído'
    executionResult.value = summarizeResult(result)
    resolvedContext.value = { ...resolvedContext.value, ...result.runtime }
  } catch (error) {
    const message = error.message || 'A execução falhou'
    executionState.value = 'failed'
    executionResult.value = message
    addExecutionLog(message)
    if (executionTicket && currentCommand.value?.command_id) {
      try {
        const response = await completeHelenaCommand(
          sessionToken.value,
          currentCommand.value.command_id,
          executionTicket,
          false,
          null,
          message
        )
        currentCommand.value = response.data
      } catch (auditError) {
        errorMessage.value = `Execução falhou e a auditoria não confirmou: ${auditError.message}`
      }
    }
  } finally {
    busy.value = false
  }
}

const cancelPlan = async () => {
  if (!currentCommand.value || busy.value) return
  busy.value = true
  errorMessage.value = ''
  try {
    const response = await cancelHelenaCommand(
      sessionToken.value,
      currentCommand.value.command_id
    )
    currentCommand.value = response.data
    approvalToken.value = ''
    executionState.value = 'cancelled'
    executionResult.value = 'Plano cancelado antes de alterar o processo.'
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    busy.value = false
  }
}

const resetComposer = () => {
  currentCommand.value = null
  approvalToken.value = ''
  command.value = ''
  executionState.value = 'idle'
  executionLogs.value = []
  executionResult.value = ''
  progressValue.value = null
  errorMessage.value = ''
  nextTick(() => commandInputRef.value?.focus())
}

const loadHistory = async event => {
  if (!event.target.open || historyBusy.value || !authenticated.value) return
  historyBusy.value = true
  try {
    const response = await listHelenaCommands(sessionToken.value, 20)
    commandHistory.value = response.data
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    historyBusy.value = false
  }
}

const formatDate = value => {
  if (!value) return 'sem data'
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(value))
}

const statusLabel = value => ({
  pending_approval: 'aguardando aprovação',
  ready: 'pronto',
  executing: 'executando',
  completed: 'concluído',
  failed: 'falhou',
  cancelled: 'cancelado'
}[value] || value)

const riskLabel = value => ({
  low: 'baixo risco',
  medium: 'atenção',
  high: 'alto impacto'
}[value] || value)

const toolLabel = tool => ({
  inspect_context: 'Leitura do contexto verificado',
  navigate: 'Navegação local',
  build_graph: 'Fase 2',
  create_simulation: 'Fase 3',
  prepare_simulation: 'Fase 3',
  start_simulation: 'Fase 3',
  stop_simulation: 'Controle de execução',
  generate_report: 'Fase 4',
  ask_analysis: 'Fase 5',
  continue_analysis: 'Pipeline encadeado',
  run_full_analysis: 'Pipeline completo no servidor'
}[tool] || tool)

const handleShortcut = event => {
  if (event.altKey && event.key.toLowerCase() === 'h') {
    event.preventDefault()
    if (isOpen.value) closePanel()
    else openPanel()
  }
}

const handleOpenAiFriend = event => {
  const suggestedCommand = String(event?.detail?.command || '').trim()
  if (suggestedCommand && executionState.value !== 'executing') {
    command.value = suggestedCommand.slice(0, 4000)
  }
  openPanel()
}

onMounted(() => {
  window.addEventListener('keydown', handleShortcut)
  window.addEventListener('mirofish:open-ai-friend', handleOpenAiFriend)
  loadStatus()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleShortcut)
  window.removeEventListener('mirofish:open-ai-friend', handleOpenAiFriend)
  sessionToken.value = ''
})
</script>

<style scoped>
.helena-root {
  --helena-ink: #e8edf6;
  --helena-muted: #9aa8bd;
  --helena-panel: #0b1220;
  --helena-panel-soft: #111c2d;
  --helena-line: rgba(172, 190, 218, 0.16);
  --helena-gold: #d7a53a;
  --helena-mint: #49c98b;
  --helena-danger: #ef6a6a;
  position: fixed;
  right: 22px;
  bottom: 22px;
  z-index: 1400;
  font-family: var(--f-sans, "Geist"), system-ui, sans-serif;
}

.helena-launcher {
  position: relative;
  min-width: 188px;
  height: 58px;
  padding: 0 18px 0 14px;
  border: 1px solid rgba(215, 165, 58, 0.48);
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  background: linear-gradient(145deg, #111c2d, #0a111e);
  box-shadow: 0 18px 48px rgba(5, 10, 20, 0.32);
  cursor: pointer;
  overflow: hidden;
}

.helena-launcher:focus-visible,
.icon-button:focus-visible,
button:focus-visible,
textarea:focus-visible,
input:focus-visible,
summary:focus-visible {
  outline: 2px solid var(--helena-gold);
  outline-offset: 3px;
}

.helena-launcher svg {
  width: 23px;
  height: 23px;
  fill: none;
  stroke: var(--helena-gold);
  stroke-width: 1.7;
  stroke-linecap: round;
}

.launcher-orbit {
  position: absolute;
  left: 8px;
  width: 34px;
  height: 34px;
  border: 1px solid rgba(215, 165, 58, 0.25);
  border-radius: 50%;
}

.launcher-label {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}
.launcher-label strong {
  font: 700 12px/1 "JetBrains Mono", monospace;
  letter-spacing: 0.10em;
}
.launcher-label small {
  color: var(--helena-muted);
  font: 500 9px/1 var(--f-sans, "Geist"), sans-serif;
  letter-spacing: 0.04em;
}

.helena-panel {
  width: min(440px, calc(100vw - 32px));
  max-height: min(780px, calc(100vh - 44px));
  border: 1px solid rgba(215, 165, 58, 0.26);
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  color: var(--helena-ink);
  background:
    radial-gradient(circle at 90% 0, rgba(215, 165, 58, 0.11), transparent 32%),
    var(--helena-panel);
  box-shadow: 0 28px 90px rgba(3, 8, 18, 0.48);
  overflow: hidden;
  animation: panel-in 180ms ease-out;
}

@keyframes panel-in {
  from { opacity: 0; transform: translateY(12px) scale(0.98); }
}

.helena-header {
  min-height: 72px;
  padding: 14px 16px 12px;
  border-bottom: 1px solid var(--helena-line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.helena-identity,
.header-actions,
.workspace-heading,
.plan-header,
.progress-copy,
.composer-footer,
.plan-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.helena-identity {
  justify-content: flex-start;
}

.helena-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #151006;
  background: linear-gradient(145deg, #ebc76d, #b77d18);
  font: 800 17px/1 "JetBrains Mono", monospace;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--helena-gold);
  font: 700 9px/1.2 "JetBrains Mono", monospace;
  letter-spacing: 0.16em;
}

.helena-header h2,
.workspace-heading h3,
.plan-header h3,
.auth-card h3,
.empty-state h3 {
  margin: 0;
}

.helena-header h2 {
  font-size: 19px;
}

.availability {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--helena-muted);
  font-size: 11px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #77849a;
}

.is-online .status-dot { background: var(--helena-mint); box-shadow: 0 0 0 4px rgba(73, 201, 139, 0.1); }
.is-locked .status-dot { background: var(--helena-gold); }
.is-offline .status-dot { background: var(--helena-danger); }

.icon-button {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--helena-line);
  border-radius: 11px;
  display: grid;
  place-items: center;
  color: var(--helena-muted);
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.icon-button svg {
  width: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
}

.context-strip {
  min-height: 38px;
  padding: 7px 16px;
  border-bottom: 1px solid var(--helena-line);
  display: flex;
  align-items: center;
  gap: 9px;
  background: rgba(255, 255, 255, 0.018);
}

.phase-chip {
  padding: 4px 7px;
  border-radius: 6px;
  color: #f2d796;
  background: rgba(215, 165, 58, 0.1);
  font-size: 10px;
  white-space: nowrap;
}

.context-id {
  min-width: 0;
  flex: 1;
  color: var(--helena-muted);
  font: 500 10px/1.2 "JetBrains Mono", monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.next-step-strip {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: baseline;
  gap: 10px;
  padding: 9px 16px 10px;
  border-bottom: 1px solid var(--helena-line);
  background: rgba(215, 165, 58, 0.045);
}
.next-step-strip span {
  color: var(--helena-gold);
  font: 700 8px/1.2 "JetBrains Mono", monospace;
  letter-spacing: 0.12em;
}
.next-step-strip p {
  margin: 0;
  color: #b4c0d2;
  font-size: 10px;
  line-height: 1.45;
}

.text-button {
  padding: 5px 0;
  border: 0;
  color: #b9c7da;
  background: none;
  font-size: 11px;
  cursor: pointer;
}

.text-button:hover { color: #fff; }
.text-button.danger { color: #e98d8d; }

.helena-body {
  padding: 16px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: #36445a transparent;
}

.center-state,
.empty-state {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--helena-muted);
  text-align: center;
}

.empty-state p {
  max-width: 340px;
  margin: 0;
  line-height: 1.55;
  font-size: 13px;
}

.empty-icon {
  width: 44px;
  height: 44px;
  border: 1px solid rgba(239, 106, 106, 0.38);
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: var(--helena-danger);
  background: rgba(239, 106, 106, 0.08);
  font: 800 18px/1 monospace;
}

.auth-card {
  padding: 18px;
  border: 1px solid var(--helena-line);
  border-radius: 16px;
  display: grid;
  gap: 13px;
  background: rgba(255, 255, 255, 0.025);
}

.auth-card > div:nth-child(2) {
  text-align: center;
}

.auth-card p {
  margin: 6px 0 0;
  color: var(--helena-muted);
  font-size: 12px;
  line-height: 1.5;
}

.security-lock {
  width: 50px;
  height: 50px;
  margin: 0 auto;
  border-radius: 15px;
  display: grid;
  place-items: center;
  color: var(--helena-gold);
  background: rgba(215, 165, 58, 0.09);
}

.security-lock svg,
.approval-notice svg {
  width: 25px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
}

label {
  color: #cad4e3;
  font-size: 11px;
  font-weight: 650;
}

.input-row {
  display: flex;
  align-items: stretch;
}

input,
textarea {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid rgba(172, 190, 218, 0.22);
  color: var(--helena-ink);
  background: #080f1b;
  font: 500 13px/1.55 var(--f-sans, "Geist"), system-ui, sans-serif;
}

input {
  height: 44px;
  padding: 0 12px;
  border-radius: 11px 0 0 11px;
}

textarea {
  min-height: 108px;
  padding: 12px;
  border-radius: 12px;
  resize: vertical;
}

input::placeholder,
textarea::placeholder { color: #66758b; }

.reveal-button {
  padding: 0 12px;
  border: 1px solid rgba(172, 190, 218, 0.22);
  border-left: 0;
  border-radius: 0 11px 11px 0;
  color: #aebbd0;
  background: #101a29;
  font-size: 10px;
  cursor: pointer;
}

.primary-button,
.secondary-button {
  min-height: 44px;
  padding: 0 16px;
  border-radius: 11px;
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
}

.primary-button {
  border: 1px solid #d7a53a;
  color: #171106;
  background: linear-gradient(145deg, #edc96e, #c88c24);
  box-shadow: 0 10px 25px rgba(183, 125, 24, 0.18);
}

.primary-button.high-risk {
  border-color: #e5a951;
  background: linear-gradient(145deg, #f1be62, #cf792e);
}

.secondary-button {
  border: 1px solid var(--helena-line);
  color: #c3cede;
  background: rgba(255, 255, 255, 0.035);
}

button:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.command-workspace {
  display: grid;
  gap: 10px;
}

.workspace-heading h3,
.plan-header h3 {
  color: #f4f7fb;
  font-size: 14px;
}

.composer-footer {
  margin-top: -4px;
  color: #6f7f96;
  font-size: 9px;
}

.command-suggestions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}
.command-suggestions button {
  min-width: 0;
  padding: 9px;
  border: 1px solid rgba(172, 190, 218, 0.15);
  border-radius: 10px;
  color: #dbe3ef;
  background: rgba(255, 255, 255, 0.025);
  text-align: left;
  cursor: pointer;
  transition: 150ms ease;
}
.command-suggestions button:hover {
  border-color: rgba(215, 165, 58, 0.46);
  background: rgba(215, 165, 58, 0.07);
  transform: translateY(-1px);
}
.command-suggestions span {
  display: block;
  font-size: 9px;
  font-weight: 700;
  line-height: 1.25;
}
.command-suggestions small {
  display: block;
  margin-top: 4px;
  color: #72839b;
  font: 500 7px/1.3 "JetBrains Mono", monospace;
}

.plan-card {
  margin-top: 15px;
  padding: 15px;
  border: 1px solid rgba(215, 165, 58, 0.21);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(215, 165, 58, 0.055), rgba(255, 255, 255, 0.018));
}

.plan-header {
  align-items: flex-start;
}

.risk-badge,
.mutation-tag,
.read-tag {
  padding: 4px 7px;
  border-radius: 7px;
  font: 700 8px/1.2 "JetBrains Mono", monospace;
  letter-spacing: 0.04em;
  white-space: nowrap;
  text-transform: uppercase;
}

.risk-low,
.read-tag {
  color: #7fe0ad;
  background: rgba(73, 201, 139, 0.1);
}

.risk-medium {
  color: #f0cf7c;
  background: rgba(215, 165, 58, 0.11);
}

.risk-high,
.mutation-tag {
  color: #ffac91;
  background: rgba(239, 106, 106, 0.11);
}

.plan-rationale {
  margin: 10px 0 12px;
  color: var(--helena-muted);
  font-size: 11px;
  line-height: 1.5;
}

.action-list,
.activity-log ul,
.audit-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.action-list {
  display: grid;
  gap: 7px;
}

.action-list li {
  min-height: 48px;
  padding: 8px 9px;
  border: 1px solid var(--helena-line);
  border-radius: 10px;
  display: grid;
  grid-template-columns: 28px 1fr auto;
  align-items: center;
  gap: 9px;
  background: rgba(5, 11, 20, 0.45);
}

.action-index {
  color: var(--helena-gold);
  font: 700 10px/1 monospace;
}

.action-list strong,
.action-list li div span {
  display: block;
}

.action-list strong {
  color: #dfe6f0;
  font-size: 11px;
}

.action-list li div span {
  margin-top: 3px;
  color: #718096;
  font-size: 9px;
}

.execution-progress,
.activity-log,
.result-card,
.approval-notice {
  margin-top: 12px;
}

.progress-copy {
  color: #b4c0d2;
  font-size: 10px;
}

.progress-copy strong {
  color: var(--helena-gold);
  font-family: "JetBrains Mono", monospace;
}

.progress-track {
  height: 5px;
  margin-top: 7px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.07);
  overflow: hidden;
}

.progress-track span {
  height: 100%;
  display: block;
  border-radius: inherit;
  background: linear-gradient(90deg, #b97d19, #efcc73);
  transition: width 240ms ease;
}

.activity-log {
  padding: 10px;
  border-radius: 10px;
  background: rgba(3, 8, 15, 0.55);
}

.activity-log ul {
  display: grid;
  gap: 5px;
}

.activity-log li {
  display: grid;
  grid-template-columns: 54px 1fr;
  gap: 8px;
  color: #9eabbe;
  font-size: 9px;
}

.activity-log time {
  color: #65758c;
  font-family: "JetBrains Mono", monospace;
}

.result-card {
  padding: 11px;
  border: 1px solid rgba(73, 201, 139, 0.24);
  border-radius: 10px;
  color: #9ce2bc;
  background: rgba(73, 201, 139, 0.07);
}

.result-card.failed {
  border-color: rgba(239, 106, 106, 0.25);
  color: #f2a2a2;
  background: rgba(239, 106, 106, 0.07);
}

.result-card p {
  margin: 5px 0 0;
  color: #b8c4d4;
  font-size: 10px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.approval-notice {
  padding: 10px;
  border: 1px solid rgba(215, 165, 58, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--helena-gold);
  background: rgba(215, 165, 58, 0.06);
}

.approval-notice p {
  margin: 0;
  color: #b8c4d5;
  font-size: 10px;
  line-height: 1.45;
}

.plan-actions {
  margin-top: 13px;
  justify-content: flex-start;
}

.plan-actions .primary-button {
  flex: 1;
}

.audit-section {
  margin-top: 13px;
  border-top: 1px solid var(--helena-line);
}

.audit-section summary {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #aab7ca;
  font-size: 10px;
  cursor: pointer;
  list-style: none;
}

.audit-section summary::-webkit-details-marker { display: none; }
.audit-section summary span:last-child { color: #66758a; }

.audit-list {
  display: grid;
  gap: 6px;
}

.audit-list li {
  padding: 8px 9px;
  border-radius: 9px;
  display: grid;
  grid-template-columns: 8px 1fr;
  align-items: center;
  gap: 9px;
  background: rgba(255, 255, 255, 0.025);
}

.audit-list strong,
.audit-list span {
  display: block;
}

.audit-list strong {
  color: #c8d2df;
  font-size: 10px;
}

.audit-list div span {
  margin-top: 3px;
  color: #65748a;
  font-size: 9px;
}

.audit-status {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #7e8ca0;
}

.status-completed { background: var(--helena-mint); }
.status-failed { background: var(--helena-danger); }
.status-executing { background: var(--helena-gold); }
.status-cancelled { background: #8592a5; }

.audit-loading,
.audit-empty {
  margin: 5px 0;
  color: #718096;
  font-size: 10px;
}

.error-message {
  margin: 0;
  color: #f09b9b;
  font-size: 11px;
  line-height: 1.45;
}

.sticky-error {
  margin-top: 10px;
  padding: 9px;
  border-radius: 9px;
  background: rgba(239, 106, 106, 0.07);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(215, 165, 58, 0.18);
  border-top-color: var(--helena-gold);
  border-radius: 50%;
  display: inline-block;
  animation: spin 700ms linear infinite;
}

.spinner.small {
  width: 13px;
  height: 13px;
  margin-right: 7px;
  vertical-align: -2px;
}

@keyframes spin { to { transform: rotate(360deg); } }

.sr-only,
.sr-only:not(:focus):not(:active) {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

code {
  color: #efd283;
  font-family: "JetBrains Mono", monospace;
}

@media (max-width: 640px) {
  .helena-root {
    right: 12px;
    bottom: max(12px, env(safe-area-inset-bottom));
  }

  .helena-launcher {
    min-width: 52px;
    width: 52px;
    padding: 0;
    justify-content: center;
    border-radius: 16px;
  }

  .launcher-label { display: none; }
  .launcher-orbit { left: 8px; }

  .helena-panel {
    position: fixed;
    right: 8px;
    bottom: max(8px, env(safe-area-inset-bottom));
    left: 8px;
    width: auto;
    max-height: calc(100dvh - 16px - env(safe-area-inset-bottom));
    border-radius: 20px;
  }

  .helena-header {
    min-height: 64px;
  }

  .availability {
    width: 8px;
    overflow: hidden;
  }

  .status-dot { flex: 0 0 7px; }

  .icon-button {
    width: 44px;
    height: 44px;
  }

  .text-button {
    min-height: 44px;
    padding: 0 4px;
  }

  .helena-body {
    padding: 13px;
  }

  .action-list li {
    grid-template-columns: 24px 1fr;
  }

  .mutation-tag,
  .read-tag {
    grid-column: 2;
    justify-self: start;
  }

  .plan-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .plan-actions .primary-button,
  .plan-actions .secondary-button {
    width: 100%;
  }

  .next-step-strip {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .command-suggestions {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .helena-panel,
  .spinner,
  .progress-track span {
    animation: none;
    transition: none;
  }
}
</style>
