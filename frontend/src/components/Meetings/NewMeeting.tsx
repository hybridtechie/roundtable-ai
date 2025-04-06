import React, { useState, useRef, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { streamChat, listGroups, getGroup, getQuestions, createMeeting } from "@/lib/api"
import { toast } from "@/components/ui/sonner"
import {
	Group,
	Participant,
	ChatEventType,
	ParticipantResponse,
	ChatFinalResponse,
	QuestionsResponse,
	ChatErrorResponse,
	NextParticipantResponse,
} from "@/types/types"
import { ChatMessage } from "@/components/ui/chat-message"
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from "@dnd-kit/core"
import {
	arrayMove,
	SortableContext,
	sortableKeyboardCoordinates,
	useSortable,
	verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Textarea } from "@/components/ui/textarea"

interface ChatMessageType {
	type: "participant" | "final"
	name?: string
	question?: string
	content: string
	strength?: number
	timestamp: Date
}

interface WeightedParticipant {
	id: string
	name: string
	weight: number
}

// Sortable Participant Item Component
const SortableParticipant: React.FC<{
	participant: WeightedParticipant
	updateWeight: (id: string, weight: number) => void
}> = ({ participant, updateWeight }) => {
	const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: participant.id })

	const style = {
		transform: CSS.Transform.toString(transform),
		transition,
	}

	return (
		<li
			ref={setNodeRef}
			style={style}
			{...attributes}
			{...listeners}
			className="flex items-center justify-between p-2 bg-gray-100 rounded cursor-move">
			<span>{participant.name}</span>
			<input
				type="number"
				min="1"
				max="10"
				value={participant.weight}
				onChange={(e) => updateWeight(participant.id, parseInt(e.target.value))}
				className="w-16 p-1 border rounded"
			/>
		</li>
	)
}

