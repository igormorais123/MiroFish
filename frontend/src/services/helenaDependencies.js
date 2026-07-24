import { buildGraph, getTaskStatus } from '../api/graph'
import {
  createSimulation,
  getRunStatus,
  getSimulation,
  prepareSimulation,
  startSimulation,
  stopSimulation
} from '../api/simulation'
import { chatWithReport, generateReport } from '../api/report'
import { runInternalPreset } from '../api/helena'

const sleep = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

export const createDefaultHelenaDependencies = ({ router, token }) => ({
  buildGraph,
  getTaskStatus,
  createSimulation,
  getRunStatus,
  getSimulation,
  prepareSimulation,
  startSimulation,
  stopSimulation,
  chatWithReport,
  generateReport,
  runInternalPreset: payload => runInternalPreset(token, payload),
  navigate: target => router.push(target),
  sleep
})
