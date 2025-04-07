import React, { useState, useEffect } from "react"
import { listMeetings, deleteMeeting } from "@/lib/api"
import { Meeting } from "@/types/types"
import { DataTable } from "@/components/ui/data-table"
import { columns, MeetingDetailsDialog } from "./columns"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"

const Meetings: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  const fetchMeetings = () => {
    setIsLoading(true)
    listMeetings()
      .then((res) => {
        setMeetings(res.data.meetings)
        setIsLoading(false)
      })
      .catch((error: Error) => {
        console.error("Failed to fetch Meetings:", error)
        toast.error("Failed to fetch meetings. Please try again later.")
        setIsLoading(false)
      })
  }

  useEffect(() => {
    fetchMeetings()
  }, [])

  const handleDelete = async (id: string) => {
    try {
      await deleteMeeting(id)
      toast.success("Meeting deleted successfully")
      fetchMeetings()
    } catch (error) {
      console.error("Failed to delete meeting:", error)
      toast.error("Failed to delete meeting. Please try again later.")
    }
  }

  const handleView = (meeting: Meeting) => {
    setSelectedMeeting(meeting)
    setShowDetails(true)
  }

  return (
    <div className="p-6">
      <h1 className="mb-4 text-3xl font-bold">Meetings</h1>
      <div className="container py-10 mx-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <LoadingSpinner size={32} />
          </div>
        ) : (
          <DataTable columns={columns({ onDelete: handleDelete, onView: handleView })} data={meetings} />
        )}
      </div>
      {selectedMeeting && (
        <MeetingDetailsDialog
          meeting={selectedMeeting}
          open={showDetails}
          onOpenChange={setShowDetails}
        />
      )}
    </div>
  )
}

export default Meetings
