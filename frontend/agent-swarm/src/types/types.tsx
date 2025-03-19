export interface Participant {
	id: string
	name: string
	role: string
	persona_description: string
}

export interface Group {
	id: string
	name: string
	descriptions: string
	participants: Participant[]
}

export interface MeetingRequest {
	group_id: string
	strategy: string
	topic: string
	questions: string[]
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

export interface Meeting {
	id: string
	name: string
	participant_ids: string[]
	group_ids: string[]
	topic?: string
	participants: Participant[]
}
