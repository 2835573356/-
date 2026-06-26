import { ref } from 'vue'
import { showToast } from './useToast'

/**
 * WebSocket 客户端 composable — 对应后端 /api/v1/ws/dashboard
 *
 * 后端推送消息类型:
 *  - connected     → 连接确认
 *  - heartbeat     → 心跳
 *  - health_update → 健康度变化
 *  - new_alert     → 新告警
 *  - data_refresh  → 数据已刷新
 */
export function useWebSocket() {
  const ws = ref(null)
  const connected = ref(false)
  const lastMessage = ref(null)
  const reconnectTimer = ref(null)
  const maxReconnectDelay = 30000
  const baseReconnectDelay = 2000
  let reconnectAttempts = 0

  /** Build the WebSocket URL */
  function buildUrl() {
    const token = localStorage.getItem('token')
    if (!token) return null
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}/ws/dashboard?token=${encodeURIComponent(token)}`
  }

  /** Connect to the backend WebSocket */
  function connect() {
    const url = buildUrl()
    if (!url) return

    // Avoid double-connect
    if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      ws.value = new WebSocket(url)
    } catch (e) {
      console.error('[WS] Failed to create WebSocket:', e)
      scheduleReconnect()
      return
    }

    ws.value.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
      console.log('[WS] Connected to dashboard real-time channel')
    }

    ws.value.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        lastMessage.value = msg
        handleMessage(msg)
      } catch (e) {
        console.warn('[WS] Failed to parse message:', event.data)
      }
    }

    ws.value.onclose = (event) => {
      connected.value = false
      ws.value = null
      if (event.code !== 1000) {
        console.warn(`[WS] Disconnected (code=${event.code}), scheduling reconnect...`)
        scheduleReconnect()
      }
    }

    ws.value.onerror = (error) => {
      console.error('[WS] Connection error:', error)
      // onclose will fire after onerror, so reconnect is handled there
    }
  }

  /** Handle incoming messages by type */
  function handleMessage(msg) {
    switch (msg.type) {
      case 'connected':
        console.log('[WS]', msg.data?.message)
        break

      case 'heartbeat':
        // Silently acknowledge
        break

      case 'health_update': {
        const d = msg.data
        showToast(
          `健康度更新：评分 ${d.health_score}，状态 ${d.health_status === 'high_risk' ? '高风险' : d.health_status === 'warning' ? '警告' : '健康'}`,
          d.health_status === 'high_risk' ? 'error' : d.health_status === 'warning' ? 'warn' : 'info'
        )
        break
      }

      case 'new_alert': {
        const d = msg.data
        showToast(
          `⚠️ 新告警: ${d.title || '未知告警'} [${d.priority || 'P1'}]`,
          d.priority === 'P0' ? 'error' : 'warn',
          8000
        )
        break
      }

      case 'data_refresh':
        showToast('🔄 看板数据已刷新', 'info', 2000)
        break

      default:
        console.log('[WS] Unknown message type:', msg.type)
    }
  }

  /** Disconnect gracefully */
  function disconnect() {
    clearReconnectTimer()
    if (ws.value) {
      ws.value.close(1000, 'Client disconnect')
      ws.value = null
    }
    connected.value = false
  }

  /** Schedule reconnection with exponential backoff */
  function scheduleReconnect() {
    clearReconnectTimer()
    const delay = Math.min(
      baseReconnectDelay * Math.pow(1.5, reconnectAttempts),
      maxReconnectDelay
    )
    reconnectAttempts++
    console.log(`[WS] Reconnecting in ${Math.round(delay / 1000)}s (attempt #${reconnectAttempts})...`)
    reconnectTimer.value = setTimeout(() => {
      connect()
    }, delay)
  }

  function clearReconnectTimer() {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }
  }

  return {
    connected,
    lastMessage,
    connect,
    disconnect
  }
}
