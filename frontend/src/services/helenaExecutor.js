const DEFAULT_TASK_TIMEOUT = 30 * 60 * 1000
const DEFAULT_SIMULATION_TIMEOUT = 2 * 60 * 60 * 1000
const TERMINAL_TASK = new Set(['completed', 'failed'])
const TERMINAL_SIMULATION = new Set(['completed', 'failed', 'stopped'])

const unwrapData = response => response?.data || response || {}

export const resolveRuntimeParams = (params = {}, runtime = {}) => {
  const result = {}
  for (const [key, value] of Object.entries(params || {})) {
    if (value === '$project_id') result[key] = runtime.project_id
    else if (value === '$graph_id') result[key] = runtime.graph_id
    else if (value === '$simulation_id') result[key] = runtime.simulation_id
    else if (value === '$report_id') result[key] = runtime.report_id
    else result[key] = value
  }
  return result
}

const routeForPhase = (phase, runtime) => {
  const routes = {
    Home: { name: 'Home' },
    Process: { name: 'Process', params: { projectId: runtime.project_id } },
    Simulation: { name: 'Simulation', params: { simulationId: runtime.simulation_id } },
    SimulationRun: { name: 'SimulationRun', params: { simulationId: runtime.simulation_id } },
    Report: { name: 'Report', params: { reportId: runtime.report_id } },
    Interaction: { name: 'Interaction', params: { reportId: runtime.report_id } }
  }
  return routes[phase] || routes.Home
}

export const waitForTask = async (
  taskId,
  dependencies,
  onProgress = () => {},
  timeoutMs = DEFAULT_TASK_TIMEOUT
) => {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeoutMs) {
    const response = await dependencies.getTaskStatus(taskId)
    const task = unwrapData(response)
    onProgress(task.message || `Tarefa ${task.status || 'em andamento'}`, task.progress)
    if (TERMINAL_TASK.has(task.status)) {
      if (task.status === 'failed') {
        throw new Error(task.error || task.message || 'A tarefa falhou')
      }
      return task
    }
    await dependencies.sleep(2000)
  }
  throw new Error('A tarefa excedeu o tempo limite do console Helena')
}

export const waitForSimulation = async (
  simulationId,
  dependencies,
  onProgress = () => {},
  timeoutMs = DEFAULT_SIMULATION_TIMEOUT
) => {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeoutMs) {
    const response = await dependencies.getRunStatus(simulationId)
    const data = unwrapData(response)
    const status = data.runner_status || data.status || data.run_status
    const progress = data.progress ?? data.progress_percentage
    onProgress(data.message || `Simulacao ${status || 'em andamento'}`, progress)
    if (TERMINAL_SIMULATION.has(status)) {
      if (status === 'failed') {
        throw new Error(data.error || data.message || 'A simulacao falhou')
      }
      return data
    }
    await dependencies.sleep(5000)
  }
  throw new Error('A simulacao excedeu o tempo limite do console Helena')
}

export const waitForPreparation = async (
  simulationId,
  dependencies,
  onProgress = () => {},
  timeoutMs = DEFAULT_TASK_TIMEOUT
) => {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeoutMs) {
    const response = await dependencies.getSimulation(simulationId)
    const data = unwrapData(response)
    const status = data.status
    onProgress(
      data.message || `Preparacao ${status || 'em andamento'}`,
      status === 'ready' ? 100 : null
    )
    if (status === 'ready') return data
    if (status === 'failed') {
      throw new Error(data.error || 'A preparacao da simulacao falhou')
    }
    if (status !== 'preparing') {
      throw new Error(`Preparacao interrompida no estado ${status || 'desconhecido'}`)
    }
    await dependencies.sleep(2000)
  }
  throw new Error('A preparacao excedeu o tempo limite do console Helena')
}

const executeBuildGraph = async (params, runtime, dependencies, onProgress) => {
  const response = await dependencies.buildGraph({ project_id: params.project_id })
  const data = unwrapData(response)
  if (data.task_id) {
    const task = await waitForTask(data.task_id, dependencies, onProgress)
    runtime.graph_id = task.result?.graph_id || runtime.graph_id
    return { ...data, task }
  }
  return data
}

const executeCreateSimulation = async (params, runtime, dependencies) => {
  const response = await dependencies.createSimulation({
    project_id: params.project_id,
    graph_id: params.graph_id
  })
  const data = unwrapData(response)
  runtime.simulation_id = data.simulation_id
  runtime.simulation_status = data.status
  return data
}

const executePrepareSimulation = async (params, runtime, dependencies, onProgress) => {
  const response = await dependencies.prepareSimulation({
    simulation_id: params.simulation_id,
    use_llm_for_profiles: true,
    parallel_profile_count: 5,
    force_regenerate: false
  })
  const data = unwrapData(response)
  if (data.task_id) {
    const task = await waitForTask(data.task_id, dependencies, onProgress)
    runtime.simulation_status = 'ready'
    return { ...data, task }
  }
  runtime.simulation_status = data.status || runtime.simulation_status
  return data
}

const executeStartSimulation = async (params, runtime, dependencies) => {
  const response = await dependencies.startSimulation({
    simulation_id: params.simulation_id,
    platform: params.platform || 'parallel',
    max_rounds: params.max_rounds || 50,
    enable_graph_memory_update: false
  })
  const data = unwrapData(response)
  runtime.simulation_status = data.status || 'running'
  return data
}

