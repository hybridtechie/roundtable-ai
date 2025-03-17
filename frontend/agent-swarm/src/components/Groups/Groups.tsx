import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { listParticipants, listGroups, createGroup } from "@/lib/api"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Participant, Group } from "@/types/types"

const Groups: React.FC = () => {
	const [groups, setGroups] = useState<Group[]>([])
	const [participants, setParticipants] = useState<Participant[]>([])
	const [selectedParticipantIds, setSelectedParticipantIds] = useState<string[]>([])

	useEffect(() => {
		listGroups()
			.then((res) => setGroups(res.data.groups))
			.catch(console.error)
		listParticipants()
			.then((res) => setParticipants(res.data.participants))
			.catch(console.error)
	}, [])

	const handleCreateGroup = async () => {
		try {
			await createGroup({ participant_ids: selectedParticipantIds })
			const res = await listGroups()
			setGroups(res.data.groups)
			setSelectedParticipantIds([])
		} catch (error) {
			console.error("Error creating group:", error)
		}
	}

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">Groups</h1>
			<Dialog>
				<DialogTrigger asChild>
					<Button>Create New Group</Button>
				</DialogTrigger>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Create Group</DialogTitle>
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
						<Button onClick={handleCreateGroup} disabled={selectedParticipantIds.length === 0}>
							Create
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
			<div className="grid gap-4 mt-4">
				{groups.map((group) => (
					<Card key={group.id}>
						<CardHeader>
							<CardTitle>{group.name || group.id}</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="space-y-2">
								<div>
									<p className="mb-2 font-medium">Participants:</p>
									<ul className="pl-6 space-y-1 list-disc">
										{group.participants.map((participant) => (
											<li key={participant.id}>
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

export default Groups
