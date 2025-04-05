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

export interface MeetingRequest {
    group_id: string
    strategy: string
    topic: string
    questions: string[]
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
    participants: Participant[]
}
