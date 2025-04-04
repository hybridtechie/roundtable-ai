import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { createParticipant } from "@/lib/api"

const CreateParticipant: React.FC = () => {
	const [newParticipant, setNewParticipant] = useState({ id: "", name: "", persona_description: "", context: "" })

	const handleCreateParticipant = async () => {
		try {
			await createParticipant(newParticipant)
			setNewParticipant({ id: "", name: "", persona_description: "", context: "" })
		} catch (error) {
			console.error("Error creating participant:", error)
		}
	}

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">Create Participant</h1>
			<Card>
				<CardHeader>
					<CardTitle>New Participant</CardTitle>
				</CardHeader>
				<CardContent className="flex flex-col gap-4">
					<Input
						placeholder="Participant ID"
						value={newParticipant.id}
						onChange={(e) => setNewParticipant({ ...newParticipant, id: e.target.value })}
					/>
					<Input
						placeholder="Name"
						value={newParticipant.name}
						onChange={(e) => setNewParticipant({ ...newParticipant, name: e.target.value })}
					/>
					<Input
						placeholder="Persona Description"
						value={newParticipant.persona_description}
						onChange={(e) => setNewParticipant({ ...newParticipant, persona_description: e.target.value })}
					/>
					<Textarea
						placeholder="Context"
						value={newParticipant.context}
						onChange={(e) => setNewParticipant({ ...newParticipant, context: e.target.value })}
					/>
					<Button onClick={handleCreateParticipant}>Create Participant</Button>
				</CardContent>
			</Card>
		</div>
	)
}

export default CreateParticipant