const NewMeeting: React.FC = () => {
	const [step, setStep] = useState<"group" | "participants" | "questions" | "chat">("group")
	const [selectedGroup, setSelectedGroup] = useState<string>("")

	// Handle group selection
	const handleGroupSelect = async (groupId: string) => {
		setSelectedGroup(groupId)
		setParticipants([]) // Clear participants before fetching new ones

		try {
			const response = await getGroup(groupId)
			const groupParticipants = response.data.participants.map((p: Participant) => ({
				id: p.id,
				name: p.name,
				role: p.role,
				weight: 5, // Default weight
				persona_description: p.role_overview || "Participant",
			}))
			setParticipants(groupParticipants)
		} catch (error) {
			console.error("Error fetching group participants:", error)
			toast.error("Failed to fetch group participants")
		}
	}
	const [discussionStrategy, setDiscussionStrategy] = useState<string>("round robin")
	const [topic, setTopic] = useState<string>("")
	const [groups, setGroups] = useState<Group[]>([])
	interface ExtendedParticipant extends WeightedParticipant {
		persona_description: string
		role: string
	}

	const [participants, setParticipants] = useState<ExtendedParticipant[]>([])
	const [thinkingParticipant, setThinkingParticipant] = useState<string | null>(null)
	const [questions, setQuestions] = useState<string[]>([])
	const [selectedQuestions, setSelectedQuestions] = useState<string[]>([])
	const [messages, setMessages] = useState<ChatMessageType[]>([])
	const [isLoading, setIsLoading] = useState(false)
	const cleanupRef = useRef<(() => void) | null>(null)
	const chatContainerRef = useRef<HTMLDivElement>(null)

	// Setup sensors for drag-and-drop
	const sensors = useSensors(
		useSensor(PointerSensor),
		useSensor(KeyboardSensor, {
			coordinateGetter: sortableKeyboardCoordinates,
		}),
	)

	// Auto-scroll to bottom when new messages arrive
	useEffect(() => {
		if (chatContainerRef.current) {
			chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
		}
	}, [messages])

	// Fetch groups on mount and set default group
	useEffect(() => {
		const fetchGroupsAndSetDefault = async () => {
			try {
				const response = await listGroups()
				setGroups(response.data.groups)

				// If we have groups, select the first one and load its participants
				if (response.data.groups.length > 0) {
					const defaultGroup = response.data.groups[0]
					setSelectedGroup(defaultGroup.id)

					// Fetch participants for default group
					const groupResponse = await getGroup(defaultGroup.id)
					const groupParticipants = groupResponse.data.participants.map((p: Participant) => ({
						id: p.id,
						name: p.name,
						role: p.role,
						weight: 5,
						persona_description: p.role_overview || "Participant",
					}))
					setParticipants(groupParticipants)
				}
			} catch (error) {
				console.error("Error fetching groups:", error)
				toast.error("Failed to fetch groups")
			}
		}
		fetchGroupsAndSetDefault()
	}, [])

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			cleanupRef.current?.()
		}
	}, [])

	// Fetch questions when moving to next step
	const handleNextFromGroup = async () => {
		if (!selectedGroup || !topic.trim()) return
		try {
			getQuestions(topic, selectedGroup).then((response) => setQuestions(response.data.questions))

			setStep("participants")
		} catch (error) {
			console.error("Error fetching questions:", error)
			toast.error("Failed to fetch questions")
		}
	}

	// Handle drag-and-drop reordering
	const handleDragEnd = (event: DragEndEvent) => {
		const { active, over } = event

		if (active.id !== over?.id) {
			setParticipants((items) => {
				const oldIndex = items.findIndex((item) => item.id === active.id)
				const newIndex = items.findIndex((item) => item.id === over?.id)
				return arrayMove(items, oldIndex, newIndex)
			})
		}
	}

	// Update participant weight
	const updateWeight = (id: string, weight: number) => {
		setParticipants((prev) => prev.map((p) => (p.id === id ? { ...p, weight: Math.max(1, Math.min(10, weight)) } : p)))
	}

	// Handle question selection (max 5)
	const toggleQuestion = (question: string) => {
		setSelectedQuestions((prev) => {
			if (prev.includes(question)) {
				return prev.filter((q) => q !== question)
			} else if (prev.length < 5) {
				return [...prev, question]
			}
			return prev
		})
	}

	const handleBackFromParticipants = () => {
		setStep("group")
	}

	const handleNextFromParticipants = () => {
		if (participants.length > 0) setStep("questions")
	}

	const handleStartChat = async () => {
		if (!selectedGroup || !topic.trim()) return

		setIsLoading(true)
		setMessages([])

		try {
			// Create meeting and get meeting_id
			const response = await createMeeting({
				group_id: selectedGroup,
				strategy: discussionStrategy,
				topic: topic,
				questions: selectedQuestions,
			})
			const meeting_id = response.data.meeting_id

			// Cleanup any existing chat stream
			cleanupRef.current?.()

			// Start streaming chat with meeting_id
			cleanupRef.current = streamChat(meeting_id, {
				onEvent: (
					eventType: ChatEventType,
					data:
						| ParticipantResponse
						| ChatFinalResponse
						| QuestionsResponse
						| ChatErrorResponse
						| NextParticipantResponse,
				) => {
					switch (eventType) {
						case ChatEventType.NextParticipant:
							if ("participant_name" in data && "participant_id" in data) {
								setThinkingParticipant(data.participant_name)
							}
							break
						case ChatEventType.Questions:
							if ("questions" in data) {
								setQuestions(data.questions)
							}
							break
						case ChatEventType.ParticipantResponse:
							if ("participant" in data && "question" in data && "answer" in data) {
								setThinkingParticipant(null)
								const participant = participants.find((p) => p.name === data.participant)
								setMessages((prev) => [
									...prev,
									{
										type: "participant",
										name: data.participant,
										role: participant?.role,
										question: data.question,
										content: data.answer,
										strength: "strength" in data ? data.strength : undefined,
										timestamp: new Date(),
									},
								])
								setThinkingParticipant(null)
							}
							break
						case ChatEventType.FinalResponse:
							if ("response" in data) {
								setMessages((prev) => [
									...prev,
									{
										type: "final",
										content: data.response,
										timestamp: new Date(),
									},
								])
							}
							break
						case ChatEventType.Error:
							if ("detail" in data) {
								console.error("Chat error:", data.detail)
								toast.error(data.detail)
								setIsLoading(false)
							}
							break
						case ChatEventType.Complete:
							setIsLoading(false)
							toast.success("Meeting completed successfully")
							break
					}
				},
			})

			// Automatically move to the chat view
			setStep("chat")
		} catch (error) {
			console.error("Error starting chat:", error)
			toast.error("Failed to start meeting")
			setIsLoading(false)
		}
	}

	return (
		<div className="flex flex-col h-[calc(100vh-2rem)] p-4">
			{step === "group" && (
				<div className="flex flex-col items-center justify-center h-full gap-4">
					<h2 className="text-2xl font-bold">Step 1: Choose Participants</h2>
					<div className="flex flex-col items-start w-[70%]">
						<label className="mb-2 text-lg font-semibold">Participant Group</label>
						<Select value={selectedGroup} onValueChange={handleGroupSelect}>
							<SelectTrigger className="w-full">
								<SelectValue placeholder="Select a Participant Group" />
							</SelectTrigger>
							<SelectContent>
								{groups.map((group) => (
									<SelectItem key={group.id} value={group.id}>
										{group.name || group.id}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
					<div className="flex flex-col items-start w-[70%] mt-4">
						<label className="mb-2 text-lg font-semibold">Discussion Strategy</label>
						<Select value={discussionStrategy} onValueChange={setDiscussionStrategy}>
							<SelectTrigger className="w-full">
								<SelectValue placeholder="Select a Strategy" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="round robin">Round Robin</SelectItem>
								<SelectItem value="opinionated">Opinionated</SelectItem>
							</SelectContent>
						</Select>
					</div>
					<div className="flex flex-col items-start w-[70%] mt-4">
						<label className="mb-2 text-lg font-semibold">Topic</label>
						<Textarea
							placeholder="Enter your message"
							value={topic}
							onChange={(e) => setTopic(e.target.value)}
							className="flex-1 min-h-[60px]"
							rows={4}
						/>
					</div>
					<div className="flex flex-row w-[70%] mt-4">
						<Button
							onClick={handleNextFromGroup}
							disabled={!selectedGroup || !topic.trim()}
							className="text-white bg-blue-500 hover:bg-blue-600">
							Next
						</Button>
					</div>
				</div>
			)}

			{step === "participants" && (
				<div className="flex flex-col items-center justify-center h-full gap-4">
					<h2 className="text-2xl font-bold">Step 2: Order Participants & Assign Weights</h2>
					<DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
						<SortableContext items={participants.map((p) => p.id)} strategy={verticalListSortingStrategy}>
							<ul className="w-[70%] space-y-2">
								{participants.map((participant) => (
									<SortableParticipant
										key={participant.id}
										participant={participant}
										updateWeight={updateWeight}
									/>
								))}
							</ul>
						</SortableContext>
					</DndContext>
					<div className="flex flex-row w-[70%] mt-4 justify-between">
						<Button onClick={handleBackFromParticipants} className="text-white bg-blue-500 hover:bg-blue-600">
							Back
						</Button>
						<Button onClick={handleNextFromParticipants} className="text-white bg-blue-500 hover:bg-blue-600">
							Next
						</Button>
					</div>
				</div>
			)}

			{step === "questions" && (
				<div className="flex flex-col items-center justify-center h-full gap-4">
					<h2 className="text-2xl font-bold">Step 3: Select Questions (Up to 5)</h2>
					<div className="w-[70%] space-y-2">
						{questions.map((question) => (
							<div key={question} className="flex items-center space-x-2">
								<Checkbox
									checked={selectedQuestions.includes(question)}
									onCheckedChange={() => toggleQuestion(question)}
									disabled={!selectedQuestions.includes(question) && selectedQuestions.length >= 5}
								/>
								<span>{question}</span>
							</div>
						))}
					</div>
					<Button
						onClick={handleStartChat}
						disabled={selectedQuestions.length === 0 || isLoading}
						className="text-white bg-blue-500 hover:bg-blue-600">
						{isLoading ? "Starting Meeting..." : "Start Meeting"}
					</Button>
				</div>
			)}

			{step === "chat" && (
				<div className="flex flex-col h-full">
					<Card className="flex flex-col flex-1 border-none">
						<CardContent className="flex flex-col p-0 h-[70vh] overflow-hidden">
							<div ref={chatContainerRef} className="flex-1 overflow-y-auto">
								<div className="p-4 space-y-4">
									{messages.length === 0 && !isLoading && (
										<div className="text-center text-muted-foreground">
											No messages yet. Start the meeting to begin the discussion.
										</div>
									)}
									{messages.map((msg, index) => (
										<ChatMessage key={index} {...msg} />
									))}
									{isLoading && thinkingParticipant && (
										<div className="text-center text-muted-foreground">
											{thinkingParticipant} is thinking...
										</div>
									)}
								</div>
							</div>
						</CardContent>
					</Card>
					<div className="mt-4">
						<Button
							onClick={handleStartChat}
							disabled={isLoading}
							className="text-white bg-blue-500 hover:bg-blue-600">
							Start Meeting
						</Button>
					</div>
				</div>
			)}
		</div>
	)
}

export default NewMeeting
