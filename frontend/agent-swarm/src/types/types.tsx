export interface AiTwin {
	id: string
	name: string
	role: string
	persona_description: string
}

export interface ChatRequest {
	meeting_id: string
	message: string
}

export interface AiTwinResponse {
	aitwin_id: string
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
	AiTwinResponse = "aitwin_response",
	FinalResponse = "final_response",
	Error = "error",
	Complete = "complete",
}

export interface Meeting {
	id: string
	name: string
	aitwin_ids: string[]
	topic?: string
}

// Remove chatroom type as we're fully migrating to Meeting
