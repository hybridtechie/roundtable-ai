import React, { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { listChatSessions } from "@/lib/api"
import { ChatSession } from "@/types/types"

interface ChatSessionsContextType {
  chatSessions: ChatSession[]
  loading: boolean
  error: string | null
  refreshChatSessions: () => Promise<void>
}

const ChatSessionsContext = createContext<ChatSessionsContextType | undefined>(undefined)

export const useChatSessions = () => {
  const context = useContext(ChatSessionsContext)
  if (context === undefined) {
    throw new Error("useChatSessions must be used within a ChatSessionsProvider")
  }
  return context
}

interface ChatSessionsProviderProps {
  children: ReactNode
}

export const ChatSessionsProvider: React.FC<ChatSessionsProviderProps> = ({ children }) => {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchChatSessions = async () => {
    setLoading(true)
    try {
      const response = await listChatSessions()
      // Take only the last 10 sessions, sorted by most recent
      const sortedSessions = response.data.chat_sessions
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 30)
      setChatSessions(sortedSessions)
      setError(null)
    } catch (err) {
      setError("Failed to load chat sessions")
      console.error("Error fetching chat sessions:", err)
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchChatSessions()
  }, [])

  const value = {
    chatSessions,
    loading,
    error,
    refreshChatSessions: fetchChatSessions,
  }

  return <ChatSessionsContext.Provider value={value}>{children}</ChatSessionsContext.Provider>
}
