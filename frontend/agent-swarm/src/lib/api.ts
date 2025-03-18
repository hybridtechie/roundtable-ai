import axios from "axios"
import { Participant, MeetingRequest, ParticipantResponse, ChatFinalResponse, Meeting, Group } from "@/types/types"

const api = axios.create({
	baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000", // Fallback to default if env not set
})

// Participants
export const createParticipant = (data: { id: string; name: string; persona_description: string; context: string }) =>
	api.post("/participant", data)

export const listParticipants = () => api.get<{ participants: Participant[] }>("/participants")

// Groups

export const createGroup = (data: { participant_ids: string[] }) => api.post("/group", data)

export const listGroups = () => api.get<{ groups: Group[] }>("/groups")

// Meetings

export const createMeeting = (data: { participant_ids: string[] }) => api.post("/meeting", data)

export const setMeetingTopic = (data: { meeting_id: string; topic: string }) => api.post("/meeting/topic", data)

export const listMeetings = () => api.get<{ meetings: Meeting[] }>("/meetings")

interface StreamCallbacks {
	onParticipantResponse?: (response: ParticipantResponse) => void
	onFinalResponse?: (response: ChatFinalResponse) => void
	onError?: (error: { detail: string }) => void
	onComplete?: () => void
}

export const streamChat = (data: MeetingRequest, callbacks: StreamCallbacks): (() => void) => {
	const eventSource = new EventSource(
		`${api.defaults.baseURL}/chat-stream?group_id=${data.group_id}&strategy=${encodeURIComponent(data.strategy)}&message=${encodeURIComponent(data.message)}`,
	)

	eventSource.addEventListener("participant_response", ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as ParticipantResponse
		callbacks.onParticipantResponse?.(data)
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
