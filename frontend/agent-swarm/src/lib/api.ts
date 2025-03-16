import axios from "axios"
import { Agent } from "@/types/types"

const api = axios.create({
	baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000", // Fallback to default if env not set
})

export const createAgent = (data: { id: string; name: string; persona_description: string; context: string }) =>
	api.post("/create-agent", data)

export const listAgents = () => api.get<{ agents: Agent[] }>("/list-agents")

export const createChatroom = (data: { agent_ids: string[] }) => api.post("/create-chatroom", data)

export const setChatroomTopic = (data: { chatroom_id: string; topic: string }) => api.post("/set-chatroom-topic", data)

export const startChat = (data: { chatroom_id: string; message: string }) => api.post("/chat", data)

export const listChatrooms = () => api.get("/list-chatrooms")
