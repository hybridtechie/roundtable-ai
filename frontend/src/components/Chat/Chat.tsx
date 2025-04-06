import React, { useRef, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { ChatMessage } from "@/components/ui/chat-message";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { getChatSession } from "@/lib/api";
import { ChatMessage as ChatMessageType } from "@/types/types";

interface DisplayMessage {
  type: "participant" | "final";
  name?: string;
  role?: string;
  content: string;
  timestamp: Date;
}

interface ChatSessionDetails {
  id: string;
  meeting_id: string;
  user_id: string;
  messages: ChatMessageType[];
  participant_id: string;
  meeting_name?: string;
  meeting_topic?: string;
}

const Chat: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string>("");
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchChatSession = async () => {
      if (!sessionId) return;
      
      setIsLoading(true);
      try {
        const response = await getChatSession(sessionId);
        const sessionData = response.data as ChatSessionDetails;
        
        // Set session title from meeting name/topic if available
        if (sessionData.meeting_name || sessionData.meeting_topic) {
          setSessionTitle(sessionData.meeting_name || sessionData.meeting_topic || "");
        }
        
        // Format messages for display
        const formattedMessages = sessionData.messages.map((msg): DisplayMessage => {
          const isUser = msg.role === "user";
          const isAssistant = msg.role === "assistant";
          
          return {
            type: isAssistant ? "participant" : "final",
            name: isAssistant ? sessionData.participant_id : (isUser ? "User" : "System"),
            role: msg.role,
            content: msg.content,
            timestamp: new Date()
          };
        });
        
        setMessages(formattedMessages);
      } catch (err) {
        console.error("Error fetching chat session:", err);
        setError("Failed to load chat session");
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchChatSession();
  }, [sessionId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

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
                  ) : (
                    error ? error : "No messages found in this chat session."
                  )}
                </div>
              )}
              {messages.map((msg, index) => (
                <ChatMessage key={index} {...msg} />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Chat;