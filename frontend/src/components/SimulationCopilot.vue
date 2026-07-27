<template>
  <div class="copilot">
    <div class="copilot-header">
      <div class="copilot-title">
        <span class="pulse-dot" :class="statusClass"></span>
        COPILOTO OPERACIONAL
      </div>
      <span class="copilot-rate" v-if="activity.actions_per_minute">
        {{ activity.actions_per_minute }} ações/min
      </span>
    </div>

    <!-- Leitura corrente: determinística, sem custo de token.
         Com alerta ativo o bloco de alertas já comunica o estado; repetir a
         headline seria a mesma frase duas vezes seguidas. -->
    <p class="copilot-headline" v-if="!alerts.length">
      {{ pulse.headline || 'Aguardando dados da execução...' }}
    </p>

    <div class="copilot-metrics" v-if="activity.actions_total">
      <div class="metric">
        <span class="metric-label">EVENTOS</span>
        <span class="metric-value mono">{{ activity.actions_total }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">AGENTES ATIVOS</span>
        <span class="metric-value mono">{{ activity.distinct_agents_in_window || 0 }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">ÚLTIMA AÇÃO</span>
        <span class="metric-value mono">{{ lastActionText }}</span>
      </div>
      <div class="metric" v-if="activity.failures_in_window">
        <span class="metric-label">FALHAS</span>
        <span class="metric-value mono warn">{{ activity.failures_in_window }}</span>
      </div>
    </div>

    <div class="copilot-alerts" v-if="alerts.length">
      <div
        v-for="alert in alerts"
        :key="alert.code"
        class="alert"
        :class="`alert-${alert.severity}`"
      >
        {{ alert.message }}
      </div>
    </div>

    <div class="action-mix" v-if="actionMix.length">
      <div v-for="item in actionMix" :key="item.type" class="mix-row">
        <span class="mix-label">{{ item.type }}</span>
        <span class="mix-bar"><span class="mix-fill" :style="{ width: item.percent + '%' }"></span></span>
        <span class="mix-count mono">{{ item.count }}</span>
      </div>
    </div>

    <!-- Consulta sob demanda: só aqui o modelo é chamado -->
    <div class="copilot-chat">
      <div class="chat-log" ref="chatLog" v-if="conversation.length">
        <div
          v-for="(turn, index) in conversation"
          :key="index"
          class="chat-turn"
          :class="`turn-${turn.role}`"
        >
          <span class="turn-role">{{ turn.role === 'user' ? 'VOCÊ' : 'COPILOTO' }}</span>
          <p class="turn-content">{{ turn.content }}</p>
        </div>
      </div>

      <div class="chat-suggestions" v-if="!conversation.length">
        <button
          v-for="suggestion in suggestions"
          :key="suggestion"
          class="suggestion"
          @click="submitQuestion(suggestion)"
          :disabled="isAsking"
        >{{ suggestion }}</button>
      </div>

      <form class="chat-input" @submit.prevent="submitQuestion()">
        <input
          v-model="question"
          type="text"
          placeholder="Pergunte sobre a execução em andamento..."
          :disabled="isAsking"
        />
        <button type="submit" :disabled="isAsking || !question.trim()">
          {{ isAsking ? '...' : 'ENVIAR' }}
        </button>
      </form>

      <p class="chat-error" v-if="askError">{{ askError }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { askCopilot, getCopilotPulse } from '../api/simulation'

const props = defineProps({
  simulationId: { type: String, required: true },
  // Enquanto a run está viva o pulso se atualiza sozinho.
  active: { type: Boolean, default: false }
})

const pulse = ref({})
const conversation = ref([])
const question = ref('')
const isAsking = ref(false)
const askError = ref(null)
const chatLog = ref(null)

let pulseTimer = null

const suggestions = [
  'O que está acontecendo agora?',
  'O ritmo está normal?',
  'Vale a pena continuar rodando?'
]

const activity = computed(() => pulse.value.activity || {})
const alerts = computed(() => pulse.value.alerts || [])

const statusClass = computed(() => {
  if (alerts.value.some(a => a.severity === 'critical')) return 'critical'
  if (alerts.value.length) return 'warning'
  return pulse.value.runner_status === 'running' ? 'running' : 'idle'
})

const lastActionText = computed(() => {
  const seconds = activity.value.seconds_since_last_action
  if (seconds === null || seconds === undefined) return '—'
  if (seconds < 60) return `${seconds}s`
  return `${Math.floor(seconds / 60)}min`
})

// Distribuição relativa dentro da janela observada.
const actionMix = computed(() => {
  const byType = activity.value.by_action_type || {}
  const total = Object.values(byType).reduce((sum, count) => sum + count, 0)
  if (!total) return []

  return Object.entries(byType)
    .map(([type, count]) => ({ type, count, percent: Math.round((count / total) * 100) }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)
})

const fetchPulse = async () => {
  if (!props.simulationId) return
  try {
    const res = await getCopilotPulse(props.simulationId)
    if (res.success && res.data) pulse.value = res.data
  } catch (err) {
    console.warn('Falha ao obter pulso do copiloto:', err)
  }
}

const submitQuestion = async (preset = null) => {
  const text = (preset || question.value).trim()
  if (!text || isAsking.value) return

  askError.value = null
  isAsking.value = true
  question.value = ''
  conversation.value.push({ role: 'user', content: text })
  await scrollChatToEnd()

  try {
    const res = await askCopilot(props.simulationId, {
      question: text,
      chat_history: conversation.value.slice(-7, -1)
    })

    if (res.success && res.data) {
      conversation.value.push({ role: 'assistant', content: res.data.response })
      // A resposta traz o pulso do instante da pergunta: aproveita e atualiza.
      if (res.data.pulse) pulse.value = res.data.pulse
    } else {
      askError.value = res.error || 'Não foi possível responder agora.'
    }
  } catch (err) {
    askError.value = err.message || 'Falha na consulta ao copiloto.'
  } finally {
    isAsking.value = false
    await scrollChatToEnd()
  }
}

const scrollChatToEnd = async () => {
  await nextTick()
  if (chatLog.value) chatLog.value.scrollTop = chatLog.value.scrollHeight
}

const startPulsePolling = () => {
  stopPulsePolling()
  fetchPulse()
  pulseTimer = setInterval(fetchPulse, 5000)
}

const stopPulsePolling = () => {
  if (pulseTimer) {
    clearInterval(pulseTimer)
    pulseTimer = null
  }
}

watch(() => props.active, (isActive) => {
  if (isActive) startPulsePolling()
  else {
    stopPulsePolling()
    fetchPulse() // leitura final do estado parado
  }
})

onMounted(() => {
  if (props.active) startPulsePolling()
  else fetchPulse()
})

onUnmounted(stopPulsePolling)
</script>

<style scoped>
.copilot {
  border: 1px solid rgba(15, 39, 71, 0.12);
  border-radius: 6px;
  background: #fffdf8;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.copilot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copilot-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 0.08em;
  font-weight: 700;
  color: #0f2747;
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #b8b8b8;
  flex-shrink: 0;
}

.pulse-dot.running {
  background: #2e7d32;
  animation: copilot-pulse 2s ease-in-out infinite;
}

.pulse-dot.warning { background: #c9952a; }
.pulse-dot.critical {
  background: #c0392b;
  animation: copilot-pulse 1s ease-in-out infinite;
}

@keyframes copilot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .pulse-dot.running,
  .pulse-dot.critical { animation: none; }
}

.copilot-rate {
  font-size: 10px;
  color: #8a8a8a;
}

.copilot-headline {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #2c2c2c;
}

.copilot-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-label {
  font-size: 9px;
  letter-spacing: 0.06em;
  color: #8a8a8a;
}

.metric-value {
  font-size: 15px;
  font-weight: 600;
  color: #0f2747;
}

.metric-value.warn { color: #c0392b; }

.mono {
  font-family: 'SF Mono', 'Consolas', monospace;
}

.copilot-alerts {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alert {
  font-size: 12px;
  line-height: 1.45;
  padding: 8px 10px;
  border-radius: 4px;
  border-left: 3px solid;
}

.alert-critical {
  background: rgba(192, 57, 43, 0.07);
  border-color: #c0392b;
  color: #8e2b21;
}

.alert-warning {
  background: rgba(201, 149, 42, 0.09);
  border-color: #c9952a;
  color: #8a6518;
}

.alert-info {
  background: rgba(15, 39, 71, 0.05);
  border-color: #0f2747;
  color: #35404f;
}

.action-mix {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mix-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
}

.mix-label {
  width: 120px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mix-bar {
  flex: 1;
  height: 4px;
  background: rgba(15, 39, 71, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.mix-fill {
  display: block;
  height: 100%;
  background: #c9952a;
}

.mix-count {
  width: 34px;
  text-align: right;
  color: #8a8a8a;
}

.copilot-chat {
  border-top: 1px solid rgba(15, 39, 71, 0.08);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-log {
  max-height: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-turn {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.turn-role {
  font-size: 9px;
  letter-spacing: 0.06em;
  color: #8a8a8a;
}

.turn-content {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: #2c2c2c;
  white-space: pre-wrap;
}

.turn-user .turn-content { color: #0f2747; font-weight: 500; }

.chat-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.suggestion {
  font-size: 11px;
  padding: 5px 10px;
  border: 1px solid rgba(15, 39, 71, 0.16);
  border-radius: 12px;
  background: transparent;
  color: #35404f;
  cursor: pointer;
}

.suggestion:hover:not(:disabled) {
  border-color: #c9952a;
  color: #0f2747;
}

.suggestion:disabled { opacity: 0.5; cursor: default; }

.chat-input {
  display: flex;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  font-size: 12px;
  padding: 8px 10px;
  border: 1px solid rgba(15, 39, 71, 0.16);
  border-radius: 4px;
  background: #fff;
  color: #2c2c2c;
}

.chat-input input:focus {
  outline: none;
  border-color: #c9952a;
}

.chat-input button {
  font-size: 11px;
  letter-spacing: 0.05em;
  font-weight: 600;
  padding: 8px 14px;
  border: none;
  border-radius: 4px;
  background: #0f2747;
  color: #fff;
  cursor: pointer;
}

.chat-input button:disabled { opacity: 0.45; cursor: default; }

.chat-error {
  margin: 0;
  font-size: 11px;
  color: #c0392b;
}
</style>
