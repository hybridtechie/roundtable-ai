import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { createAgent, listAgents } from "@/lib/api"

const CreateAgent: React.FC = () => {
	const [newAgent, setNewAgent] = useState({ id: "", name: "", persona_description: "", context: "" })

	const handleCreateAgent = async () => {
		try {
			await createAgent(newAgent)
			setNewAgent({ id: "", name: "", persona_description: "", context: "" })
		} catch (error) {
			console.error("Error creating agent:", error)
		}
	}

	return (
		<div className="p-6">
			<h1 className="text-3xl font-bold mb-4">Create Agent</h1>
			<Card>
				<CardHeader>
					<CardTitle>New Agent</CardTitle>
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
		</div>
	)
}

export default CreateAgent
