import React, { createContext, useState } from "react"

export const ChatbotContext = createContext(null)

export const ChatbotProvider = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  return (
    <ChatbotContext.Provider value={{ isOpen, setIsOpen, conversationId, setConversationId }}>
      {children}
    </ChatbotContext.Provider>
  )
}
