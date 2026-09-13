import { useEffect, useRef } from "react"

/**
 * Live chat socket (master spec §30). Subscribes to a conversation's
 * WebSocket and forwards persisted events (user_message / bot_reply) so
 * every open tab or device stays in sync without polling. The REST POST
 * remains the canonical send path; if the socket is unavailable (proxy
 * without WS support, server without channels) the chat keeps working
 * exactly as before — this hook is purely additive.
 */
export default function useChatSocket(conversationId, onEvent) {
  const handler = useRef(onEvent)
  useEffect(() => {
    handler.current = onEvent
  }, [onEvent])

  useEffect(() => {
    if (!conversationId) return undefined
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:"
    let ws
    let closed = false
    let retry = 0
    let retryTimer = null

    const connect = () => {
      try {
        ws = new WebSocket(`${proto}//${window.location.host}/ws/chat/${conversationId}/`)
      } catch {
        return
      }
      ws.onopen = () => { retry = 0 }
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === "user_message" || data.type === "bot_reply" || data.type === "admin_reply") handler.current?.(data)
        } catch {
          /* ignore malformed frames */
        }
      }
      ws.onclose = () => {
        if (!closed && retry < 3) {
          retry += 1
          retryTimer = setTimeout(connect, 1000 * retry)
        }
      }
      ws.onerror = () => {
        try { ws.close() } catch { /* noop */ }
      }
    }

    connect()
    return () => {
      closed = true
      if (retryTimer) clearTimeout(retryTimer)
      try { ws?.close() } catch { /* noop */ }
    }
  }, [conversationId])
}
