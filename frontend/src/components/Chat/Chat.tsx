import React, { useRef, useEffect, useState } from "react"
import { useParams, useLocation } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { ChatMessage } from "@/components/ui/chat-message"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { ChatInput } from "@/components/ui/chat-input"
import { useAuth } from "@/context/AuthContext"
import { getChatSession, sendChatMessage, streamChat } from "@/lib/api"
import { toast } from "@/components/ui/sonner"
import { Button } from "@/components/ui/button"
import { Download, FileText, Maximize2, Minimize2 } from "lucide-react" // Added more icons
import {
  ChatMessage as ChatMessageType,
  ChatEventType,
  ParticipantResponse,
  ChatFinalResponse,
  QuestionsResponse,
  ChatErrorResponse,
  NextParticipantResponse,
} from "@/types/types"

interface DisplayMessage {
  type?: string
  name?: string
  role?: string
  question?: string
  content: string
  strength?: number
  timestamp: Date
}

interface ChatSessionDetails {
  id: string
  meeting_id: string
  user_id: string
  messages: ChatMessageType[]
  display_messages: ChatMessageType[]
  participant_id: string
  meeting_name?: string
  meeting_topic?: string
  meeting_strategy?: string
}
const Chat: React.FC = () => {
  const { meetingId, sessionId } = useParams<{ meetingId: string; sessionId?: string }>()
  const location = useLocation()
  const isStreamMode = location.pathname.includes("/stream")
  const { state, dispatch } = useAuth()

  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [inputValue, setInputValue] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionTitle, setSessionTitle] = useState<string>("")
  const [thinkingParticipant, setThinkingParticipant] = useState<string | null>(null)
  const [allMessagesExpanded, setAllMessagesExpanded] = useState<boolean | undefined>(undefined) // State for global expand/collapse
  const [meetingStrategy, setMeetingStrategy] = useState<string | undefined>(undefined) // Store meeting strategy
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupRef.current?.()
    }
  }, [])

  // Handle regular chat session loading
  useEffect(() => {
    const fetchChatSession = async () => {
      if (!sessionId || isStreamMode) {
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setMessages([]) // Clear messages while loading
      try {
        const response = await getChatSession(sessionId)
        const sessionData = response.data as ChatSessionDetails
        setMeetingStrategy(sessionData.meeting_strategy) // Store the meeting strategy

        // Set session title from meeting name/topic if available
        if (sessionData.meeting_name || sessionData.meeting_topic) {
          setSessionTitle(
            `${sessionData.meeting_name || ""}${sessionData.meeting_name && sessionData.meeting_topic ? "\n" : ""}${sessionData.meeting_topic || ""}`,
          )
        }

        // Format messages for display
        const formattedMessages = sessionData.display_messages.map((msg): DisplayMessage => {
          return {
            type: msg.type,
            name: msg.name,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(),
          }
        })

        setMessages(formattedMessages)
      } catch (err) {
        console.error("Error fetching chat session:", err)
        setError("Failed to load chat session")
      } finally {
        setIsLoading(false)
      }
    }

    fetchChatSession()
  }, [sessionId, isStreamMode])

  // Handle streaming chat mode
  useEffect(() => {
    const startStreamingChat = async () => {
      if (!meetingId || !isStreamMode) {
        setIsLoading(false)
        return
      }
      setIsLoading(true)
      setMessages([]) // Clear messages while loading

      try {
        // Get meeting details from auth context state
        const meeting = state.backendUser?.meetings?.find((m) => m.id === meetingId)

        // Set session title if meeting is found
        if (meeting && (meeting.name || meeting.topic)) {
          setSessionTitle(`${meeting.name || ""}${meeting.name && meeting.topic ? "\n" : ""}${meeting.topic || ""}`)
        } else {
          // Set a default title if meeting not found
          setSessionTitle("Meeting Discussion")
          console.warn("Meeting not found in state:", meetingId)
        }

        // Cleanup any existing chat stream
        cleanupRef.current?.()

        // Start streaming chat with meeting_id
        cleanupRef.current = streamChat(meetingId, {
          onEvent: (
            eventType: ChatEventType,
            data: ParticipantResponse | ChatFinalResponse | QuestionsResponse | ChatErrorResponse | NextParticipantResponse,
          ) => {
            switch (eventType) {
              case ChatEventType.NextParticipant:
                console.log("Next participant:", data)
                setIsLoading(false)
                if ("participant_name" in data && "participant_id" in data) {
                  setThinkingParticipant(data.participant_name)
                }
                break
              case ChatEventType.ParticipantResponse:
                setIsLoading(false)
                if ("participant" in data && "question" in data && "answer" in data) {
                  setThinkingParticipant(null)
                  setMessages((prev) => [
                    ...prev,
                    {
                      type: "participant",
                      name: data.participant,
                      question: data.question,
                      content: data.answer,
                      strength: "strength" in data ? data.strength : undefined,
                      timestamp: new Date(),
                    },
                  ])
                }
                break
              case ChatEventType.FinalResponse:
                if ("response" in data) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      type: "final",
                      content: data.response,
                      timestamp: new Date(),
                    },
                  ])
                }
                break
              case ChatEventType.Error:
                if ("detail" in data) {
                  console.error("Chat error:", data.detail)
                  toast.error(data.detail)
                  setIsLoading(false)
                }
                break
              case ChatEventType.Complete:
                setIsLoading(false)
                toast.success("Meeting completed successfully")
                break
            }
          },
        })
      } catch (error) {
        console.error("Error starting chat stream:", error)
        // More detailed error logging
        if (error instanceof Error) {
          console.error("Error message:", error.message)
          console.error("Error stack:", error.stack)
          setError(`Failed to start chat stream: ${error.message}`)
        } else {
          setError("Failed to start chat stream: Unknown error")
        }
        setIsLoading(false)
        toast.error("Failed to start chat stream. Please try again or contact support if the issue persists.")
      }
    }

    startStreamingChat()

    return () => {
      cleanupRef.current?.()
    }
  }, [meetingId, isStreamMode, state.backendUser?.meetings])

  // Scroll to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !meetingId) return

    setIsSending(true)
    try {
      const user_message: DisplayMessage[] = [
        {
          type: "user",
          name: "You",
          content: inputValue,
          timestamp: new Date(),
        },
      ]
      setMessages((prev) => [...prev, ...user_message])

      const response = await sendChatMessage(meetingId, inputValue, currentSessionId)

      // If this is first message in a new chat, store the session ID
      // Create the response message
      const response_message: DisplayMessage[] = [
        {
          type: response.data.type,
          name: response.data.name,
          content: response.data.response,
          timestamp: new Date(),
        },
      ]

      setMessages((prev) => [...prev, ...response_message])

      // If this is first message in a new chat, set session ID and add to context
      if (!currentSessionId && response.data.session_id) {
        setCurrentSessionId(response.data.session_id)

        // Create a new chat session object and add it to AuthContext
        // Create a minimal chat session with required fields
        // Get meeting details from state
        const meeting = state.backendUser?.meetings?.find((m) => m.id === meetingId)

        // Get group details if meeting has group_ids (array)
        const groupId = meeting?.group_ids?.[0] || undefined // Take first group if exists
        const group = groupId ? state.backendUser?.groups?.find((g) => g.id === groupId) : undefined

        //  Declare participants variable
        let participants: { participant_id: string; name: string; role: string }[] = []
        if (group) {
          participants = (group?.participants || []).map((p) => ({
            participant_id: p.id,
            name: p.name,
            role: p.role || "participant", // Default role if not specified
          }))
        } else {
          const participant = state.backendUser?.participants?.find((m) => m.id === meeting?.participant_ids?.[0])
          participants = [
            {
              participant_id: participant?.id || "",
              name: participant?.name || "You",
              role: participant?.role || "participant", // Default role if not specified
            },
          ]
        }

        const newChatSession = {
          id: response.data.session_id,
          meeting_id: meetingId,
          user_id: state.backendUser?.id || "",
          title: meeting?.name || sessionTitle?.split("\n")[0] || "Chat Session",
          messages: [], // Empty array for messages
          display_messages: [], // Empty array for display messages
          _ts: Math.floor(Date.now() / 1000),
          meeting_name: meeting?.name || sessionTitle?.split("\n")[0] || "",
          meeting_topic: meeting?.topic || sessionTitle?.split("\n")[1] || "",
          participants: participants,
          group_id: groupId,
          group_name: group?.name,
        }

        dispatch({ type: "ADD_CHAT_SESSION", payload: newChatSession })
      }

      setInputValue("")

      setInputValue("")
    } catch (error) {
      console.error("Error sending message:", error)
      // Display error using toast
      toast.error("Failed to send message. Please try again.")
      setError("Failed to send message") // Keep setting local error state if needed by UI
    } finally {
      setIsSending(false)
    }
  }

  const handleExportMessages = () => {
    if (messages.length === 0) {
      toast.info("No messages to export.")
      return
    }

    const jsonString = JSON.stringify(messages, null, 2) // Pretty print JSON
    const blob = new Blob([jsonString], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
    const meetingName = sessionTitle.split("\n")[0] || "chat"
    link.download = `${meetingName.replace(/\s+/g, "_")}_${timestamp}.json` // Filename: meeting_name_timestamp.json
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url) // Clean up the object URL
    toast.success("Messages exported successfully.")
  }

  const handleExportText = () => {
    if (messages.length === 0) {
      toast.info("No messages to export.")
      return
    }

    const transcript = messages
      .map((msg) => {
        const time = msg.timestamp.toLocaleTimeString()
        if (msg.type === "participant" || msg.type === "user") {
          return `[${time}] ${msg.name}${msg.role ? ` (${msg.role})` : ""}:\n${msg.content}\n`
        } else if (msg.type === "final") {
          return `[${time}] Final Response:\n${msg.content}\n`
        }
        return `[${time}] System Message:\n${msg.content}\n` // Fallback for other types
      })
      .join("\n")

    const blob = new Blob([transcript], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
    const meetingName = sessionTitle.split("\n")[0] || "chat"
    link.download = `${meetingName.replace(/\s+/g, "_")}_transcript_${timestamp}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success("Transcript exported successfully.")
  }

  const handleExpandAll = () => {
    setAllMessagesExpanded(true)
  }

  const handleCollapseAll = () => {
    setAllMessagesExpanded(false)
  }

  return (
    <div className="flex flex-col h-full">
      {sessionTitle && (
        <div className="flex items-center justify-between p-4 pb-2">
          {" "}
          {/* Use flex for layout */}
          <div className="space-y-1">
            <h2 className="text-xl font-semibold">{sessionTitle.split("\n")[0]}</h2>
            {sessionTitle.includes("\n") && <p className="text-sm text-muted-foreground">{sessionTitle.split("\n")[1]}</p>}
          </div>
          <div className="flex items-center gap-1">
            {" "}
            {/* Group buttons */}
            <Button variant="ghost" size="icon" onClick={handleExportMessages} title="Export Chat as JSON">
              <Download className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={handleExportText} title="Export Transcript as Text">
              <FileText className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={handleExpandAll} title="Expand All Messages">
              <Maximize2 className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={handleCollapseAll} title="Collapse All Messages">
              <Minimize2 className="w-5 h-5" />
            </Button>
          </div>
        </div>
      )}
      <Card className="flex flex-col flex-1 border-none">
        <CardContent className="flex flex-col p-0 h-[70vh] overflow-hidden">
          <div ref={chatContainerRef} className="flex-1 overflow-y-auto">
            <div className="p-4 space-y-4">
              {isLoading ? (
                <div className="flex flex-col items-center gap-2">
                  <LoadingSpinner size={24} />
                  <span className="text-muted-foreground">Loading messages...</span>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center text-muted-foreground">
                  {error ? (
                    <div className="text-red-500">
                      <p className="font-semibold">Error:</p>
                      <p>{error}</p>
                      <p className="mt-2 text-sm">Try refreshing the page or creating a new meeting.</p>
                    </div>
                  ) : isStreamMode ? (
                    "Waiting for participants to join the discussion..."
                  ) : sessionId ? (
                    "Start a new conversation..."
                  ) : (
                    "Waiting for user input..."
                  )}
                </div>
              ) : null}
              {messages.map((msg, index) => (
                <ChatMessage key={index} {...msg} forceExpand={allMessagesExpanded} /> // Pass expand state
              ))}
              {thinkingParticipant && (
                <div className="text-center text-muted-foreground">{thinkingParticipant} is thinking...</div>
              )}
              {isSending && !isStreamMode && <div className="text-center text-muted-foreground">Thinking...</div>}
            </div>
          </div>
        </CardContent>
        {(!meetingStrategy || meetingStrategy === "chat") && !isStreamMode && (
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSendMessage}
            disabled={isLoading || !!error || !meetingId}
            isLoading={isSending}
          />
        )}
      </Card>
    </div>
  )
}

export default Chat
