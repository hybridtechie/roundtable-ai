import React, { useState } from "react"
import { Card, CardDescription, CardTitle, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Eye, Pencil, Trash2, Plus, Info } from "lucide-react"
import { updateParticipant, deleteParticipant } from "@/lib/api" // Added deleteParticipant
import { Participant } from "@/types/types"
import { useNavigate } from "react-router-dom"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"
import { encodeMarkdownContent, decodeMarkdownContent } from "@/lib/utils"
import { useAuth } from "@/context/AuthContext"
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

  const [selectedParticipant, setSelectedParticipant] = useState<Participant | null>(null)
  const [editedParticipant, setEditedParticipant] = useState<Participant | null>(null)
  const [participantToDelete, setParticipantToDelete] = useState<Participant | null>(null) // State for delete confirmation
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
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

  // --- Edit Handler ---
  const handleEdit = (participant: Participant) => {
    const decodedParticipant = {
      ...participant,
      name: decodeMarkdownContent(participant.name),
      role: decodeMarkdownContent(participant.role),
      professional_background: decodeMarkdownContent(participant.professional_background),
      industry_experience: decodeMarkdownContent(participant.industry_experience),
      role_overview: decodeMarkdownContent(participant.role_overview),
      technical_stack: decodeMarkdownContent(participant.technical_stack),
      soft_skills: decodeMarkdownContent(participant.soft_skills),
      core_qualities: decodeMarkdownContent(participant.core_qualities),
      style_preferences: decodeMarkdownContent(participant.style_preferences),
      additional_info: decodeMarkdownContent(participant.additional_info),
    }
    // Store the original participant (with ID) to know which one to update
    setSelectedParticipant(participant)
    setEditedParticipant(decodedParticipant) // Use decoded for editing form
    setIsEditDialogOpen(true)
  }

  // --- Update Handler (inside Edit Dialog) ---
  const handleUpdate = async () => {
    // Use selectedParticipant.id for the update API call, editedParticipant for data
    if (!editedParticipant || !selectedParticipant?.id) return
    setIsUpdating(true)
    try {
      // Encode all text fields before sending to API
      // Ensure the type matches what updateParticipant expects (likely excluding id/user_id)
      const participantDataToUpdate = {
        name: encodeMarkdownContent(editedParticipant.name),
        role: encodeMarkdownContent(editedParticipant.role),
        professional_background: encodeMarkdownContent(editedParticipant.professional_background),
        industry_experience: encodeMarkdownContent(editedParticipant.industry_experience),
        role_overview: encodeMarkdownContent(editedParticipant.role_overview),
        technical_stack: encodeMarkdownContent(editedParticipant.technical_stack),
        soft_skills: encodeMarkdownContent(editedParticipant.soft_skills),
        core_qualities: encodeMarkdownContent(editedParticipant.core_qualities),
        style_preferences: encodeMarkdownContent(editedParticipant.style_preferences),
        additional_info: encodeMarkdownContent(editedParticipant.additional_info),
      }

      // API now returns the full updated participant object in response.data
      const response = await updateParticipant(selectedParticipant.id, participantDataToUpdate)
      const updatedParticipant: Participant | undefined = response.data

      if (updatedParticipant && updatedParticipant.id) {
        // Dispatch the updated participant data received from the API
        dispatch({ type: "UPDATE_PARTICIPANT", payload: updatedParticipant })
        toast.success("Participant updated successfully")
        setIsEditDialogOpen(false)
        setEditedParticipant(null) // Clear edit state
        setSelectedParticipant(null) // Clear selected state
      } else {
        console.error("Update participant response did not contain expected participant data:", response.data)
        toast.error("Failed to update participant (invalid server response).")
      }
    } catch (error) {
      console.error("Error updating participant:", error)
      toast.error("Failed to update participant")
    } finally {
      setIsUpdating(false)
    }
  }

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
                    onClick={() => {
                      setSelectedParticipant(participant)
                      setIsViewDialogOpen(true)
                    }}>
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => handleEdit(participant)}>
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

      {/* --- View Dialog --- */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>View Participant</DialogTitle>
          </DialogHeader>
          {selectedParticipant && (
            <div className="grid gap-4 py-4">
              {" "}
              {/* Added py-4 */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Name</label>
                <p>{decodeMarkdownContent(selectedParticipant.name)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Role</label>
                <p>{decodeMarkdownContent(selectedParticipant.role)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Professional Background</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[60px]">
                  {decodeMarkdownContent(selectedParticipant.professional_background)}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Industry Experience</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[40px]">
                  {decodeMarkdownContent(selectedParticipant.industry_experience)}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Role Overview</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[50px]">
                  {decodeMarkdownContent(selectedParticipant.role_overview)}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Technical Stack</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[40px]">
                  {decodeMarkdownContent(selectedParticipant.technical_stack)}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Soft Skills</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[40px]">
                  {decodeMarkdownContent(selectedParticipant.soft_skills)}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Core Qualities</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[40px]">
                  {decodeMarkdownContent(selectedParticipant.core_qualities)}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Style Preferences</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[40px]">
                  {decodeMarkdownContent(selectedParticipant.style_preferences)}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Additional Information</label>
                <div className="p-2 mt-1 text-sm border rounded-md bg-muted min-h-[40px]">
                  {decodeMarkdownContent(selectedParticipant.additional_info)}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* --- Edit Dialog --- */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Participant</DialogTitle>
          </DialogHeader>
          {editedParticipant && (
            <div className="grid gap-4 py-4">
              {" "}
              {/* Added py-4 */}
              {/* Form fields remain largely the same, ensure they use editedParticipant state */}
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={editedParticipant.name || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, name: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Role</label>
                <Input
                  value={editedParticipant.role || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, role: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Professional Background</label>
                <Textarea
                  rows={5}
                  value={editedParticipant.professional_background || ""}
                  onChange={(e) =>
                    setEditedParticipant((prev) => (prev ? { ...prev, professional_background: e.target.value } : null))
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Industry Experience</label>
                <Textarea
                  rows={3}
                  value={editedParticipant.industry_experience || ""}
                  onChange={(e) =>
                    setEditedParticipant((prev) => (prev ? { ...prev, industry_experience: e.target.value } : null))
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Role Overview</label>
                <Textarea
                  rows={4}
                  value={editedParticipant.role_overview || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, role_overview: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Technical Stack</label>
                <Textarea
                  rows={3}
                  value={editedParticipant.technical_stack || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, technical_stack: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Soft Skills</label>
                <Textarea
                  rows={3}
                  value={editedParticipant.soft_skills || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, soft_skills: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Core Qualities</label>
                <Textarea
                  rows={3}
                  value={editedParticipant.core_qualities || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, core_qualities: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Style Preferences</label>
                <Textarea
                  rows={3}
                  value={editedParticipant.style_preferences || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, style_preferences: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Additional Information</label>
                <Textarea
                  rows={3}
                  value={editedParticipant.additional_info || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, additional_info: e.target.value } : null))}
                />
              </div>
              {/* Update Button */}
              <Button className="mt-4" onClick={handleUpdate} disabled={isUpdating}>
                {isUpdating ? (
                  <>
                    <LoadingSpinner className="mr-2" size={16} />
                    Updating...
                  </>
                ) : (
                  "Update Participant"
                )}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Participants
