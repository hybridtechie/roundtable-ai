import axios from "axios"
import {
	Participant,
	MeetingRequest,
	ParticipantResponse,
	ChatFinalResponse,
	Meeting,
	Group,
	ChatEventType,
	QuestionsResponse,
	ChatErrorResponse,
} from "@/types/types"

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

export const getGroup = (groupId: string) => api.get<Group>(`/group/${groupId}`)

// Meetings

export const createMeeting = (data: MeetingRequest) => api.post("/meeting", data)

export const setMeetingTopic = (data: { meeting_id: string; topic: string }) => api.post("/meeting/topic", data)

export const listMeetings = () => api.get<{ meetings: Meeting[] }>("/meetings")

export const getQuestions = (topic: string, group_id: string) =>
	api.get<{ questions: string[] }>(`/get-questions?topic=${encodeURIComponent(topic)}&group_id=${group_id}`)

interface StreamCallbacks {
	onEvent: (
		eventType: ChatEventType,
		data: ParticipantResponse | ChatFinalResponse | QuestionsResponse | ChatErrorResponse,
	) => void
}

export const streamChat = (meeting_id: string, callbacks: StreamCallbacks): (() => void) => {
	const eventSource = new EventSource(`${api.defaults.baseURL}/chat-stream?meeting_id=${meeting_id}`)

	eventSource.addEventListener(ChatEventType.Questions, ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as QuestionsResponse
		callbacks.onEvent(ChatEventType.Questions, data)
	}) as EventListener)

	eventSource.addEventListener(ChatEventType.ParticipantResponse, ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as ParticipantResponse
		callbacks.onEvent(ChatEventType.ParticipantResponse, data)
	}) as EventListener)

	eventSource.addEventListener(ChatEventType.FinalResponse, ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as ChatFinalResponse
		callbacks.onEvent(ChatEventType.FinalResponse, data)
	}) as EventListener)

	eventSource.addEventListener(ChatEventType.Error, ((event: MessageEvent) => {
		const data = JSON.parse(event.data) as ChatErrorResponse
		callbacks.onEvent(ChatEventType.Error, data)
	}) as EventListener)

	eventSource.addEventListener(ChatEventType.Complete, () => {
		eventSource.close()
		callbacks.onEvent(ChatEventType.Complete, {} as ChatErrorResponse)
	})

	eventSource.onerror = (error) => {
		console.error("SSE Error:", error)
		eventSource.close()
		callbacks.onEvent(ChatEventType.Error, { detail: "Connection error" })
	}

	return () => {
		eventSource.close()
	}
}
