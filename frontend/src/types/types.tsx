export interface Participant {
  id: string
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
}

// Type for updating participant data (all fields optional except maybe name/role if required by backend)
export type ParticipantUpdateData = Partial<Omit<Participant, "id">> & {
  // Add required fields if any, e.g.:
  // name: string;
  // role: string;
}

export interface Group {
  id: string
  name: string
  description: string
  participants: Participant[] // Full participant objects (might be incomplete/empty from API)
  participant_ids?: string[] // Optional: Array of participant IDs (might be present from API)
}

export interface ParticipantOrder {
  participant_id: string
  weight: number
  order: number
}

export interface MeetingRequest {
  group_id?: string
  participant_id?: string
  name?: string
  strategy: string
  topic: string
  questions: string[]
  participant_order?: ParticipantOrder[]
}

export interface ParticipantResponse {
  participant: string
  question: string
  answer: string
  strength?: number
}

export interface ChatFinalResponse {
  response: string
}

export interface QuestionsResponse {
  questions: string[]
}

export type ChatErrorResponse = {
  detail: string
}

export interface NextParticipantResponse {
  participant_id: string
  participant_name: string
}

export enum ChatEventType {
  Questions = "questions",
  ParticipantResponse = "participant_response",
  FinalResponse = "final_response",
  Error = "error",
  Complete = "complete",
  NextParticipant = "next_participant",
}

export interface Meeting {
  id: string
  name: string
  participant_ids: string[]
  group_ids: string[]
  topic?: string
  strategy: string
  participants: Participant[]
}

export interface ChatSession {
  id: string
  title: string
  user_id: string
  messages: ChatMessage[]
  display_messages: ChatMessage[]
  // Required field from CosmosDB
  _ts: number // CosmosDB timestamp, used as created_at
  // Optional fields
  participant_id?: string
  meeting_id?: string
  meeting_name?: string
  meeting_topic?: string
  group_name?: string
  group_id?: string
  participants: {
    participant_id: string
    name: string
    role: string
  }[]
}

export interface ChatMessage {
  role: string
  content: string
  type?: string
  name?: string
  step?: string
}

export interface UserInfo {
  user_id: string
  display_name: string
  email: string
}

export interface UserDetailInfo extends UserInfo {
  llm_providers_count: number
  participants_count: number
  meetings_count: number
  groups_count: number
  chat_sessions_count: number
}

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

export interface DeleteResponse {
  deleted_id: string // Matches the backend response format
}
