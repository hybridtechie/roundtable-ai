import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { listAgents, listChatrooms, createChatroom, setChatroomTopic } from "@/lib/api"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"

const Chatrooms: React.FC = () => {
	const [chatrooms, setChatrooms] = useState<any[]>([])
	const [agents, setAgents] = useState<any[]>([])
	const [selectedAgentIds, setSelectedAgentIds] = useState<string[]>([])
	const [newTopic, setNewTopic] = useState("")
	const [selectedChatroomId, setSelectedChatroomId] = useState("")

	useEffect(() => {
		listChatrooms()
			.then((res) => setChatrooms(res.data.chatrooms))
			.catch(console.error)
		listAgents()
			.then((res) => setAgents(res.data.agents))
			.catch(console.error)
	}, [])

	const handleCreateChatroom = async () => {
		try {
			await createChatroom({ agent_ids: selectedAgentIds })
			const res = await listChatrooms()
			setChatrooms(res.data.chatrooms)
			setSelectedAgentIds([])
		} catch (error) {
			console.error("Error creating chatroom:", error)
		}
	}

	const handleSetTopic = async () => {
		try {
			await setChatroomTopic({ chatroom_id: selectedChatroomId, topic: newTopic })
			const res = await listChatrooms()
			setChatrooms(res.data.chatrooms)
			setNewTopic("")
		} catch (error) {
			console.error("Error setting topic:", error)
		}
	}

	return (
		<div className="p-6">
			<h1 className="text-3xl font-bold mb-4">Chatrooms</h1>
			<Dialog>
				<DialogTrigger asChild>
					<Button>Create New Chatroom</Button>
				</DialogTrigger>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Create Chatroom</DialogTitle>
					</DialogHeader>
					<div className="flex flex-col gap-4">
						<div className="grid gap-2">
							{agents.map((agent) => (
								<div key={agent.id} className="flex items-center gap-2">
									<input
										type="checkbox"
										checked={selectedAgentIds.includes(agent.id)}
										onChange={(e) =>
											setSelectedAgentIds(
												e.target.checked
													? [...selectedAgentIds, agent.id]
													: selectedAgentIds.filter((id) => id !== agent.id),
											)
										}
									/>
									<p>{agent.name}</p>
								</div>
							))}
						</div>
					</div>
					<DialogFooter>
						<Button onClick={handleCreateChatroom} disabled={selectedAgentIds.length === 0}>
							Create
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
			<div className="grid gap-4 mt-4">
				{chatrooms.map((chatroom) => (
					<Card key={chatroom.id}>
						<CardHeader>
							<CardTitle>{chatroom.id}</CardTitle>
						</CardHeader>
						<CardContent>
							<p>Topic: {chatroom.topic || "Not Set"}</p>
							<p>Agents: {chatroom.agent_ids.join(", ")}</p>
							<Input
								placeholder="Set Topic"
								value={newTopic}
								onChange={(e) => {
									setSelectedChatroomId(chatroom.id)
									setNewTopic(e.target.value)
								}}
								className="mt-2"
							/>
							<Button
								onClick={handleSetTopic}
								disabled={selectedChatroomId !== chatroom.id || !newTopic}
								className="mt-2">
								Set Topic
							</Button>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	)
}

export default Chatrooms
