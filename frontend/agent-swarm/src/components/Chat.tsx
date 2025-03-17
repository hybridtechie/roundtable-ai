import React, { useState, useRef, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { streamChat, listMeetings } from "@/lib/api"
import { Meeting, AiTwinResponse, ChatFinalResponse } from "@/types/types"
import { ChatMessage } from "@/components/ui/chat-message"
import { ChatInput } from "@/components/ui/chat-input"

interface ChatMessage {
	type: "aitwin" | "final"
	name?: string
	step?: string
	content: string
	timestamp: Date
}

const Chat: React.FC = () => {
	const [selectedMeeting, setSelectedMeeting] = useState<string>("")
	const [meetings, setMeetings] = useState<Meeting[]>([])
	const [chatMessage, setChatMessage] = useState("")
	const [messages, setMessages] = useState<ChatMessage[]>([])
	const [isLoading, setIsLoading] = useState(false)
	const cleanupRef = useRef<(() => void) | null>(null)
	const chatContainerRef = useRef<HTMLDivElement>(null)

	// Auto-scroll to bottom when new messages arrive
	useEffect(() => {
		if (chatContainerRef.current) {
			chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
		}
	}, [messages])

	// Fetch meetings on mount
	useEffect(() => {
		const fetchMeetings = async () => {
			try {
				const response = await listMeetings()
				console.log("Fetched meetings:", response.data.meetings)
				setMeetings(response.data.meetings)
			} catch (error) {
				console.error("Error fetching meetings:", error)
			}
		}
		fetchMeetings()
	}, [])

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			cleanupRef.current?.()
		}
	}, [])

	const handleStartChat = () => {
		if (!selectedMeeting || !chatMessage.trim()) return

		console.log("Starting chat with:", { selectedMeeting, chatMessage })
		setIsLoading(true)
		setMessages([])

		// If there's an existing cleanup function, call it
		if (cleanupRef.current) {
			console.log("Cleaning up previous chat session")
			cleanupRef.current()
		}

		// Store new cleanup function
		cleanupRef.current = streamChat(
			{ meeting_id: selectedMeeting, message: chatMessage },
			{
				onAiTwinResponse: (response: AiTwinResponse) => {
					console.log("Received AI twin response:", response)
					if (!response.response) {
						console.error("Invalid response format:", response)
						return
					}
					setMessages((prev) => {
						const newMessage: ChatMessage = {
							type: "aitwin",
							name: response.name,
							step: response.step,
							content: response.response,
							timestamp: new Date(),
						}
						console.log("Adding AI twin message:", newMessage)
						return [...prev, newMessage]
					})
				},
				onFinalResponse: (response: ChatFinalResponse) => {
					console.log("Received final response:", response)
					if (!response.response) {
						console.error("Invalid final response format:", response)
						return
					}
					setMessages((prev) => {
						const newMessage: ChatMessage = {
							type: "final",
							content: response.response,
							timestamp: new Date(),
						}
						console.log("Adding final message:", newMessage)
						return [...prev, newMessage]
					})
				},
				onError: (error) => {
					console.error("Chat error:", error)
					setIsLoading(false)
				},
				onComplete: () => {
					console.log("Chat session complete")
					setIsLoading(false)
					setChatMessage("")
				},
			},
		)
	}

	return (
		<div className="flex flex-col h-[calc(100vh-2rem)]">
			<Card className="flex flex-col flex-1">
				<CardHeader className="py-4">
					<CardTitle className="flex items-center gap-4">
						<span>Chat</span>
						<Select value={selectedMeeting} onValueChange={setSelectedMeeting}>
							<SelectTrigger className="w-[200px]">
								<SelectValue placeholder="Select a meeting" />
							</SelectTrigger>
							<SelectContent>
								{meetings.map((meeting) => (
									<SelectItem key={meeting.id} value={meeting.id}>
										{meeting.name || meeting.id}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</CardTitle>
				</CardHeader>
				<CardContent className="flex flex-col p-0 h-[70vh] overflow-hidden">
					{/* Chat messages */}
					<div ref={chatContainerRef} className="flex-1 overflow-y-auto">
						<div className="p-4 space-y-4">
							{messages.length === 0 && !isLoading && (
								<div className="text-center text-muted-foreground">
									No messages yet. Start a chat to begin the discussion.
								</div>
							)}
							{messages.map((msg, index) => (
								<ChatMessage key={index} {...msg} />
							))}
							{isLoading && <div className="text-center text-muted-foreground">AI Twins are thinking...</div>}
						</div>
					</div>
				</CardContent>
			</Card>

			{/* Chat input */}
			<div className="mt-4">
				<ChatInput
					value={chatMessage}
					onChange={setChatMessage}
					onSend={handleStartChat}
					disabled={!selectedMeeting}
					isLoading={isLoading}
				/>
			</div>
		</div>
	)
}

export default Chat
