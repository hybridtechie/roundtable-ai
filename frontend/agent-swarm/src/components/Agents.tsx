import React, { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { listAgents } from "@/lib/api"
import { Agent } from "@/types/types"

const Agents: React.FC = () => {
	const [agents, setAgents] = useState<Agent[]>([])

	useEffect(() => {
		listAgents()
			.then((res) => setAgents(res.data.agents))
			.catch((error) => {
				console.error("Failed to fetch agents:", error)
			})
	}, [])

	return (
		<div className="p-6">
			<h1 className="text-3xl font-bold mb-4">Agents</h1>
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
	)
}

export default Agents
