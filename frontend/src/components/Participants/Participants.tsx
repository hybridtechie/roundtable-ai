import React, { useState } from "react"
import { Card, CardDescription, CardTitle, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
// Removed Dialog imports as Edit Dialog is gone
// Removed Input import
// Removed Textarea import
import { Eye, Pencil, Trash2, Plus, Info } from "lucide-react"
import { deleteParticipant } from "@/lib/api" // Removed updateParticipant
import { Participant } from "@/types/types"
import { useNavigate } from "react-router-dom"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"
import { decodeMarkdownContent } from "@/lib/utils" // Removed encodeMarkdownContent
import { useAuth } from "@/context/AuthContext"
// Removed ParticipantView import as it's now a separate page
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog" // Import AlertDialog components

const Participants: React.FC = () => {
  const navigate = useNavigate()
  const { state, dispatch, isLoading: isAuthLoading } = useAuth() // Get dispatch

  // Removed selectedParticipant state
  // Removed editedParticipant state
  const [participantToDelete, setParticipantToDelete] = useState<Participant | null>(null) // State for delete confirmation
  // Removed isViewDialogOpen state
  // Removed isEditDialogOpen state
  // Removed isUpdating state
  const [isDeleting, setIsDeleting] = useState(false) // Loading state for delete

  // Derive participants from context state
  const participants: Participant[] = (state.backendUser?.participants as Participant[]) || []

  // --- Delete Handler ---
  const handleDeleteConfirmation = (participant: Participant) => {
    setParticipantToDelete(participant)
    // AlertDialogTrigger will open the dialog
  }

  const executeDelete = async () => {
    if (!participantToDelete) return

    setIsDeleting(true)
    try {
      // API now returns { deleted_id: "..." }
      const response = await deleteParticipant(participantToDelete.id)
      const deletedId = response.data?.deleted_id

      if (deletedId) {
        dispatch({ type: "DELETE_PARTICIPANT", payload: deletedId })
        toast.success(`Participant "${decodeMarkdownContent(participantToDelete.name)}" deleted successfully!`)
        setParticipantToDelete(null) // Close dialog by resetting state
      } else {
        console.error("Delete participant response did not contain deleted_id:", response.data)
        toast.error(
          `Failed to delete participant "${decodeMarkdownContent(participantToDelete.name)}" (invalid server response).`,
        )
      }
    } catch (error) {
      console.error("Error deleting participant:", error)
      toast.error(`Failed to delete participant "${decodeMarkdownContent(participantToDelete.name)}".`)
    } finally {
      setIsDeleting(false)
    }
  }

  // --- Edit Handler Removed ---
  // --- Update Handler Removed ---

  // Handle loading state
  if (isAuthLoading || !state.isInitialized) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size={48} />
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-3xl font-bold">Participants</h1>
        <Button onClick={() => navigate("create")} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Create New
        </Button>
      </div>

      <div className="flex items-start gap-2 p-3 mb-4 rounded-md bg-muted">
        <Info className="w-5 h-5 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-muted-foreground">
          All participant fields support markdown formatting. You can use <strong>bold</strong>, <em>italic</em>, lists, and other
          markdown syntax to format your content.
        </p>
      </div>

      {participants.length === 0 ? (
        <p className="text-center text-muted-foreground">No participants found. Create one!</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {participants.map((participant) => (
            <Card key={participant.id}>
              <div className="flex items-center p-4">
                <Avatar className="h-14 w-14">
                  <AvatarFallback>
                    {participant.name
                      ? participant.name.charAt(0).toUpperCase() + (participant.name.length > 1 ? participant.name.charAt(1) : "")
                      : "P"}
                  </AvatarFallback>
                </Avatar>
                <div className="ml-4">
                  <CardTitle className="text-lg">{decodeMarkdownContent(participant.name)}</CardTitle>
                  <CardDescription>{decodeMarkdownContent(participant.role)}</CardDescription>
                </div>
              </div>
              <CardContent>
                <p className="mb-4 text-sm text-muted-foreground">
                  {decodeMarkdownContent(participant.professional_background)?.slice(0, 100)}
                  {(decodeMarkdownContent(participant.professional_background)?.length || 0) > 100 ? "..." : ""}
                </p>
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(`/participant/${participant.id}`)} // Navigate to the participant view page
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                  {/* Update Edit button to navigate */}
                  <Button variant="ghost" size="icon" onClick={() => navigate(`/participant/${participant.id}`)}>
                    <Pencil className="w-4 h-4" />
                  </Button>
                  {/* --- Delete Button with Confirmation --- */}
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="ghost" size="icon" onClick={() => handleDeleteConfirmation(participant)}>
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </Button>
                    </AlertDialogTrigger>
                    {/* Render Dialog Content only if participantToDelete matches this participant */}
                    {participantToDelete?.id === participant.id && (
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the participant
                            <strong className="mx-1">{`"${decodeMarkdownContent(participantToDelete.name)}"`}</strong>
                            and remove their data from the server.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel onClick={() => setParticipantToDelete(null)}>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={executeDelete}
                            disabled={isDeleting}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            {isDeleting ? <LoadingSpinner size={16} className="mr-2" /> : null}
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    )}
                  </AlertDialog>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* --- View Dialog Removed --- */}

      {/* --- Edit Dialog Removed --- */}
    </div>
  )
}

export default Participants
