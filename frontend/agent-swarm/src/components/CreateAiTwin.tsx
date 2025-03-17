import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { createAiTwin, listAiTwins } from "@/lib/api"

const CreateAiTwin: React.FC = () => {
	const [newAiTwin, setNewAiTwin] = useState({ id: "", name: "", persona_description: "", context: "" })

	const handleCreateAiTwin = async () => {
		try {
			await createAiTwin(newAiTwin)
			setNewAiTwin({ id: "", name: "", persona_description: "", context: "" })
		} catch (error) {
			console.error("Error creating aiTwin:", error)
		}
	}

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">Create AiTwin</h1>
			<Card>
				<CardHeader>
					<CardTitle>New AiTwin</CardTitle>
				</CardHeader>
				<CardContent className="flex flex-col gap-4">
					<Input
						placeholder="AiTwin ID"
						value={newAiTwin.id}
						onChange={(e) => setNewAiTwin({ ...newAiTwin, id: e.target.value })}
					/>
					<Input
						placeholder="Name"
						value={newAiTwin.name}
						onChange={(e) => setNewAiTwin({ ...newAiTwin, name: e.target.value })}
					/>
					<Input
						placeholder="Persona Description"
						value={newAiTwin.persona_description}
						onChange={(e) => setNewAiTwin({ ...newAiTwin, persona_description: e.target.value })}
					/>
					<Textarea
						placeholder="Context"
						value={newAiTwin.context}
						onChange={(e) => setNewAiTwin({ ...newAiTwin, context: e.target.value })}
					/>
					<Button onClick={handleCreateAiTwin}>Create AiTwin</Button>
				</CardContent>
			</Card>
		</div>
	)
}

export default CreateAiTwin
