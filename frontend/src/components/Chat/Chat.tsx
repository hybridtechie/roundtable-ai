import React, { useRef, useEffect, useState } from "react"
import { useParams, useLocation } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { ChatMessage } from "@/components/ui/chat-message"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { ChatInput } from "@/components/ui/chat-input"
import { getChatSession, sendChatMessage, streamChat, getMeeting } from "@/lib/api"
import { toast } from "@/components/ui/sonner"
import {
  ChatMessage as ChatMessageType,
  ChatEventType,
  ParticipantResponse,
  ChatFinalResponse,
  QuestionsResponse,
  ChatErrorResponse,
  NextParticipantResponse
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
}
const Chat: React.FC = () => {
  const { meetingId, sessionId } = useParams<{ meetingId: string; sessionId?: string }>()
  const location = useLocation()
  const isStreamMode = location.pathname.includes('/stream')
  
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [inputValue, setInputValue] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionTitle, setSessionTitle] = useState<string>("")
  const [thinkingParticipant, setThinkingParticipant] = useState<string | null>(null)
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
      try {
        const response = await getChatSession(sessionId)
        const sessionData = response.data as ChatSessionDetails

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
      setMessages([])
      console.log("Starting streaming chat for meeting ID:", meetingId)

      try {
        // Get meeting details to set title
        const meetingResponse = await getMeeting(meetingId)
        console.log("Meeting response:", meetingResponse.data)
        
        // Check if meeting data exists and has the expected structure
        if (meetingResponse.data && meetingResponse.data.meeting) {
          const meeting = meetingResponse.data.meeting
          
          // Set session title if name or topic exists
          if (meeting && (meeting.name || meeting.topic)) {
            setSessionTitle(
              `${meeting.name || ""}${meeting.name && meeting.topic ? "\n" : ""}${meeting.topic || ""}`,
            )
          } else {
            // Set a default title if name and topic are missing
            setSessionTitle("Meeting Discussion")
          }
        } else {
          // Set a default title if meeting data is missing
          setSessionTitle("Meeting Discussion")
          console.warn("Meeting data is missing or has unexpected structure:", meetingResponse.data)
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
                if ("participant_name" in data && "participant_id" in data) {
                  setThinkingParticipant(data.participant_name)
                }
                break
              case ChatEventType.ParticipantResponse:
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
        console.log("Chat stream started successfully")
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
  }, [meetingId, isStreamMode])

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
      if (!currentSessionId && response.data.session_id) {
        setCurrentSessionId(response.data.session_id)
      }

      // Add the user's message and the response to the messages
      const response_message: DisplayMessage[] = [
        {
          type: response.data.type,
          name: response.data.name,
          content: response.data.response,
          timestamp: new Date(),
        },
      ]

      setMessages((prev) => [...prev, ...response_message])

      setInputValue("")
    } catch (error) {
      console.error("Error sending message:", error)
      setError("Failed to send message")
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {sessionTitle && (
        <div className="p-4 pb-0">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold">{sessionTitle.split("\n")[0]}</h2>
            {sessionTitle.includes("\n") && <p className="text-sm text-muted-foreground">{sessionTitle.split("\n")[1]}</p>}
          </div>
        </div>
      )}
      <Card className="flex flex-col flex-1 border-none">
        <CardContent className="flex flex-col p-0 h-[70vh] overflow-hidden">
          <div ref={chatContainerRef} className="flex-1 overflow-y-auto">
            <div className="p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-muted-foreground">
                  {isLoading ? (
                    <div className="flex flex-col items-center gap-2">
                      <LoadingSpinner size={24} />
                      <span>Loading messages...</span>
                    </div>
                  ) : error ? (
                    <div className="text-red-500">
                      <p className="font-semibold">Error:</p>
                      <p>{error}</p>
                      <p className="mt-2 text-sm">
                        Try refreshing the page or creating a new meeting.
                      </p>
                    </div>
                  ) : (
                    isStreamMode ?
                      "Waiting for participants to join the discussion..." :
                      sessionId ? "Start a new conversation..." : "Waiting for user input..."
                  )}
                </div>
              )}
              {messages.map((msg, index) => (
                <ChatMessage key={index} {...msg} />
              ))}
              {isLoading && thinkingParticipant && (
                <div className="text-center text-muted-foreground">{thinkingParticipant} is thinking...</div>
              )}
            </div>
          </div>
        </CardContent>
        {!isStreamMode && (
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
