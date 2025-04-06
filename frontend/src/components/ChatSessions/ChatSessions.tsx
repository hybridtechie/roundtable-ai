import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { listChatSessions } from "@/lib/api";
import { ChatSession } from "@/types/types";

const ChatSessions: React.FC = () => {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChatSessions = async () => {
      try {
        const response = await listChatSessions();
        // Take only the last 10 sessions, sorted by most recent
        const sortedSessions = response.data.chat_sessions
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 10);
        setChatSessions(sortedSessions);
      } catch (err) {
        setError("Failed to load chat sessions");
        console.error("Error fetching chat sessions:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchChatSessions();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  if (chatSessions.length === 0) {
    return <div className="p-4 text-sm text-muted-foreground">No recent chats</div>;
  }

  return (
    <>
      <div className="px-2 mb-2">
        <h3 className="text-sm font-medium">Recent Chats</h3>
      </div>
      <div className="flex flex-col space-y-1">
        {chatSessions.map((session) => (
          <NavLink
            key={session.id}
            to={`/chat/${session.id}`}
            className={({ isActive }: { isActive: boolean }) =>
              `w-full pl-4 rounded-md ${
                isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"
              }`
            }
          >
            <Button variant="ghost" className="justify-start w-full font-normal truncate">
              {session.title || session.meeting_name || session.meeting_topic || `Chat ${session.id.substring(0, 8)}`}
            </Button>
          </NavLink>
        ))}
      </div>
    </>
  );
};

export default ChatSessions;