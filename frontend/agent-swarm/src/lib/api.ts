import axios from "axios"
import { AiTwin, ChatRequest, AiTwinResponse, ChatFinalResponse, Meeting } from "@/types/types"

const api = axios.create({
	baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000", // Fallback to default if env not set
})

export const createAiTwin = (data: { id: string; name: string; persona_description: string; context: string }) =>
	api.post("/aitwin", data)

export const listAiTwins = () => api.get<{ aitwins: AiTwin[] }>("/aitwins")

export const createMeeting = (data: { aitwin_ids: string[] }) => api.post("/meeting", data)

export const setMeetingTopic = (data: { meeting_id: string; topic: string }) => api.post("/meeting/topic", data)

export const startChat = (data: { meeting_id: string; message: string }) => api.post("/chat", data)

export const listMeetings = () => api.get<{ meetings: Meeting[] }>("/meetings")

interface StreamCallbacks {
	onAiTwinResponse?: (response: AiTwinResponse) => void
	onFinalResponse?: (response: ChatFinalResponse) => void
	onError?: (error: { detail: string }) => void
	onComplete?: () => void
}

export const streamChat = (data: ChatRequest, callbacks: StreamCallbacks): (() => void) => {
	const eventSource = new EventSource(
		`${api.defaults.baseURL}/chat-stream?meeting_id=${data.meeting_id}&message=${encodeURIComponent(data.message)}`,
	)

	eventSource.addEventListener("aitwin_response", ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as AiTwinResponse
		callbacks.onAiTwinResponse?.(data)
	}) as EventListener)

	eventSource.addEventListener("final_response", ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as ChatFinalResponse
		callbacks.onFinalResponse?.(data)
	}) as EventListener)

	eventSource.addEventListener("error", ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as { detail: string }
		callbacks.onError?.(data)
	}) as EventListener)

	eventSource.addEventListener("complete", () => {
		eventSource.close()
		callbacks.onComplete?.()
	})

	eventSource.onerror = (error) => {
		console.error("SSE Error:", error)
		eventSource.close()
		callbacks.onError?.({ detail: "Connection error" })
	}

	return () => {
		eventSource.close()
	}
}
