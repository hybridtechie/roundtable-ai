import React, { useState, useRef, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { streamChat, listChatrooms } from "@/lib/api"
import { Chatroom, AgentResponse, ChatFinalResponse } from "@/types/types"
import { ChatMessage } from "@/components/ui/chat-message"
import { ChatInput } from "@/components/ui/chat-input"

interface ChatMessage {
    type: 'agent' | 'final'
    name?: string
    step?: string
    content: string
    timestamp: Date
}

const Chat: React.FC = () => {
    const [selectedChatroom, setSelectedChatroom] = useState<string>("")
    const [chatrooms, setChatrooms] = useState<Chatroom[]>([])
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

    // Fetch chatrooms on mount
    useEffect(() => {
        const fetchChatrooms = async () => {
            try {
                const response = await listChatrooms()
                console.log('Fetched chatrooms:', response.data.chatrooms)
                setChatrooms(response.data.chatrooms)
            } catch (error) {
                console.error("Error fetching chatrooms:", error)
            }
        }
        fetchChatrooms()
    }, [])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            cleanupRef.current?.()
        }
    }, [])

    const handleStartChat = () => {
        if (!selectedChatroom || !chatMessage.trim()) return
        
        console.log('Starting chat with:', { selectedChatroom, chatMessage })
        setIsLoading(true)
        setMessages([])

        // If there's an existing cleanup function, call it
        if (cleanupRef.current) {
            console.log('Cleaning up previous chat session')
            cleanupRef.current()
        }

        // Store new cleanup function
        cleanupRef.current = streamChat(
            { chatroom_id: selectedChatroom, message: chatMessage },
            {
                onAgentResponse: (response: AgentResponse) => {
                    console.log('Received agent response:', response)
                    if (!response.response || typeof response.response[0] !== 'string') {
                        console.error('Invalid response format:', response)
                        return
                    }
                    setMessages((prev) => {
                        const newMessage: ChatMessage = {
                            type: 'agent',
                            name: response.name,
                            step: response.step,
                            content: response.response[0],
                            timestamp: new Date()
                        }
                        console.log('Adding agent message:', newMessage)
                        return [...prev, newMessage]
                    })
                },
                onFinalResponse: (response: ChatFinalResponse) => {
                    console.log('Received final response:', response)
                    if (!response.response || typeof response.response[0] !== 'string') {
                        console.error('Invalid final response format:', response)
                        return
                    }
                    setMessages((prev) => {
                        const newMessage: ChatMessage = {
                            type: 'final',
                            content: response.response[0],
                            timestamp: new Date()
                        }
                        console.log('Adding final message:', newMessage)
                        return [...prev, newMessage]
                    })
                },
                onError: (error) => {
                    console.error("Chat error:", error)
                    setIsLoading(false)
                },
                onComplete: () => {
                    console.log('Chat session complete')
                    setIsLoading(false)
                    setChatMessage("")
                }
            }
        )
    }

    return (
        <Card className="h-[600px] flex flex-col">
            <CardHeader className="py-4">
                <CardTitle className="flex items-center gap-4">
                    <span>Chat</span>
                    <Select value={selectedChatroom} onValueChange={setSelectedChatroom}>
                        <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Select a chatroom" />
                        </SelectTrigger>
                        <SelectContent>
                            {chatrooms.map((room) => (
                                <SelectItem key={room.id} value={room.id}>
                                    {room.name || room.id}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col flex-1 p-0">
                {/* Chat messages */}
                <div 
                    ref={chatContainerRef}
                    className="flex-1 overflow-y-auto"
                >
                    <div className="p-4 space-y-4">
                        {messages.length === 0 && !isLoading && (
                            <div className="text-center text-muted-foreground">
                                No messages yet. Start a chat to begin the discussion.
                            </div>
                        )}
                        {messages.map((msg, index) => (
                            <ChatMessage key={index} {...msg} />
                        ))}
                        {isLoading && (
                            <div className="text-center text-muted-foreground">
                                Agents are thinking...
                            </div>
                        )}
                    </div>
                </div>

                {/* Chat input */}
                <ChatInput
                    value={chatMessage}
                    onChange={setChatMessage}
                    onSend={handleStartChat}
                    disabled={!selectedChatroom}
                    isLoading={isLoading}
                />
            </CardContent>
        </Card>
    )
}

export default Chat
