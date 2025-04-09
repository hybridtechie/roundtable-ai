import React, { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { listParticipants, createMeeting, listMeetings } from "@/lib/api"
import { Participant, Meeting } from "@/types/types"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "sonner"

const NewChat: React.FC = () => {
  const navigate = useNavigate()
  const [chatMode, setChatMode] = useState<"new" | "existing">("new")
  const [participants, setParticipants] = useState<Participant[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [selectedParticipant, setSelectedParticipant] = useState("")
  const [selectedMeeting, setSelectedMeeting] = useState("")
  const [name, setName] = useState("")
  const [topic, setTopic] = useState("")
  const [loading, setLoading] = useState(false)
  const [loadingParticipants, setLoadingParticipants] = useState(false)
  const [loadingMeetings, setLoadingMeetings] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      setLoadingParticipants(true)
      setLoadingMeetings(true)
      try {
        const [participantsRes, meetingsRes] = await Promise.all([listParticipants(), listMeetings()])
        setParticipants(participantsRes.data.participants)
        // Filter meetings to only include those without group_ids
        setMeetings(meetingsRes.data.meetings.filter((meeting) => !meeting.group_ids?.length))
      } catch (error) {
        console.error("Error fetching data:", error)
        toast.error("Failed to load required data")
      } finally {
        setLoadingParticipants(false)
        setLoadingMeetings(false)
      }
    }
    fetchData()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (chatMode === "existing") {
        // For existing meetings, navigate directly to chat session
        navigate(`/chat/${selectedMeeting}/session`, { state: { messages: [] } })
        return
      }

      // For new meetings
      const response = await createMeeting({
        participant_id: selectedParticipant,
        name: name,
        topic: topic,
        strategy: "chat",
        questions: [],
        participant_order: [
          {
            participant_id: selectedParticipant,
            weight: 10,
            order: 1,
          },
        ],
      })
      toast.success("Chat meeting created successfully")
      navigate(`/chat/${response.data.meeting_id}/session`, { state: { messages: [] } })
    } catch (error) {
      console.error("Error creating chat:", error)
      toast.error("Failed to create chat meeting")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container p-4 mx-auto">
      <Card>
        <CardContent className="p-6">
          <div className="mb-6">
            <h2 className="mb-4 text-xl font-semibold">Start a Chat</h2>
            <div className="flex mb-4 space-x-2">
              <Button
                type="button"
                variant={chatMode === "new" ? "default" : "outline"}
                onClick={() => setChatMode("new")}
                className="flex-1">
                Create New Chat
              </Button>
              <Button
                type="button"
                variant={chatMode === "existing" ? "default" : "outline"}
                onClick={() => setChatMode("existing")}
                className="flex-1">
                Use Existing Meeting
              </Button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {chatMode === "existing" ? (
              <div className="space-y-2">
                <div className="mb-2 text-sm font-medium">Select Existing Meeting</div>
                <Select value={selectedMeeting} onValueChange={setSelectedMeeting}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={loadingMeetings ? "Loading..." : "Select a meeting"} />
                  </SelectTrigger>
                  <SelectContent>
                    {loadingMeetings ? (
                      <div className="flex justify-center p-2">
                        <LoadingSpinner size={16} />
                      </div>
                    ) : meetings.length > 0 ? (
                      meetings.map((meeting) => (
                        <SelectItem key={meeting.id} value={meeting.id}>
                          {meeting.name} {meeting.topic ? `- ${meeting.topic}` : ""}
                        </SelectItem>
                      ))
                    ) : (
                      <div className="p-2 text-sm text-center text-gray-500">No available meetings found</div>
                    )}
                  </SelectContent>
                </Select>
              </div>
            ) : (
              <>
                <div className="space-y-2">
                  <div className="mb-2 text-sm font-medium">Select Participant</div>
                  <Select value={selectedParticipant} onValueChange={setSelectedParticipant}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder={loadingParticipants ? "Loading..." : "Select a participant"} />
                    </SelectTrigger>
                    <SelectContent>
                      {loadingParticipants ? (
                        <div className="flex justify-center p-2">
                          <LoadingSpinner size={16} />
                        </div>
                      ) : (
                        participants.map((participant) => (
                          <SelectItem key={participant.id} value={participant.id}>
                            {participant.name} - {participant.role}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="mb-2 text-sm font-medium">Strategy</div>
                  <Select value="chat" onValueChange={() => {}}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a strategy" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="chat">Chat</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="mb-2 text-sm font-medium">Chat Name</div>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter chat name"
                    required={chatMode === "new"}
                  />
                </div>

                <div className="space-y-2">
                  <div className="mb-2 text-sm font-medium">Topic</div>
                  <Input
                    id="topic"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Enter chat topic"
                    required={chatMode === "new"}
                  />
                </div>
              </>
            )}

            <Button
              type="submit"
              disabled={loading || (chatMode === "new" ? !selectedParticipant || !name || !topic : !selectedMeeting)}
              className="w-full mt-6">
              {loading ? (
                <div className="flex items-center space-x-2">
                  <LoadingSpinner size={20} />
                  <span>Creating chat...</span>
                </div>
              ) : chatMode === "new" ? (
                "Start New Chat"
              ) : (
                "Join Existing Chat"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default NewChat
