import React, { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { listParticipants, createMeeting } from "@/lib/api"
import { Participant } from "@/types/types"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "sonner"

const NewChat: React.FC = () => {
  const navigate = useNavigate()
  const [participants, setParticipants] = useState<Participant[]>([])
  const [selectedParticipant, setSelectedParticipant] = useState("")
  const [name, setName] = useState("")
  const [topic, setTopic] = useState("")
  const [loading, setLoading] = useState(false)
  const [loadingParticipants, setLoadingParticipants] = useState(false)

  useEffect(() => {
    const fetchParticipants = async () => {
      setLoadingParticipants(true)
      try {
        const response = await listParticipants()
        setParticipants(response.data.participants)
      } catch (error) {
        console.error("Error fetching participants:", error)
        toast.error("Failed to load participants")
      } finally {
        setLoadingParticipants(false)
      }
    }
    fetchParticipants()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
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
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="participant" className="text-sm font-medium">
                Select Participant
              </label>
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
              <label htmlFor="strategy" className="text-sm font-medium">
                Strategy
              </label>
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
              <label htmlFor="name" className="text-sm font-medium">
                Chat Name
              </label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Enter chat name" required />
            </div>

            <div className="space-y-2">
              <label htmlFor="topic" className="text-sm font-medium">
                Topic
              </label>
              <Input
                id="topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter chat topic"
                required
              />
            </div>

            <Button type="submit" disabled={loading || !selectedParticipant || !name || !topic} className="w-full">
              {loading ? (
                <div className="flex items-center space-x-2">
                  <LoadingSpinner size={20} />
                  <span>Creating chat...</span>
                </div>
              ) : (
                "Start Chat"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default NewChat
