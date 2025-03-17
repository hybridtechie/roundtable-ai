export interface Agent {
    id: string
    name: string
    persona_description: string
}

export interface ChatRequest {
    chatroom_id: string
    message: string
}

export interface AgentResponse {
    agent_id: string
    name: string
    step: string
    response: string
}

export interface ChatFinalResponse {
    response: string
}

export type ChatErrorResponse = {
    detail: string
}

export enum ChatEventType {
    AgentResponse = "agent_response",
    FinalResponse = "final_response",
    Error = "error",
    Complete = "complete"
}

export interface Chatroom {
    id: string
    name: string
    agent_ids: string[]
    topic?: string
}
