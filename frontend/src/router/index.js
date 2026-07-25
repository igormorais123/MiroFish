import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

// Home entra no bundle inicial (e a primeira tela). As demais views carregam sob
// demanda: o relatorio e a interacao arrastam mermaid e d3, que nao precisam
// estar no caminho critico de quem so abriu a home.
const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: () => import('../views/MainView.vue'),
    props: true
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: () => import('../views/SimulationView.vue'),
    props: true
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: () => import('../views/SimulationRunView.vue'),
    props: true
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: () => import('../views/ReportView.vue'),
    props: true
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: () => import('../views/InteractionView.vue'),
    props: true
  }
]

// Detecta subpath automaticamente
const base = window.location.pathname.startsWith('/mirofish') ? '/mirofish/' : '/'

const router = createRouter({
  history: createWebHistory(base),
  routes
})

export default router
