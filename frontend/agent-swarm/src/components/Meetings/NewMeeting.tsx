import React, { useState, useRef, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { streamChat, listGroups } from "@/lib/api"
import { Group, ParticipantResponse, ChatFinalResponse } from "@/types/types"
import { ChatMessage } from "@/components/ui/chat-message"
import { ChatInput } from "@/components/ui/chat-input"

interface ChatMessage {
    type: "participant" | "final"
    name?: string
    step?: string
    content: string
    timestamp: Date
}

const NewMeeting: React.FC = () => {
    const [selectedGroup, setSelectedMeeting] = useState<string>("")
    const [groups, setGroups] = useState<Group[]>([])
    const [chatMessage, setChatMessage] = useState("")
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [showChat, setShowChat] = useState(false)
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
        const fetchGroups = async () => {
            try {
                const response = await listGroups()
                console.log("Fetched groups:", response.data.groups)
                setGroups(response.data.groups)
            } catch (error) {
                console.error("Error fetching meetings:", error)
            }
        }
        fetchGroups()
    }, [])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            cleanupRef.current?.()
        }
    }, [])

    const handleStartChat = () => {
        if (!selectedGroup || !chatMessage.trim()) return

        console.log("Starting chat with:", { selectedGroup: selectedGroup, chatMessage })
        setIsLoading(true)
        setMessages([])
        setShowChat(true) // Show chat container when sending message

        if (cleanupRef.current) {
            console.log("Cleaning up previous chat session")
            cleanupRef.current()
        }

        cleanupRef.current = streamChat(
            { group_id: selectedGroup, message: chatMessage },
            {
                onParticipantResponse: (response: ParticipantResponse) => {
                    if (!response.response || typeof response.response[0] !== "string") {
                        console.error("Invalid response format:", response)
                        return
                    }
                    setMessages((prev) => {
                        const newMessage: ChatMessage = {
                            type: "participant",
                            name: response.name,
                            step: response.step,
                            content: response.response[0],
                            timestamp: new Date(),
                        }
                        console.log("Adding Participant message:", newMessage)
                        return [...prev, newMessage]
                    })
                },
                onFinalResponse: (response: ChatFinalResponse) => {
                    console.log("Received final response:", response)
                    if (!response.response || typeof response.response[0] !== "string") {
                        console.error("Invalid final response format:", response)
                        return
                    }
                    setMessages((prev) => {
                        const newMessage: ChatMessage = {
                            type: "final",
                            content: response.response[0],
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
            }
        )
    }

    return (
        <div className="flex flex-col h-[calc(100vh-2rem)]">
            {!showChat ? (
                <div className="flex flex-col items-center justify-center h-full gap-4">
                    <Select value={selectedGroup} onValueChange={setSelectedMeeting}>
                        <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Select a Group" />
                        </SelectTrigger>
                        <SelectContent>
                            {groups.map((group) => (
                                <SelectItem key={group.id} value={group.id}>
                                    {group.name || group.id}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <div className="w-full max-w-md">
                        <ChatInput
                            value={chatMessage}
                            onChange={setChatMessage}
                            onSend={handleStartChat}
                            disabled={!selectedGroup}
                            isLoading={isLoading}
                        />
                    </div>
                </div>
            ) : (
                <>
                    <Select value={selectedGroup} onValueChange={setSelectedMeeting}>
                        <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Select a Group" />
                        </SelectTrigger>
                        <SelectContent>
                            {groups.map((group) => (
                                <SelectItem key={group.id} value={group.id}>
                                    {group.name || group.id}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>

                    <Card className="flex flex-col flex-1 border-none">
                        <CardContent className="flex flex-col p-0 h-[70vh] overflow-hidden">
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
                                    {isLoading && (
                                        <div className="text-center text-muted-foreground">
                                            Participants are thinking...
                                        </div>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <div className="mt-4">
                        <ChatInput
                            value={chatMessage}
                            onChange={setChatMessage}
                            onSend={handleStartChat}
                            disabled={!selectedGroup}
                            isLoading={isLoading}
                        />
                    </div>
                </>
            )}
        </div>
    )
}

export default NewMeeting