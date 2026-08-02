import { useState, useEffect, useRef, useCallback } from 'react'

export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('🔗 WebSocket connected')
        setIsConnected(true)
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected', event.code, event.reason)
        setIsConnected(false)
        // Attempt reconnect after 3 seconds if not closed intentionally
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 Reconnecting WebSocket...')
            connect()
          }, 3000)
        }
      }

      ws.onerror = (error) => {
        console.error('💥 WebSocket error:', error)
        // The browser will close the connection; onclose will handle reconnect
      }

      ws.onmessage = (event) => {
        setLastMessage(event.data)
      }
    } catch (error) {
      console.error('💥 WebSocket connection error:', error)
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
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
      return true
    }
    console.warn('Cannot send message – WebSocket not open')
    return false
  }, [])

  return { isConnected, lastMessage, sendMessage }
}