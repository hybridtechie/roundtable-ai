import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { listAgents } from '@/lib/api';

const Home: React.FC = () => {
  const [agents, setAgents] = useState<any[]>([]);

  useEffect(() => {
    listAgents().then((res) => setAgents(res.data.agents)).catch(console.error);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">Available Agents</h1>
      <div className="grid gap-4">
        {agents.map((agent) => (
          <Card key={agent.id}>
            <CardHeader>
              <CardTitle>{agent.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p>{agent.persona_description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Home;