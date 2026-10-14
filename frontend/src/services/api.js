import axios from 'axios'

const BASE = '/api'

// Axios instance pointed at Flask backend (proxied via Vite)
const api = axios.create({
  baseURL: BASE,
  timeout: 5000,
})

/**
 * Fetch the latest live data from the backend.
 * Returns: { logs, stats }
 *   logs  → array of { time, src, dst, attack, action }
 *   stats → { total, attacks, benign, blocked }
 */
export async function fetchLiveData() {
  const { data } = await api.get('/live-data')
  return data
}

/**
 * Fetch log history (last N entries).
 */
export async function fetchLogs(limit = 50) {
  const { data } = await api.get(`/logs?limit=${limit}`)
  return data
}

export default api
