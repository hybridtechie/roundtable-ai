import React, { useState } from "react" // Removed useEffect
import { useAuth } from "@/context/AuthContext" // Import useAuth
import { deleteMeeting } from "@/lib/api" // Keep deleteMeeting for now, but remove listMeetings
import { Meeting } from "@/types/types"
import { DataTable } from "@/components/ui/data-table"
import { columns, MeetingDetailsDialog } from "./columns"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"

const Meetings: React.FC = () => {
  // const [meetings, setMeetings] = useState<Meeting[]>([]) // Remove local state
  // const [isLoading, setIsLoading] = useState(true) // Remove local loading state
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const { state, dispatch, isLoading: isAuthLoading } = useAuth(); // Get state, dispatch, and auth loading status
  const [isDeleting, setIsDeleting] = useState(false); // Local state for delete operation loading

  // Remove fetchMeetings and useEffect as data comes from context
  // const fetchMeetings = () => { ... }
  // useEffect(() => { fetchMeetings() }, [])

  // Derive meetings from context state
  const meetings: Meeting[] = (state.backendUser?.meetings as Meeting[]) || [];

  const handleDelete = async (id: string) => {
    setIsDeleting(true); // Start delete loading
    try {
      const response = await deleteMeeting(id); // Call API
      const deletedId = response.data?.deleted_id; // Assuming API returns { deleted_id: "..." }

      if (deletedId) {
        dispatch({ type: "DELETE_MEETING", payload: deletedId }); // Dispatch action to update context state
        toast.success("Meeting deleted successfully");
      } else {
        console.error("Delete meeting response did not contain deleted_id:", response.data);
        toast.error("Failed to delete meeting (invalid server response).");
      }
    } catch (error) {
      console.error("Failed to delete meeting:", error);
      toast.error("Failed to delete meeting. Please try again later.");
    } finally {
      setIsDeleting(false); // Stop delete loading
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
        {isAuthLoading || !state.isInitialized ? ( // Use auth loading state
          <div className="flex items-center justify-center h-screen"> {/* Make spinner centered */}
            <LoadingSpinner size={48} />
          </div>
        ) : (
          <DataTable columns={columns({ onDelete: handleDelete, onView: handleView, isDeleting })} data={meetings} /> )}
      </div>
      {selectedMeeting && <MeetingDetailsDialog meeting={selectedMeeting} open={showDetails} onOpenChange={setShowDetails} />}
    </div>
  )
}

export default Meetings
