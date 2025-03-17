export interface Participant {
	id: string
	name: string
	role: string
	persona_description: string
}

export interface ChatRequest {
	meeting_id: string
	message: string
}

export interface ParticipantResponse {
	participant_id: string
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
	ParticipantResponse = "participant_response",
	FinalResponse = "final_response",
	Error = "error",
	Complete = "complete",
}

export interface MeetingParticipant {
	participant_id: string
	name: string
	role: string
}

export interface Meeting {
	id: string
	name: string
	participant_ids: string[]
	topic?: string
	participants: MeetingParticipant[]
}

// Remove chatroom type as we're fully migrating to Meeting