const executeGenerateReport = async (params, runtime, dependencies, onProgress) => {
  const response = await dependencies.generateReport({
    simulation_id: params.simulation_id,
    force_regenerate: false
  })
  const data = unwrapData(response)
  runtime.report_id = data.report_id || runtime.report_id
  if (data.task_id) {
    const task = await waitForTask(data.task_id, dependencies, onProgress)
    runtime.report_id = task.result?.report_id || runtime.report_id
    return { ...data, task }
  }
  return data
}

const executeContinueAnalysis = async (params, runtime, dependencies, onProgress) => {
  runtime.project_id = params.project_id
  runtime.graph_id = params.graph_id
  runtime.simulation_id = params.simulation_id || runtime.simulation_id

  const receipt = {}
  if (runtime.report_id && runtime.report_status === 'completed') {
    onProgress('Relatorio existente reutilizado', 100)
    receipt.report = {
      report_id: runtime.report_id,
      status: 'completed',
      reused: true
    }
    return receipt
  }

  if (!runtime.simulation_id) {
    onProgress('Criando simulacao', 5)
    receipt.create = await executeCreateSimulation(params, runtime, dependencies)
  }

  const current = unwrapData(await dependencies.getSimulation(runtime.simulation_id))
  runtime.simulation_status = current.status

  if (['created', 'failed'].includes(runtime.simulation_status)) {
    onProgress('Preparando perfis e configuracao', 15)
    receipt.prepare = await executePrepareSimulation(
      { simulation_id: runtime.simulation_id },
      runtime,
      dependencies,
      onProgress
    )
  } else if (runtime.simulation_status === 'preparing') {
    onProgress('Acompanhando preparacao ja iniciada', 15)
    receipt.prepare = await waitForPreparation(
      runtime.simulation_id,
      dependencies,
      onProgress
    )
    runtime.simulation_status = 'ready'
  }

  if (runtime.simulation_status === 'running') {
    receipt.simulation = await waitForSimulation(
      runtime.simulation_id,
      dependencies,
      onProgress
    )
    runtime.simulation_status = receipt.simulation.runner_status || receipt.simulation.status
  } else if (!['completed', 'stopped'].includes(runtime.simulation_status)) {
    onProgress('Iniciando simulacao', 45)
    receipt.start = await executeStartSimulation(
      { simulation_id: runtime.simulation_id, platform: 'parallel', max_rounds: 50 },
      runtime,
      dependencies
    )
    receipt.simulation = await waitForSimulation(
      runtime.simulation_id,
      dependencies,
      onProgress
    )
    runtime.simulation_status = receipt.simulation.runner_status || receipt.simulation.status
  }

  onProgress('Gerando relatorio', 85)
  receipt.report = await executeGenerateReport(
    { simulation_id: runtime.simulation_id },
    runtime,
    dependencies,
    onProgress
  )
  onProgress('Analise concluida', 100)
  return receipt
}

export const executeHelenaAction = async (
  action,
  runtime,
  dependencies,
  onProgress = () => {}
) => {
  const params = resolveRuntimeParams(action.params, runtime)
  switch (action.tool) {
    case 'inspect_context':
      return { context: { ...runtime } }
    case 'navigate':
      await dependencies.navigate(routeForPhase(params.phase, runtime))
      return { navigated_to: params.phase }
    case 'build_graph':
      return executeBuildGraph(params, runtime, dependencies, onProgress)
    case 'create_simulation':
      return executeCreateSimulation(params, runtime, dependencies)
    case 'prepare_simulation':
      return executePrepareSimulation(params, runtime, dependencies, onProgress)
    case 'start_simulation':
      return executeStartSimulation(params, runtime, dependencies)
    case 'stop_simulation':
      return unwrapData(await dependencies.stopSimulation({
        simulation_id: params.simulation_id
      }))
    case 'generate_report':
      return executeGenerateReport(params, runtime, dependencies, onProgress)
    case 'ask_analysis':
      return unwrapData(await dependencies.chatWithReport({
        simulation_id: params.simulation_id,
        message: params.message,
        chat_history: [],
        tool_mode: 'auto'
      }))
    case 'continue_analysis':
      return executeContinueAnalysis(params, runtime, dependencies, onProgress)
    case 'run_full_analysis': {
      const data = unwrapData(await dependencies.runInternalPreset(params))
      if (data.task_id) {
        const task = await waitForTask(data.task_id, dependencies, onProgress, DEFAULT_SIMULATION_TIMEOUT)
        Object.assign(runtime, task.result || {})
        return { ...data, task }
      }
      return data
    }
    default:
      throw new Error(`Ferramenta Helena nao permitida: ${action.tool}`)
  }
}

export const executeHelenaPlan = async (
  actions,
  initialRuntime,
  dependencies,
  onProgress = () => {}
) => {
  const runtime = { ...initialRuntime }
  const receipts = []
  for (const action of actions) {
    onProgress(action.description || action.tool)
    const result = await executeHelenaAction(
      action,
      runtime,
      dependencies,
      onProgress
    )
    receipts.push({ tool: action.tool, result })
  }
  return { runtime, receipts }
}
