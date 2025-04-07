import React, { useState, useEffect } from "react"
import { Card, CardDescription, CardTitle, CardContent } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Eye, Pencil, Trash2, Plus, Info } from "lucide-react"
import { listParticipants, updateParticipant } from "@/lib/api"
import { Participant } from "@/types/types"
import { useNavigate } from "react-router-dom"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"
import { encodeMarkdownContent, decodeMarkdownContent } from "@/lib/utils"

const Participants: React.FC = () => {
  const navigate = useNavigate()
  const [participants, setParticipants] = useState<Participant[]>([])
  const [selectedParticipant, setSelectedParticipant] = useState<Participant | null>(null)
  const [editedParticipant, setEditedParticipant] = useState<Participant | null>(null)
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    listParticipants()
      .then((res) => {
        // No need to decode here as we'll decode when displaying
        setParticipants(res.data.participants)
      })
      .catch((error: Error) => {
        console.error("Failed to fetch Participants:", error)
      })
  }, [])

  const handleDelete = (participant: Participant) => {
    console.log(`Delete requested for participant: ${participant.name} (${participant.id})`)
    toast.error(`Delete functionality not implemented yet for ${participant.name}`)
  }

  const handleEdit = (participant: Participant) => {
    // Decode markdown content when loading for editing
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
    
    setSelectedParticipant(decodedParticipant)
    setEditedParticipant(decodedParticipant)
    setIsEditDialogOpen(true)
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
          All participant fields support markdown formatting. You can use <strong>bold</strong>, <em>italic</em>,
          lists, and other markdown syntax to format your content.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-1 md:grid-cols-3 lg:grid-cols-4">
        {participants.map((participant) => (
          <Card key={participant.id}>
            <div className="flex p-1">
              <Avatar className="h-14 w-14">
                <AvatarFallback>{participant.name.charAt(0) + participant.name.charAt(1)}</AvatarFallback>
              </Avatar>
              <div className="ml-4">
                <CardTitle className="text-lg">{decodeMarkdownContent(participant.name)}</CardTitle>
                <CardDescription>{decodeMarkdownContent(participant.role)}</CardDescription>
              </div>
            </div>
            <CardContent>
              <p className="mb-4 text-sm text-muted-foreground">
                {decodeMarkdownContent(participant.professional_background)?.slice(0, 100)}...
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
                <Button variant="ghost" size="icon" onClick={() => handleDelete(participant)}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>View Participant</DialogTitle>
          </DialogHeader>
          {selectedParticipant && (
            <div className="grid gap-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input value={decodeMarkdownContent(selectedParticipant.name)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Role</label>
                <Input value={decodeMarkdownContent(selectedParticipant.role)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Professional Background</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.professional_background)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Industry Experience</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.industry_experience)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Role Overview</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.role_overview)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Technical Stack</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.technical_stack)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Soft Skills</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.soft_skills)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Core Qualities</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.core_qualities)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Style Preferences</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.style_preferences)} disabled />
              </div>
              <div>
                <label className="text-sm font-medium">Additional Information</label>
                <Textarea value={decodeMarkdownContent(selectedParticipant.additional_info)} disabled />
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Participant</DialogTitle>
          </DialogHeader>
          {selectedParticipant && (
            <div className="grid gap-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={editedParticipant?.name || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, name: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Role</label>
                <Input
                  value={editedParticipant?.role || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, role: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Professional Background</label>
                <Textarea
                  value={editedParticipant?.professional_background || ""}
                  onChange={(e) =>
                    setEditedParticipant((prev) => (prev ? { ...prev, professional_background: e.target.value } : null))
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Industry Experience</label>
                <Textarea
                  value={editedParticipant?.industry_experience || ""}
                  onChange={(e) =>
                    setEditedParticipant((prev) => (prev ? { ...prev, industry_experience: e.target.value } : null))
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">Role Overview</label>
                <Textarea
                  value={editedParticipant?.role_overview || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, role_overview: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Technical Stack</label>
                <Textarea
                  value={editedParticipant?.technical_stack || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, technical_stack: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Soft Skills</label>
                <Textarea
                  value={editedParticipant?.soft_skills || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, soft_skills: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Core Qualities</label>
                <Textarea
                  value={editedParticipant?.core_qualities || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, core_qualities: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Style Preferences</label>
                <Textarea
                  value={editedParticipant?.style_preferences || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, style_preferences: e.target.value } : null))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Additional Information</label>
                <Textarea
                  value={editedParticipant?.additional_info || ""}
                  onChange={(e) => setEditedParticipant((prev) => (prev ? { ...prev, additional_info: e.target.value } : null))}
                />
              </div>
              <Button
                className="mt-4"
                onClick={async () => {
                  if (!editedParticipant || !selectedParticipant) return
                  setIsLoading(true)
                  try {
                    // Encode all text fields to safely handle markdown content
                    const encodedParticipant = {
                      ...editedParticipant,
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
                      user_id: "roundtable_ai_admin",
                    }
                    
                    await updateParticipant(selectedParticipant.id, encodedParticipant)
                    toast.success("Participant updated successfully")
                    setIsEditDialogOpen(false)
                    // Refresh the participants list
                    const res = await listParticipants()
                    setParticipants(res.data.participants)
                  } catch (error) {
                    console.error("Error updating participant:", error)
                    toast.error("Failed to update participant")
                  } finally {
                    setIsLoading(false)
                  }
                }}
                disabled={isLoading}>
                {isLoading ? (
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
