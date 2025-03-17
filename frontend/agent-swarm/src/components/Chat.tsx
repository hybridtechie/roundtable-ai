import React, { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { streamChat, listChatrooms } from "@/lib/api"
import { Chatroom, AgentResponse, ChatFinalResponse } from "@/types/types"

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
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const cleanupRef = useRef<(() => void) | null>(null)
    
    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
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
        if (!selectedChatroom || !chatMessage) return
        
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
            <CardHeader>
                <CardTitle>Chat</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col flex-1 gap-4">
                <div className="flex gap-4">
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
                </div>

                {/* Chat messages */}
                <div className="flex-1 p-4 mb-4 space-y-4 overflow-y-auto border rounded-md bg-background/95">
                    {messages.length === 0 && !isLoading && (
                        <div className="text-center text-muted-foreground">
                            No messages yet. Start a chat to begin the discussion.
                        </div>
                    )}
                    {messages.map((msg, index) => (
                        <div key={index} className="p-3 rounded bg-secondary">
                            {msg.type === 'agent' ? (
                                <div>
                                    <div className="font-semibold">
                                        {msg.name} ({msg.step})
                                    </div>
                                    <div className="mt-1 whitespace-pre-wrap">{msg.content}</div>
                                </div>
                            ) : (
                                <div>
                                    <div className="font-semibold">Final Response</div>
                                    <div className="mt-1 whitespace-pre-wrap">{msg.content}</div>
                                </div>
                            )}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="text-center text-muted-foreground">
                            Agents are thinking...
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Message input */}
                <div className="flex gap-2">
                    <Textarea
                        placeholder="Enter your message"
                        value={chatMessage}
                        onChange={(e) => setChatMessage(e.target.value)}
                        disabled={!selectedChatroom || isLoading}
                        className="flex-1"
                    />
                    <Button 
                        onClick={handleStartChat} 
                        disabled={!selectedChatroom || !chatMessage || isLoading}
                    >
                        {isLoading ? "Chatting..." : "Start Chat"}
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

export default Chat
