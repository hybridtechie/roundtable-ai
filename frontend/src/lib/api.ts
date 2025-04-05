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
  NextParticipantResponse,
} from "@/types/types"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000", // Fallback to default if env not set
})

const USER_ID = "roundtable_ai_admin"

// Participants
export const createParticipant = (data: {
  name: string;
  role: string;
  professional_background: string;
  industry_experience: string;
  role_overview: string;
  technical_stack: string;
  soft_skills: string;
  core_qualities: string;
  style_preferences: string;
  additional_info: string;
}) => api.post("/participant", data)

export const listParticipants = () => 
  api.get<{ participants: Participant[] }>(`/participants?user_id=${USER_ID}`)

export const getParticipant = (participantId: string) =>
  api.get<Participant>(`/participant/${participantId}?user_id=${USER_ID}`)

export const updateParticipant = (participantId: string, data: {
  name: string;
  role: string;
  professional_background: string;
  industry_experience: string;
  role_overview: string;
  technical_stack: string;
  soft_skills: string;
  core_qualities: string;
  style_preferences: string;
  additional_info: string;
}) => api.put(`/participant/${participantId}`, data)

export const deleteParticipant = (participantId: string) =>
  api.delete(`/participant/${participantId}?user_id=${USER_ID}`)

// Groups
export const createGroup = (data: { name: string; description?: string; participant_ids: string[]; userId?: string }) =>
  api.post("/group", { ...data, userId: data.userId || USER_ID })

export const listGroups = () => 
  api.get<{ groups: Group[] }>(`/groups?user_id=${USER_ID}`)

export const getGroup = (groupId: string) => 
  api.get<Group>(`/group/${groupId}?user_id=${USER_ID}`)

export const updateGroup = (groupId: string, data: { name: string; participant_ids: string[] }) =>
  api.put(`/group/${groupId}`, data)

export const deleteGroup = (groupId: string) =>
  api.delete(`/group/${groupId}?user_id=${USER_ID}`)

// Meetings
export const createMeeting = (data: MeetingRequest) => 
  api.post("/meeting", data)

export const listMeetings = () => 
  api.get<{ meetings: Meeting[] }>(`/meetings?user_id=${USER_ID}`)

export const getQuestions = (topic: string, groupId: string) =>
  api.get<{ questions: string[] }>(`/get-questions?topic=${encodeURIComponent(topic)}&group_id=${groupId}&user_id=${USER_ID}`)

interface StreamCallbacks {
  onEvent: (
    eventType: ChatEventType,
    data: ParticipantResponse | ChatFinalResponse | QuestionsResponse | ChatErrorResponse | NextParticipantResponse,
  ) => void
}

// LLM Account Management
export interface LLMAccountCreate {
  provider: string
  deployment_name?: string
  model: string
  endpoint?: string
  api_version?: string
  api_key: string
}

export interface LLMAccountUpdate {
  model?: string
  deployment_name?: string
  endpoint?: string
  api_version?: string
  api_key?: string
}

export interface LLMAccountsResponse {
  default: string
  providers: LLMAccountCreate[]
}

export const createLLMAccount = (data: LLMAccountCreate) =>
  api.post("/llm-account", data)

export const listLLMAccounts = () =>
  api.get<LLMAccountsResponse>(`/llm-accounts?user_id=${USER_ID}`)

export const updateLLMAccount = (provider: string, data: LLMAccountUpdate) =>
  api.put(`/llm-account/${provider}`, data)

export const deleteLLMAccount = (provider: string) =>
  api.delete(`/llm-account/${provider}?user_id=${USER_ID}`)

export const setDefaultProvider = (provider: string) =>
  api.put(`/llm-account/${provider}/set-default?user_id=${USER_ID}`)

export const streamChat = (meetingId: string, callbacks: StreamCallbacks): (() => void) => {
  const eventSource = new EventSource(`${api.defaults.baseURL}/chat-stream?meeting_id=${meetingId}&user_id=${USER_ID}`)

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

  eventSource.addEventListener(ChatEventType.NextParticipant, ((event: MessageEvent) => {
    const data = JSON.parse(event.data) as NextParticipantResponse
    callbacks.onEvent(ChatEventType.NextParticipant, data)
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
