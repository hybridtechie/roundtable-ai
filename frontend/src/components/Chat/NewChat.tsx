import React, { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { listParticipants, createMeeting } from "@/lib/api"
import { Participant } from "@/types/types"

const NewChat: React.FC = () => {
	const navigate = useNavigate()
	const [participants, setParticipants] = useState<Participant[]>([])
	const [selectedParticipant, setSelectedParticipant] = useState("")
	const [name, setName] = useState("")
	const [topic, setTopic] = useState("")
	const [loading, setLoading] = useState(false)

	useEffect(() => {
		const fetchParticipants = async () => {
			try {
				const response = await listParticipants()
				setParticipants(response.data.participants)
			} catch (error) {
				console.error("Error fetching participants:", error)
			}
		}
		fetchParticipants()
	}, [])

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault()
		setLoading(true)
		try {
			// Create a meeting directly with the participant
			const response = await createMeeting({
				participant_id: selectedParticipant,
				name: name,
				topic: topic,
				strategy: "chat",
				questions: [],
				participant_order: [
					{
						participant_id: selectedParticipant,
						weight: 10,
						order: 1,
					},
				],
			})
			navigate(`/chat/new`, { state: { meetingId: response.data.meeting_id } })
		} catch (error) {
			console.error("Error creating chat:", error)
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="container p-4 mx-auto">
			<Card>
				<CardContent className="p-6">
					<form onSubmit={handleSubmit} className="space-y-4">
						<div className="space-y-2">
							<label htmlFor="participant" className="text-sm font-medium">
								Select Participant
							</label>
							<Select value={selectedParticipant} onValueChange={setSelectedParticipant}>
								<SelectTrigger className="w-full">
									<SelectValue placeholder="Select a participant" />
								</SelectTrigger>
								<SelectContent>
									{participants.map((participant) => (
										<SelectItem key={participant.id} value={participant.id}>
											{participant.name} - {participant.role}
										</SelectItem>
									))}
								</SelectContent>
							</Select>
						</div>

						<div className="space-y-2">
							<label htmlFor="strategy" className="text-sm font-medium">
								Strategy
							</label>
							<Select value="chat" onValueChange={() => {}}>
								<SelectTrigger className="w-full">
									<SelectValue placeholder="Select a strategy" />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="chat">Chat</SelectItem>
								</SelectContent>
							</Select>
						</div>

						<div className="space-y-2">
							<label htmlFor="name" className="text-sm font-medium">
								Chat Name
							</label>
							<Input
								id="name"
								value={name}
								onChange={(e) => setName(e.target.value)}
								placeholder="Enter chat name"
								required
							/>
						</div>

						<div className="space-y-2">
							<label htmlFor="topic" className="text-sm font-medium">
								Topic
							</label>
							<Input
								id="topic"
								value={topic}
								onChange={(e) => setTopic(e.target.value)}
								placeholder="Enter chat topic"
								required
							/>
						</div>

						<Button type="submit" disabled={loading || !selectedParticipant || !name || !topic}>
							{loading ? "Creating..." : "Start Chat"}
						</Button>
					</form>
				</CardContent>
			</Card>
		</div>
	)
}

export default NewChat
