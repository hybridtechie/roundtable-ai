import React, { useRef, useEffect, useState } from "react"
import { useParams, useLocation } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { ChatMessage } from "@/components/ui/chat-message"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { ChatInput } from "@/components/ui/chat-input"
import { getChatSession, sendChatMessage } from "@/lib/api"
import { ChatMessage as ChatMessageType } from "@/types/types"

interface DisplayMessage {
	type?: string
	name?: string
	role?: string
	content: string
	timestamp: Date
}

interface ChatSessionDetails {
	id: string
	meeting_id: string
	user_id: string
	messages: ChatMessageType[]
	display_messages: ChatMessageType[]
	participant_id: string
	meeting_name?: string
	meeting_topic?: string
}

const Chat: React.FC = () => {
	const { sessionId } = useParams<{ sessionId: string }>()
	const location = useLocation()
	const meetingId = location.state?.meetingId
	const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId)
	const [messages, setMessages] = useState<DisplayMessage[]>([])
	const [isLoading, setIsLoading] = useState(true)
	const [inputValue, setInputValue] = useState("")
	const [isSending, setIsSending] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [sessionTitle, setSessionTitle] = useState<string>("")
	const chatContainerRef = useRef<HTMLDivElement>(null)

	useEffect(() => {
		const fetchChatSession = async () => {
			if (!currentSessionId && !meetingId) return

			setIsLoading(true)
			try {
				if (currentSessionId) {
					const response = await getChatSession(currentSessionId)
					const sessionData = response.data as ChatSessionDetails

					// Set session title from meeting name/topic if available
					if (sessionData.meeting_name || sessionData.meeting_topic) {
						setSessionTitle(sessionData.meeting_name || sessionData.meeting_topic || "")
					}

					// Format messages for display
					const formattedMessages = sessionData.display_messages.map((msg): DisplayMessage => {
						return {
							type: msg.type,
							name: msg.name,
							role: msg.role,
							content: msg.content,
							timestamp: new Date(),
						}
					})

					setMessages(formattedMessages)
				}
			} catch (err) {
				console.error("Error fetching chat session:", err)
				setError("Failed to load chat session")
			} finally {
				setIsLoading(false)
			}
		}

		fetchChatSession()
	}, [currentSessionId, meetingId]) // Re-fetch when either sessionId or meetingId changes

	// Scroll to bottom when messages change
	useEffect(() => {
		if (chatContainerRef.current) {
			chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
		}
	}, [messages])

	const handleSendMessage = async () => {
		if (!inputValue.trim()) return

		// If we have a sessionId use it, otherwise use meetingId
		const id = currentSessionId || meetingId
		if (!id) return

		setIsSending(true)
		try {
			const response = await sendChatMessage(id, inputValue, currentSessionId)

			// If this is first message in a new chat, store the session ID
			if (!currentSessionId) {
				setCurrentSessionId(response.data.session_id)
			}

			// Add the user's message and the response to the messages
			const newMessages: DisplayMessage[] = [
				{
					type: "user",
					name: "You",
					content: inputValue,
					timestamp: new Date(),
				},
				{
					type: "assistant",
					name: "Assistant",
					content: response.data.response,
					timestamp: new Date(),
				},
			]

			setMessages((prev) => [...prev, ...newMessages])
			setInputValue("")
		} catch (error) {
			console.error("Error sending message:", error)
			setError("Failed to send message")
		} finally {
			setIsSending(false)
		}
	}

	return (
		<div className="flex flex-col h-full">
			{sessionTitle && (
				<div className="p-4 pb-0">
					<h2 className="text-xl font-semibold">{sessionTitle}</h2>
				</div>
			)}
			<Card className="flex flex-col flex-1 border-none">
				<CardContent className="flex flex-col p-0 h-[70vh] overflow-hidden">
					<div ref={chatContainerRef} className="flex-1 overflow-y-auto">
						<div className="p-4 space-y-4">
							{messages.length === 0 && (
								<div className="text-center text-muted-foreground">
									{isLoading ? (
										<div className="flex flex-col items-center gap-2">
											<LoadingSpinner />
											<span>Loading messages...</span>
										</div>
									) : error ? (
										error
									) : (
										"No messages found in this chat session."
									)}
								</div>
							)}
							{messages.map((msg, index) => (
								<ChatMessage key={index} {...msg} />
							))}
						</div>
					</div>
				</CardContent>
				<ChatInput
					value={inputValue}
					onChange={setInputValue}
					onSend={handleSendMessage}
					disabled={isLoading || !!error}
					isLoading={isSending}
				/>
			</Card>
		</div>
	)
}

export default Chat
