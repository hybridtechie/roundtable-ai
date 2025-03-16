import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000', // Your FastAPI backend
});

export const createAgent = (data: { id: string; name: string; persona_description: string; context: string }) =>
  api.post('/create-agent', data);

export const listAgents = () => api.get('/list-agents');

export const createChatroom = (data: { agent_ids: string[] }) => api.post('/create-chatroom', data);

export const setChatroomTopic = (data: { chatroom_id: string; topic: string }) =>
  api.post('/set-chatroom-topic', data);

export const startChat = (data: { chatroom_id: string; message: string }) => api.post('/chat', data);

export const listChatrooms = () => api.get('/list-chatrooms');