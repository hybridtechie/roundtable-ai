import axios from "axios"
import { Agent, ChatRequest, AgentResponse, ChatFinalResponse, Chatroom } from "@/types/types"

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000", // Fallback to default if env not set
})

export const createAgent = (data: { id: string; name: string; persona_description: string; context: string }) =>
    api.post("/create-agent", data)

export const listAgents = () => api.get<{ agents: Agent[] }>("/list-agents")

export const createChatroom = (data: { agent_ids: string[] }) => api.post("/create-chatroom", data)

export const setChatroomTopic = (data: { chatroom_id: string; topic: string }) => api.post("/set-chatroom-topic", data)

export const startChat = (data: { chatroom_id: string; message: string }) => api.post("/chat", data)

export const listChatrooms = () => api.get<{ chatrooms: Chatroom[] }>("/list-chatrooms")

interface StreamCallbacks {
    onAgentResponse?: (response: AgentResponse) => void
    onFinalResponse?: (response: ChatFinalResponse) => void
    onError?: (error: { detail: string }) => void
    onComplete?: () => void
}

export const streamChat = (data: ChatRequest, callbacks: StreamCallbacks): (() => void) => {
    const eventSource = new EventSource(
        `${api.defaults.baseURL}/chat-stream?chatroom_id=${data.chatroom_id}&message=${encodeURIComponent(data.message)}`
    )

    eventSource.addEventListener('agent_response', ((event: MessageEvent) => {
        const data = JSON.parse(event.data) as AgentResponse
        callbacks.onAgentResponse?.(data)
    }) as EventListener)

    eventSource.addEventListener('final_response', ((event: MessageEvent) => {
        const data = JSON.parse(event.data) as ChatFinalResponse
        callbacks.onFinalResponse?.(data)
    }) as EventListener)

    eventSource.addEventListener('error', ((event: MessageEvent) => {
        const data = JSON.parse(event.data) as { detail: string }
        callbacks.onError?.(data)
    }) as EventListener)

    eventSource.addEventListener('complete', () => {
        eventSource.close()
        callbacks.onComplete?.()
    })

    eventSource.onerror = (error) => {
        console.error('SSE Error:', error)
        eventSource.close()
        callbacks.onError?.({ detail: "Connection error" })
    }

    return () => {
        eventSource.close()
    }
}
