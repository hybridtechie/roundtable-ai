import React, { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { streamChat, listChatrooms } from "@/lib/api"
import { Chatroom } from "@/types/types"

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
        setIsLoading(true)
        setMessages([])

        // If there's an existing cleanup function, call it
        cleanupRef.current?.()

        // Store new cleanup function
        cleanupRef.current = streamChat(
            { chatroom_id: selectedChatroom, message: chatMessage },
            {
                onAgentResponse: (response) => {
                    setMessages((prev) => [
                        ...prev,
                        {
                            type: "agent",
                            name: response.name,
                            step: response.step,
                            content: response.response,
                            timestamp: new Date()
                        }
                    ])
                },
                onFinalResponse: (response) => {
                    setMessages((prev) => [
                        ...prev,
                        {
                            type: "final",
                            content: response.response,
                            timestamp: new Date()
                        }
                    ])
                },
                onError: (error) => {
                    console.error("Chat error:", error)
                    setIsLoading(false)
                },
                onComplete: () => {
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
                <div className="flex-1 mb-4 space-y-4 overflow-y-auto">
                    {messages.map((msg, index) => (
                        <div key={index} className="p-3 rounded bg-secondary">
                            {msg.type === 'agent' ? (
                                <div>
                                    <div className="font-semibold">
                                        {msg.name} ({msg.step})
                                    </div>
                                    <div className="mt-1">{msg.content}</div>
                                </div>
                            ) : (
                                <div>
                                    <div className="font-semibold">Final Response</div>
                                    <div className="mt-1">{msg.content}</div>
                                </div>
                            )}
                        </div>
                    ))}
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
