import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { createAgent, listAgents, createChatroom, setChatroomTopic, startChat, listChatrooms } from '@/lib/api';

function App() {
  // State for agents
  const [agents, setAgents] = useState<any[]>([]);
  const [newAgent, setNewAgent] = useState({ id: '', name: '', persona_description: '', context: '' });

  // State for chatrooms
  const [chatrooms, setChatrooms] = useState<any[]>([]);
  const [selectedAgentIds, setSelectedAgentIds] = useState<string[]>([]);
  const [newTopic, setNewTopic] = useState('');
  const [selectedChatroomId, setSelectedChatroomId] = useState('');

  // State for chat
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState<any>(null);

  // Fetch agents and chatrooms on mount
  useEffect(() => {
    listAgents().then((res) => setAgents(res.data.agents)).catch(console.error);
    listChatrooms().then((res) => setChatrooms(res.data.chatrooms)).catch(console.error);
  }, []);

  // Handlers
  const handleCreateAgent = async () => {
    try {
      await createAgent(newAgent);
      const res = await listAgents();
      setAgents(res.data.agents);
      setNewAgent({ id: '', name: '', persona_description: '', context: '' });
    } catch (error) {
      console.error('Error creating agent:', error);
    }
  };

  const handleCreateChatroom = async () => {
    try {
      const res = await createChatroom({ agent_ids: selectedAgentIds });
      const chatroomRes = await listChatrooms();
      setChatrooms(chatroomRes.data.chatrooms);
      setSelectedAgentIds([]);
    } catch (error) {
      console.error('Error creating chatroom:', error);
    }
  };

  const handleSetTopic = async () => {
    try {
      await setChatroomTopic({ chatroom_id: selectedChatroomId, topic: newTopic });
      const res = await listChatrooms();
      setChatrooms(res.data.chatrooms);
      setNewTopic('');
    } catch (error) {
      console.error('Error setting topic:', error);
    }
  };

  const handleStartChat = async () => {
    try {
      const res = await startChat({ chatroom_id: selectedChatroomId, message: chatMessage });
      setChatResponse(res.data);
      setChatMessage('');
    } catch (error) {
      console.error('Error starting chat:', error);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-6">Agent Swarm</h1>

      {/* Create Agent Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Create Agent</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Input
            placeholder="Agent ID"
            value={newAgent.id}
            onChange={(e) => setNewAgent({ ...newAgent, id: e.target.value })}
          />
          <Input
            placeholder="Name"
            value={newAgent.name}
            onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
          />
          <Input
            placeholder="Persona Description"
            value={newAgent.persona_description}
            onChange={(e) => setNewAgent({ ...newAgent, persona_description: e.target.value })}
          />
          <Textarea
            placeholder="Context"
            value={newAgent.context}
            onChange={(e) => setNewAgent({ ...newAgent, context: e.target.value })}
          />
          <Button onClick={handleCreateAgent}>Create Agent</Button>
        </CardContent>
      </Card>

      {/* List Agents Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Agents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            {agents.map((agent) => (
              <div key={agent.id} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedAgentIds.includes(agent.id)}
                  onChange={(e) =>
                    setSelectedAgentIds(
                      e.target.checked
                        ? [...selectedAgentIds, agent.id]
                        : selectedAgentIds.filter((id) => id !== agent.id)
                    )
                  }
                />
                <p>
                  {agent.name} - {agent.persona_description}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Create Chatroom Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Create Chatroom</CardTitle>
        </CardHeader>
        <CardContent>
          <Button onClick={handleCreateChatroom} disabled={selectedAgentIds.length === 0}>
            Create Chatroom with Selected Agents
          </Button>
        </CardContent>
      </Card>

      {/* Chatrooms Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Chatrooms</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {chatrooms.map((chatroom) => (
            <div key={chatroom.id} className="flex items-center gap-2">
              <input
                type="radio"
                name="chatroom"
                value={chatroom.id}
                checked={selectedChatroomId === chatroom.id}
                onChange={() => setSelectedChatroomId(chatroom.id)}
              />
              <p>
                {chatroom.id} - Topic: {chatroom.topic || 'Not Set'} (Agents: {chatroom.agent_ids.join(', ')})
              </p>
            </div>
          ))}
          <Input
            placeholder="Set Topic"
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            disabled={!selectedChatroomId}
          />
          <Button onClick={handleSetTopic} disabled={!selectedChatroomId || !newTopic}>
            Set Topic
          </Button>
        </CardContent>
      </Card>

      {/* Chat Section */}
      <Card>
        <CardHeader>
          <CardTitle>Chat</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Textarea
            placeholder="Enter your message"
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            disabled={!selectedChatroomId}
          />
          <Button onClick={handleStartChat} disabled={!selectedChatroomId || !chatMessage}>
            Send Message
          </Button>
          {chatResponse && (
            <div>
              <h3 className="font-semibold">Final Response:</h3>
              <p>{chatResponse.final_response}</p>
              <h3 className="font-semibold mt-4">Discussion Log:</h3>
              {chatResponse.discussion_log.map((log: any, index: number) => (
                <p key={index}>
                  <strong>{log.name} ({log.step}):</strong> {log.response}
                </p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default App;