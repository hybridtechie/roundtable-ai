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

export interface Group {
  id: string
  name: string
  description: string
  participants: Participant[]
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
  created_at: string
  user_id: string
  participant_id: string
  messages: ChatMessage[]
  display_messages: ChatMessage[]
  meeting_id?: string
  meeting_name?: string
  meeting_topic?: string
  group_name?: string
  group_id?: string
  _ts?: number
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
