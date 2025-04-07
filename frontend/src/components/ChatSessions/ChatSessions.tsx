import React from "react"
import { NavLink } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { useChatSessions } from "@/context/ChatSessionsContext"
import { ChatSession } from "@/types/types"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { ChevronRight } from "lucide-react"

interface GroupedSessions {
  [key: string]: {
    type: 'participant' | 'meeting';
    name: string;
    sessions: ChatSession[];
  }
}

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

  const groupedSessions = chatSessions.reduce<GroupedSessions>((acc, session) => {
    // Check if it's a single participant session
    const isSingleParticipant = session.participants?.length === 1;
    const key = isSingleParticipant
      ? session.participants[0].participant_id
      : (session.meeting_id || 'other');
    
    if (!acc[key]) {
      acc[key] = {
        type: isSingleParticipant ? 'participant' : 'meeting',
        name: isSingleParticipant
          ? session.participants[0].name
          : (session.meeting_name || 'Other Chats'),
        sessions: []
      };
    }
    acc[key].sessions.push(session);
    return acc;
  }, {});

  // Sort sessions within each group by timestamp
  Object.values(groupedSessions).forEach(group => {
    group.sessions.sort((a, b) => (b._ts ?? 0) - (a._ts ?? 0));
  });

  return (
    <>
      <div className="px-2 mb-2">
        <h3 className="text-sm font-medium">Recent Chats</h3>
      </div>
      <div className="flex flex-col space-y-1">
        {Object.entries(groupedSessions)
          .sort(([, a], [, b]) => {
            // Sort by the most recent _ts in each group
            const aLatest = Math.max(...a.sessions.map(s => s._ts ?? 0));
            const bLatest = Math.max(...b.sessions.map(s => s._ts ?? 0));
            return bLatest - aLatest;
          })
          .map(([key, group]) => (
            <Collapsible key={key} defaultOpen className="w-full">
            <CollapsibleTrigger className="flex items-center w-full px-2 py-1 rounded-md hover:bg-accent/30">
              <ChevronRight className="w-4 h-4" />
              <span className="ml-1 text-sm font-medium">
                {group.type === 'participant'
                  ? group.name
                  : (group.name || 'Other Chats')}
              </span>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="flex flex-col mt-1 ml-4 space-y-1">
                {group.sessions.map((session) => (
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
            </CollapsibleContent>
          </Collapsible>
        ))}
      </div>
    </>
  )
}

export default ChatSessions
