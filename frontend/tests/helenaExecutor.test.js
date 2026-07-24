import test from 'node:test'
import assert from 'node:assert/strict'

import {
  executeHelenaAction,
  executeHelenaPlan,
  resolveRuntimeParams,
  waitForPreparation,
  waitForTask
} from '../src/services/helenaExecutor.js'

const baseDependencies = overrides => ({
  buildGraph: async () => ({ data: {} }),
  getTaskStatus: async () => ({ data: { status: 'completed', progress: 100 } }),
  createSimulation: async () => ({ data: { simulation_id: 'sim_created', status: 'created' } }),
  getRunStatus: async () => ({ data: { runner_status: 'completed', progress: 100 } }),
  getSimulation: async () => ({ data: { status: 'completed' } }),
  prepareSimulation: async () => ({ data: { status: 'ready' } }),
  startSimulation: async () => ({ data: { status: 'running' } }),
  stopSimulation: async () => ({ data: { status: 'stopped' } }),
  chatWithReport: async () => ({ data: { response: 'ok' } }),
  generateReport: async () => ({ data: { report_id: 'report_created', status: 'completed' } }),
  runInternalPreset: async () => ({ data: { task_id: null } }),
  navigate: async () => {},
  sleep: async () => {},
  ...overrides
})

test('resolveRuntimeParams substitui apenas referencias conhecidas', () => {
  const result = resolveRuntimeParams(
    {
      project_id: '$project_id',
      simulation_id: '$simulation_id',
      literal: 'preservado'
    },
    { project_id: 'proj_1', simulation_id: 'sim_1' }
  )
  assert.deepEqual(result, {
    project_id: 'proj_1',
    simulation_id: 'sim_1',
    literal: 'preservado'
  })
})

test('create_simulation usa o adapter existente e atualiza o runtime', async () => {
  const runtime = { project_id: 'proj_1', graph_id: 'graph_1' }
  let received
  const dependencies = baseDependencies({
    createSimulation: async payload => {
      received = payload
      return { data: { simulation_id: 'sim_2', status: 'created' } }
    }
  })

  const result = await executeHelenaAction(
    {
      tool: 'create_simulation',
      params: { project_id: 'proj_1', graph_id: 'graph_1' }
    },
    runtime,
    dependencies
  )

  assert.deepEqual(received, { project_id: 'proj_1', graph_id: 'graph_1' })
  assert.equal(result.simulation_id, 'sim_2')
  assert.equal(runtime.simulation_id, 'sim_2')
})

test('waitForTask acompanha progresso ate conclusao', async () => {
  const states = [
    { status: 'processing', progress: 40, message: 'metade' },
    { status: 'completed', progress: 100, result: { report_id: 'report_1' } }
  ]
  const progress = []
  const result = await waitForTask(
    'task_1',
    baseDependencies({
      getTaskStatus: async () => ({ data: states.shift() })
    }),
    (message, value) => progress.push([message, value]),
    1000
  )
  assert.equal(result.result.report_id, 'report_1')
  assert.equal(progress.length, 2)
})

test('waitForTask propaga falha sem continuar o plano', async () => {
  await assert.rejects(
    waitForTask(
      'task_1',
      baseDependencies({
        getTaskStatus: async () => ({ data: { status: 'failed', error: 'gate bloqueou' } })
      }),
      () => {},
      1000
    ),
    /gate bloqueou/
  )
})

test('continue_analysis em simulacao rodando apenas aguarda e gera relatorio', async () => {
  let starts = 0
  let reports = 0
  const runtime = {
    project_id: 'proj_1',
    graph_id: 'graph_1',
    simulation_id: 'sim_1'
  }
  const dependencies = baseDependencies({
    getSimulation: async () => ({ data: { status: 'running' } }),
    startSimulation: async () => {
      starts += 1
      return { data: { status: 'running' } }
    },
    generateReport: async () => {
      reports += 1
      return { data: { report_id: 'report_1', status: 'completed' } }
    }
  })

  await executeHelenaAction(
    {
      tool: 'continue_analysis',
      params: {
        project_id: 'proj_1',
        graph_id: 'graph_1',
        simulation_id: 'sim_1'
      }
    },
    runtime,
    dependencies
  )

  assert.equal(starts, 0)
  assert.equal(reports, 1)
  assert.equal(runtime.report_id, 'report_1')
})

test('waitForPreparation acompanha preparacao existente sem iniciar outra', async () => {
  const states = [
    { status: 'preparing' },
    { status: 'ready', profiles_count: 5 }
  ]
  const result = await waitForPreparation(
    'sim_1',
    baseDependencies({
      getSimulation: async () => ({ data: states.shift() })
    }),
    () => {},
    1000
  )
  assert.equal(result.status, 'ready')
  assert.equal(result.profiles_count, 5)
})

test('continue_analysis nao duplica preparacao nem relatorio concluido', async () => {
  let prepares = 0
  let reports = 0
  const runtimeWithPreparation = {
    project_id: 'proj_1',
    graph_id: 'graph_1',
    simulation_id: 'sim_1'
  }
  const preparationStates = [
    { status: 'preparing' },
    { status: 'ready' }
  ]
  const dependencies = baseDependencies({
    getSimulation: async () => ({ data: preparationStates.shift() || { status: 'ready' } }),
    prepareSimulation: async () => {
      prepares += 1
      return { data: { status: 'ready' } }
    },
    generateReport: async () => {
      reports += 1
      return { data: { report_id: 'report_1', status: 'completed' } }
    }
  })

  await executeHelenaAction(
    {
      tool: 'continue_analysis',
      params: {
        project_id: 'proj_1',
        graph_id: 'graph_1',
        simulation_id: 'sim_1'
      }
    },
    runtimeWithPreparation,
    dependencies
  )
  assert.equal(prepares, 0)
  assert.equal(reports, 1)

  reports = 0
  const completedRuntime = {
    project_id: 'proj_1',
    graph_id: 'graph_1',
    simulation_id: 'sim_1',
    report_id: 'report_existing',
    report_status: 'completed'
  }
  const result = await executeHelenaAction(
    {
      tool: 'continue_analysis',
      params: {
        project_id: 'proj_1',
        graph_id: 'graph_1',
        simulation_id: 'sim_1'
      }
    },
    completedRuntime,
    dependencies
  )
  assert.equal(reports, 0)
  assert.equal(result.report.reused, true)
})

test('executeHelenaPlan preserva a ordem e bloqueia ferramenta desconhecida', async () => {
  const calls = []
  const dependencies = baseDependencies({
    navigate: async target => calls.push(target.name)
  })
  const result = await executeHelenaPlan(
    [
      { tool: 'inspect_context', params: {}, description: 'Ler' },
      { tool: 'navigate', params: { phase: 'Home' }, description: 'Navegar' }
    ],
    {},
    dependencies
  )
  assert.deepEqual(calls, ['Home'])
  assert.deepEqual(result.receipts.map(item => item.tool), ['inspect_context', 'navigate'])

  await assert.rejects(
    executeHelenaAction({ tool: 'shell', params: {} }, {}, dependencies),
    /nao permitida/
  )
})
