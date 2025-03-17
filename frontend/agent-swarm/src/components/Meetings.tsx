import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { listParticipants, listMeetings, createMeeting } from "@/lib/api"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Participant, Meeting } from "@/types/types"

const Meetings: React.FC = () => {
	const [meetings, setMeetings] = useState<Meeting[]>([])
	const [participants, setParticipants] = useState<Participant[]>([])
	const [selectedParticipantIds, setSelectedParticipantIds] = useState<string[]>([])

	useEffect(() => {
		listMeetings()
			.then((res) => setMeetings(res.data.meetings))
			.catch(console.error)
		listParticipants()
			.then((res) => setParticipants(res.data.participants))
			.catch(console.error)
	}, [])

	const handleCreateMeeting = async () => {
		try {
			await createMeeting({ participant_ids: selectedParticipantIds })
			const res = await listMeetings()
			setMeetings(res.data.meetings)
			setSelectedParticipantIds([])
		} catch (error) {
			console.error("Error creating meeting:", error)
		}
	}

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">Meetings</h1>
			<Dialog>
				<DialogTrigger asChild>
					<Button>Create New Meeting</Button>
				</DialogTrigger>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Create Meeting</DialogTitle>
					</DialogHeader>
					<div className="flex flex-col gap-4">
						<div className="grid gap-2">
							{participants.map((participant) => (
								<div key={participant.id} className="flex items-center gap-2">
									<input
										type="checkbox"
										checked={selectedParticipantIds.includes(participant.id)}
										onChange={(e) =>
											setSelectedParticipantIds(
												e.target.checked
													? [...selectedParticipantIds, participant.id]
													: selectedParticipantIds.filter((id) => id !== participant.id),
											)
										}
									/>
									<p>{participant.name}</p>
								</div>
							))}
						</div>
					</div>
					<DialogFooter>
						<Button onClick={handleCreateMeeting} disabled={selectedParticipantIds.length === 0}>
							Create
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
			<div className="grid gap-4 mt-4">
				{meetings.map((meeting) => (
					<Card key={meeting.id}>
						<CardHeader>
							<CardTitle>{meeting.name || meeting.id}</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="space-y-2">
								<div>
									<p className="mb-2 font-medium">Participants:</p>
									<ul className="pl-6 space-y-1 list-disc">
										{meeting.participants.map((participant) => (
											<li key={participant.participant_id}>
												<span className="font-medium">{participant.name}</span>
												<span className="text-gray-600"> - {participant.role}</span>
											</li>
										))}
									</ul>
								</div>
							</div>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	)
}

export default Meetings
