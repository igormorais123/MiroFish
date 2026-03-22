import axios from 'axios'

// Criar instancia axios
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 300000, // Timeout de 5 minutos (geracao de ontologia pode demorar)
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptador de requisicao
service.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('Erro na requisicao:', error)
    return Promise.reject(error)
  }
)

// Interceptador de resposta (mecanismo de retry com tolerancia a falhas)
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // Se o codigo de status retornado nao e success, lancar erro
    if (!res.success && res.success !== undefined) {
      console.error('Erro da API:', res.error || res.message || 'Erro desconhecido')
      return Promise.reject(new Error(res.error || res.message || 'Error'))
    }
    
    return res
  },
  error => {
    console.error('Erro na resposta:', error)
    
    // Tratar timeout
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Tempo limite da requisicao')
    }
    
    // Tratar erro de rede
    if (error.message === 'Network Error') {
      console.error('Erro de rede - verifique sua conexao')
    }
    
    return Promise.reject(error)
  }
)

// Funcao de requisicao com retry
export const requestWithRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      
      console.warn(`Requisicao falhou, tentando novamente (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
}

export default service
