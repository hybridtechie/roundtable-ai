import React from "react"
import { NavLink } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { useChatSessions } from "@/context/ChatSessionsContext"
import { ChatSession } from "@/types/types"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ChevronRight } from "lucide-react"

interface GroupedSessions {
  [key: string]: {
    type: "participant" | "meeting"
    name: string
    sessions: ChatSession[]
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
    const isSingleParticipant = session.participants?.length === 1
    const key = isSingleParticipant ? session.participants[0].participant_id : session.meeting_id || "other"

    if (!acc[key]) {
      acc[key] = {
        type: isSingleParticipant ? "participant" : "meeting",
        name: isSingleParticipant ? session.participants[0].name : session.meeting_name || "Other Chats",
        sessions: [],
      }
    }
    acc[key].sessions.push(session)
    return acc
  }, {})

  // Sort sessions within each group by timestamp
  Object.values(groupedSessions).forEach((group) => {
    group.sessions.sort((a, b) => (b._ts ?? 0) - (a._ts ?? 0))
  })

  // Separate sessions into chats and meetings
  const { chats, meetings } = Object.entries(groupedSessions).reduce(
    (acc, [key, group]) => {
      if (group.type === "participant") {
        acc.chats.push({ key, ...group })
      } else {
        acc.meetings.push({ key, ...group })
      }
      return acc
    },
    { chats: [], meetings: [] } as {
      chats: ((typeof groupedSessions)[string] & { key: string })[]
      meetings: ((typeof groupedSessions)[string] & { key: string })[]
    },
  )

  // Sort by most recent timestamp
  const sortByTimestamp = (items: ((typeof groupedSessions)[string] & { key: string })[]) => {
    return items.sort((a, b) => {
      const aLatest = Math.max(...a.sessions.map((s) => s._ts ?? 0))
      const bLatest = Math.max(...b.sessions.map((s) => s._ts ?? 0))
      return bLatest - aLatest
    })
  }

  return (
    <div className="flex flex-col space-y-4">
      {/* Chats Section */}
      <div>
        <div className="px-2 mb-2">
          <h3 className="text-sm font-medium">Direct Chat</h3>
        </div>
        <div className="flex flex-col space-y-1 max-h-[300px] overflow-y-auto">
          {sortByTimestamp(chats)
            .slice(0, 5)
            .map((group) => (
              <Collapsible key={group.key} defaultOpen={false} className="w-full">
                <CollapsibleTrigger className="flex items-center w-full px-2 py-1 rounded-md hover:bg-accent/30">
                  <ChevronRight className="w-4 h-4" />
                  <span className="ml-1 text-sm font-medium truncate">{group.name}</span>
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
      </div>

      {/* Meetings Section */}
      <div>
        <hr className="my-2 border-gray-200" />
        <div className="px-2 mb-2">
          <h3 className="text-sm font-medium">Groups</h3>
        </div>
        <div className="flex flex-col space-y-1">
          {sortByTimestamp(meetings).map((group) => (
            <Collapsible key={group.key} defaultOpen={false} className="w-full">
              <CollapsibleTrigger className="flex items-center w-full px-2 py-1 rounded-md hover:bg-accent/30">
                <ChevronRight className="w-4 h-4" />
                <span className="ml-1 text-sm font-medium truncate">{group.name}</span>
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
      </div>
    </div>
  )
}

export default ChatSessions
