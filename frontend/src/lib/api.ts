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
  ChatSession,
  LLMAccountCreate,
  LLMAccountUpdate,
  LLMAccountsResponse,
  DeleteResponse
} from "@/types/types"

// Determine the base URL based on environment
const getBaseUrl = () => {
  // If VITE_API_URL is set, use it (highest priority)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }

  // Check if we're in development or production
  const isDevelopment = import.meta.env.MODE === "development"

  return isDevelopment
    ? "http://localhost:8000" // Local development
    : "https://wa-roundtableai-azd3a2hxenb9a4gr.australiaeast-01.azurewebsites.net" // Production
}

const api = axios.create({
  baseURL: getBaseUrl(),
})

// Add a request interceptor to include the access token in headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("idToken")
    if (token) {
      console.log("Token Found")
      config.headers.Authorization = `Bearer ${token}`
    }else{
      console.log("No token found")
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

const USER_ID = "roundtable_ai_admin"

// Participants
export const createParticipant = (data: {
  name: string
  role: string
  professional_background: string
  industry_experience: string
  role_overview: string
  technical_stack: string
  soft_skills: string
  core_qualities: string
  style_preferences: string
  additional_info: string
}) => api.post("/participant", { ...data, user_id: USER_ID })

export const listParticipants = () => api.get<{ participants: Participant[] }>(`/participants`)

export const getParticipant = (participantId: string) => api.get<Participant>(`/participant/${participantId}`)

export const updateParticipant = (
  participantId: string,
  data: {
    name: string
    role: string
    professional_background: string
    industry_experience: string
    role_overview: string
    technical_stack: string
    soft_skills: string
    core_qualities: string
    style_preferences: string
    additional_info: string
  },
) => api.put(`/participant/${participantId}`, { ...data, user_id: USER_ID })

export const deleteParticipant = (participantId: string) => api.delete(`/participant/${participantId}`)

// Groups
export const createGroup = (data: { name: string; description?: string; participant_ids: string[]; userId?: string }) =>
  api.post("/group", { ...data, userId: data.userId || USER_ID })

export const listGroups = () => api.get<{ groups: Group[] }>(`/groups`)

export const getGroup = (groupId: string) => api.get<Group>(`/group/${groupId}`)

export const updateGroup = (groupId: string, data: { name: string; participant_ids: string[] }) =>
  api.put(`/group/${groupId}`, { ...data, user_id: USER_ID })

export const deleteGroup = (groupId: string) => api.delete(`/group/${groupId}`)

// Meetings
export const createMeeting = (data: MeetingRequest) => api.post("/meeting", data)

export const listMeetings = () => api.get<{ meetings: Meeting[] }>(`/meetings`)

export const getMeeting = (meetingId: string) => api.get<{ meeting: Meeting }>(`/meeting/${meetingId}`)

export const deleteMeeting = (meetingId: string) => api.delete(`/meeting/${meetingId}`)

export const getQuestions = (topic: string, groupId: string) =>
  api.get<{ questions: string[] }>(`/get-questions?topic=${encodeURIComponent(topic)}&group_id=${groupId}&user_id=${USER_ID}`)

// Chat Sessions
export const listChatSessions = () => api.get<{ chat_sessions: ChatSession[] }>(`/chat-sessions`)

export const sendChatMessage = (meetingId: string, message: string, sessionId?: string) =>
  api.post<{ session_id: string; response: string; name: string; type: string; timestap: string }>(
    `/chat-session`,
    {
      meeting_id: meetingId,
      user_message: message,
      session_id: sessionId,
    },
  )

export const getChatSession = (sessionId: string) => api.get(`/chat-session/${sessionId}`)

export const deleteChatSession = (sessionId: string) => api.delete<DeleteResponse>(`/chat-session/${sessionId}`)

interface StreamCallbacks {
  onEvent: (
    eventType: ChatEventType,
    data: ParticipantResponse | ChatFinalResponse | QuestionsResponse | ChatErrorResponse | NextParticipantResponse,
  ) => void
}

// LLM Account Management


export const createLLMAccount = (data: LLMAccountCreate) => api.post("/llm-account", data)

export const listLLMAccounts = () => api.get<LLMAccountsResponse>(`/llm-accounts`)

export const updateLLMAccount = (provider: string, data: LLMAccountUpdate) => api.put(`/llm-account/${provider}`, data)

export const deleteLLMAccount = (provider: string) => api.delete(`/llm-account/${provider}`)

export const setDefaultProvider = (provider: string) => api.put(`/llm-account/${provider}/set-default`)

// User Information
export const login = () => api.post("/user/login")

export const streamChat = (meetingId: string, callbacks: StreamCallbacks): (() => void) => {
  console.log(`Starting chat stream for meeting ID: ${meetingId}, user ID: ${USER_ID}`)
  const url = `${api.defaults.baseURL}/chat-stream?meeting_id=${meetingId}&user_id=${USER_ID}`
  console.log(`EventSource URL: ${url}`)
  
  const eventSource = new EventSource(url)

  // Handle connection open
  eventSource.onopen = () => {
    console.log("EventSource connection opened successfully")
  }

  eventSource.addEventListener(ChatEventType.Questions, ((event: MessageEvent) => {
    console.log("Received questions event:", event.data)
    try {
      const data = JSON.parse(event.data) as QuestionsResponse
      callbacks.onEvent(ChatEventType.Questions, data)
    } catch (error) {
      console.error("Error parsing questions event:", error)
    }
  }) as EventListener)

  eventSource.addEventListener(ChatEventType.ParticipantResponse, ((event: MessageEvent) => {
    console.log("Received participant response event:", event.data)
    try {
      const data = JSON.parse(event.data) as ParticipantResponse
      callbacks.onEvent(ChatEventType.ParticipantResponse, data)
    } catch (error) {
      console.error("Error parsing participant response event:", error)
    }
  }) as EventListener)

  eventSource.addEventListener(ChatEventType.FinalResponse, ((event: MessageEvent) => {
    console.log("Received final response event:", event.data)
    try {
      const data = JSON.parse(event.data) as ChatFinalResponse
      callbacks.onEvent(ChatEventType.FinalResponse, data)
    } catch (error) {
      console.error("Error parsing final response event:", error)
    }
  }) as EventListener)

  eventSource.addEventListener(ChatEventType.Error, ((event: MessageEvent) => {
    console.log("Received error event:", event.data)
    try {
      const data = JSON.parse(event.data) as ChatErrorResponse
      callbacks.onEvent(ChatEventType.Error, data)
    } catch (error) {
      console.error("Error parsing error event:", error)
      callbacks.onEvent(ChatEventType.Error, { detail: "Error parsing error event" })
    }
  }) as EventListener)

  eventSource.addEventListener(ChatEventType.NextParticipant, ((event: MessageEvent) => {
    console.log("Received next participant event:", event.data)
    try {
      const data = JSON.parse(event.data) as NextParticipantResponse
      callbacks.onEvent(ChatEventType.NextParticipant, data)
    } catch (error) {
      console.error("Error parsing next participant event:", error)
    }
  }) as EventListener)

  eventSource.addEventListener(ChatEventType.Complete, (() => {
    console.log("Received complete event")
    eventSource.close()
    callbacks.onEvent(ChatEventType.Complete, {} as ChatErrorResponse)
  }) as EventListener)

  eventSource.onerror = (error) => {
    console.error("SSE Error:", error)
    eventSource.close()
    callbacks.onEvent(ChatEventType.Error, { detail: "Connection error with the server. Please try again later." })
  }

  return () => {
    eventSource.close()
  }
}
