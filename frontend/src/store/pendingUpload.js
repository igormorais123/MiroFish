/**
 * Armazenamento temporario de arquivos e requisitos pendentes de upload
 * Usado para navegar imediatamente apos clicar em iniciar na pagina inicial, chamando a API na pagina Process
 */
import { reactive } from 'vue'

const STORAGE_KEY = 'mirofish_pending_requirement'

const state = reactive({
  files: [],
  simulationRequirement: '',
  isPending: false
})

export function setPendingUpload(files, requirement) {
  state.files = files
  state.simulationRequirement = requirement
  state.isPending = true
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.setItem(STORAGE_KEY, requirement || '')
  }
}

export function getPendingUpload() {
  const storedRequirement = typeof sessionStorage !== 'undefined'
    ? sessionStorage.getItem(STORAGE_KEY) || ''
    : ''
  const simulationRequirement = state.simulationRequirement || storedRequirement
  return {
    files: state.files,
    simulationRequirement,
    isPending: state.isPending || simulationRequirement.trim() !== ''
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.isPending = false
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.removeItem(STORAGE_KEY)
  }
}

export default state
