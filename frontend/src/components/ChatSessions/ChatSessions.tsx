import React from "react"
import { NavLink } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { useChatSessions } from "@/context/ChatSessionsContext"

const ChatSessions: React.FC = () => {
  const { chatSessions, loading, error } = useChatSessions()

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner size={24} />
      </div>
    )
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>
  }

  if (chatSessions.length === 0) {
    return <div className="p-4 text-sm text-muted-foreground">No recent chats</div>
  }

  return (
    <>
      <div className="px-2 mb-2">
        <h3 className="text-sm font-medium">Recent Chats</h3>
      </div>
      <div className="flex flex-col space-y-1">
        {[...chatSessions].sort((a, b) => (b._ts ?? 0) - (a._ts ?? 0)).map((session) => (
          <NavLink
            key={session.id}
            to={`/chat/${session.meeting_id}/session/${session.id}`}
            className={({ isActive }: { isActive: boolean }) =>
              `w-full pl-4 rounded-md ${isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"}`
            }>
            <Button variant="ghost" className="justify-start w-full font-normal truncate">
              {session.title || session.meeting_name || session.meeting_topic || `Chat ${session.id.substring(0, 8)}`}
            </Button>
          </NavLink>
        ))}
      </div>
    </>
  )
}

export default ChatSessions
