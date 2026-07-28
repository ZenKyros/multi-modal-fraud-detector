import { useState, useEffect, useRef, useCallback } from 'react'

const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('🔗 WebSocket connected')
        setIsConnected(true)
        // Clear any reconnect timeout if we succeeded
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected', event.code, event.reason)
        setIsConnected(false)
        // Attempt reconnect after delay (unless closed intentionally)
        if (event.code !== 1000) { // Normal closure
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 Attempting WebSocket reconnect...')
            connect()
          }, 3000)
        }
      }

      ws.onerror = (error) => {
        console.error('💥 WebSocket error:', error)
        // The browser will close the connection automatically; onclose will handle reconnect
      }

      ws.onmessage = (event) => {
        setLastMessage(event.data)
      }
    } catch (error) {
      console.error('💥 WebSocket connection error:', error)
      // Retry after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => connect(), 3000)
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting')
      }
    }
  }, [connect])

  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
      return true
    } else {
      console.warn('Cannot send message – WebSocket not open')
      return false
    }
  }, [])

  return {
    isConnected,
    lastMessage,
    sendMessage,
  }
}

export default useWebSocket