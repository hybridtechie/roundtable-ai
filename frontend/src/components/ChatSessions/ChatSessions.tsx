import React from "react"
import { NavLink } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { MoreHorizontal } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { deleteChatSession } from "@/lib/api"
import { ChatSession } from "@/types/types"
import { useAuth } from "@/context/AuthContext"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ChevronRight } from "lucide-react"

interface GroupedSessions {
  [key: string]: {
    type: "participant" | "meeting"
    name: string
    sessions: ChatSession[]
  }
}

interface ChatMenuProps {
  sessionId: string
  onDelete: () => void
}

const ChatMenu: React.FC<ChatMenuProps> = ({ onDelete }) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="w-8 h-8 p-0" onClick={(e) => e.preventDefault()}>
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={(e) => {
            e.preventDefault()
            onDelete()
          }}>
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

const ChatSessions: React.FC = () => {
  const { state, dispatch } = useAuth()
  const chatSessions = state.backendUser?.chat_sessions || []
  // Sort sessions by most recent first and take only last 30
  const sortedChatSessions = [...chatSessions]
    .sort((a, b) => b._ts - a._ts) // Use _ts directly for sorting
    .slice(0, 30)

  const handleDelete = async (sessionId: string) => {
    try {
      const response = await deleteChatSession(sessionId)
      // Only update context if deletion was successful
      if (response.data.deleted_id === sessionId) {
        dispatch({ type: "DELETE_CHAT_SESSION", payload: sessionId })
      } else {
        console.error("Delete response ID mismatch:", response.data.deleted_id, sessionId)
      }
    } catch (error) {
      console.error("Failed to delete chat session:", error)
    }
  }

  if (!state.backendUser) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner size={24} />
      </div>
    )
  }

  if (sortedChatSessions.length === 0) {
    return <div className="p-4 text-sm text-muted-foreground">No recent chats</div>
  }

  const groupedSessions = sortedChatSessions.reduce<GroupedSessions>((acc, session) => {
    console.log("Processing session:", {
      id: session.id,
      _ts: session._ts,
      timestamp: new Date(session._ts * 1000).toLocaleString(),
      participants: session.participants?.length,
      meeting_id: session.meeting_id,
      group_name: session.group_name,
      title: session.title,
    })
    // Check if it's a single participant session
    const isSingleParticipant = session.participants?.length === 1
    const key = isSingleParticipant ? session.participants[0].participant_id : session.group_id || "other"

    if (!acc[key]) {
      acc[key] = {
        type: isSingleParticipant ? "participant" : "meeting",
        name: isSingleParticipant ? session.participants[0].name : session.group_name || session.meeting_name || "Other Chats",
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
  console.log("Before categorization - groupedSessions:", groupedSessions)
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
  console.log("After categorization - meetings:", meetings)

  // Sort by most recent timestamp
  console.log("Before sorting - meetings:", meetings)
  const sortByTimestamp = (items: ((typeof groupedSessions)[string] & { key: string })[]) => {
    const sorted = items.sort((a, b) => {
      const aLatest = Math.max(...a.sessions.map((s) => s._ts ?? 0))
      const bLatest = Math.max(...b.sessions.map((s) => s._ts ?? 0))
      console.log("Comparing timestamps:", { a: aLatest, b: bLatest })
      return bLatest - aLatest
    })
    console.log("After sorting:", sorted)
    return sorted
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
                        <div className="flex items-center w-full">
                          <Button variant="ghost" className="justify-start flex-1 font-normal truncate">
                            {session.title ||
                              session.meeting_name ||
                              session.meeting_topic ||
                              `Chat from ${new Date(session._ts * 1000).toLocaleDateString()}` ||
                              `Chat ${session.id.substring(0, 8)}`}
                          </Button>
                          <div className="flex-shrink-0">
                            <ChatMenu sessionId={session.id} onDelete={() => handleDelete(session.id)} />
                          </div>
                        </div>
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
          {sortByTimestamp(meetings).map((group) => {
            console.log("Processing group:", group)
            return (
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
                        <div className="flex items-center w-full">
                          <Button variant="ghost" className="justify-start flex-1 font-normal truncate">
                            {session.title ||
                              session.meeting_topic ||
                              session.meeting_name ||
                              session.group_name ||
                              `Chat from ${new Date(session._ts * 1000).toLocaleDateString()}` ||
                              `Chat ${session.id.substring(0, 8)}`}
                          </Button>
                          <div className="flex-shrink-0">
                            <ChatMenu sessionId={session.id} onDelete={() => handleDelete(session.id)} />
                          </div>
                        </div>
                      </NavLink>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ChatSessions
