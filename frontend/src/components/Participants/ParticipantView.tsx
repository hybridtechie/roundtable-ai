import React, { useEffect, useState, useCallback } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Participant, ParticipantUpdateData } from "@/types/types"
import { decodeMarkdownContent, encodeMarkdownContent } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { ChevronDown, ChevronUp, ArrowLeft, Save, X, Pencil } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"
import { updateParticipant } from "@/lib/api"

const ParticipantViewPage: React.FC = () => {
  const { participantId } = useParams<{ participantId: string }>()
  const { state, dispatch, isLoading: isAuthLoading } = useAuth()
  const navigate = useNavigate()

  const [participant, setParticipant] = useState<Participant | null>(null)
  const [editedData, setEditedData] = useState<ParticipantUpdateData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isDetailsOpen, setIsDetailsOpen] = useState(false)

  const loadParticipantData = useCallback(() => {
    if (!isAuthLoading && state.isInitialized && participantId) {
      const foundParticipant = state.backendUser?.participants?.find((p) => p.id === participantId)
      if (foundParticipant) {
        setParticipant(foundParticipant)
        setEditedData({
          name: decodeMarkdownContent(foundParticipant.name),
          role: decodeMarkdownContent(foundParticipant.role),
          professional_background: decodeMarkdownContent(foundParticipant.professional_background),
          industry_experience: decodeMarkdownContent(foundParticipant.industry_experience),
          role_overview: decodeMarkdownContent(foundParticipant.role_overview),
          technical_stack: decodeMarkdownContent(foundParticipant.technical_stack),
          soft_skills: decodeMarkdownContent(foundParticipant.soft_skills),
          core_qualities: decodeMarkdownContent(foundParticipant.core_qualities),
          style_preferences: decodeMarkdownContent(foundParticipant.style_preferences),
          additional_info: decodeMarkdownContent(foundParticipant.additional_info),
        })
      } else {
        toast.error("Participant not found.")
      }
      setIsLoading(false)
    } else if (!isAuthLoading && state.isInitialized && !participantId) {
      toast.error("Participant ID is missing.")
      setIsLoading(false)
    }
  }, [participantId, state.backendUser?.participants, isAuthLoading, state.isInitialized])

  useEffect(() => {
    loadParticipantData()
  }, [loadParticipantData])

  const handleInputChange = (field: keyof ParticipantUpdateData, value: string) => {
    // Add explicit type for prev
    setEditedData((prev: ParticipantUpdateData | null) => (prev ? { ...prev, [field]: value } : null))
  }

  const handleEditClick = () => {
    setIsEditing(true)
    setIsDetailsOpen(true)
  }

  const handleCancel = () => {
    setIsEditing(false)
    if (participant) {
      // Reset editedData to original decoded values
      setEditedData({
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
      })
    }
  }

  const handleSave = async () => {
    if (!editedData || !participantId) return
    setIsSaving(true)
    try {
      // Correctly encode all string fields before sending
      const encodedData = Object.keys(editedData).reduce((acc, key) => {
        const fieldKey = key as keyof ParticipantUpdateData
        const value = editedData[fieldKey]
        // Only encode if the value is a string (it should be based on ParticipantUpdateData)
        acc[fieldKey] = typeof value === 'string' ? encodeMarkdownContent(value) : value
        return acc
      }, {} as ParticipantUpdateData) // Initialize accumulator correctly

      // Ensure required fields (if any) are present before sending, though api.ts now accepts Partial
      // Example check (adjust if backend requires specific fields):
      if (!encodedData.name || !encodedData.role) {
         toast.error("Name and Role cannot be empty.");
         setIsSaving(false);
         return;
      }


      const response = await updateParticipant(participantId, encodedData)
      const updatedParticipant: Participant | undefined = response.data

      if (updatedParticipant && updatedParticipant.id) {
        dispatch({ type: "UPDATE_PARTICIPANT", payload: updatedParticipant })
        setParticipant(updatedParticipant)
        setIsEditing(false)
        toast.success("Participant updated successfully!")
        // Re-initialize editedData with new decoded values
        setEditedData({
          name: decodeMarkdownContent(updatedParticipant.name),
          role: decodeMarkdownContent(updatedParticipant.role),
          professional_background: decodeMarkdownContent(updatedParticipant.professional_background),
          industry_experience: decodeMarkdownContent(updatedParticipant.industry_experience),
          role_overview: decodeMarkdownContent(updatedParticipant.role_overview),
          technical_stack: decodeMarkdownContent(updatedParticipant.technical_stack),
          soft_skills: decodeMarkdownContent(updatedParticipant.soft_skills),
          core_qualities: decodeMarkdownContent(updatedParticipant.core_qualities),
          style_preferences: decodeMarkdownContent(updatedParticipant.style_preferences),
          additional_info: decodeMarkdownContent(updatedParticipant.additional_info),
        })
      } else {
        console.error("Update participant response did not contain expected data:", response.data)
        toast.error("Failed to update participant (invalid server response).")
      }
    } catch (error) {
      console.error("Error updating participant:", error)
      toast.error("Failed to update participant.")
    } finally {
      setIsSaving(false)
    }
  }

  const renderField = (
    label: string,
    fieldKey: keyof ParticipantUpdateData,
    isTextarea: boolean = false,
    rows: number = 3,
    minHeightView: string = "min-h-[40px]",
  ) => {
    const value = editedData?.[fieldKey] ?? ""
    const idAndHtmlFor = String(fieldKey) // Ensure fieldKey is string for attributes

    if (isEditing) {
      return (
        <div>
          <label htmlFor={idAndHtmlFor} className="block mb-1 text-sm font-medium">
            {label}
          </label>
          {isTextarea ? (
            <Textarea
              id={idAndHtmlFor}
              rows={rows}
              value={value}
              onChange={(e) => handleInputChange(fieldKey, e.target.value)}
              className="text-sm"
              placeholder={`Enter ${label.toLowerCase()}`}
            />
          ) : (
            <Input
              id={idAndHtmlFor}
              type="text"
              value={value}
              onChange={(e) => handleInputChange(fieldKey, e.target.value)}
              className="text-sm"
              placeholder={`Enter ${label.toLowerCase()}`}
            />
          )}
        </div>
      )
    } else {
      return (
        <div>
          <label className="block mb-1 text-sm font-medium text-muted-foreground">{label}</label>
          <div className={`p-3 text-sm border rounded-md bg-muted ${minHeightView}`}>
            {value || <span className="italic text-gray-500">Not provided</span>}
          </div>
        </div>
      )
    }
  }

  if (isLoading || isAuthLoading || !state.isInitialized) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size={48} />
      </div>
    )
  }

  if (!participant || !editedData) {
    return (
      <div className="p-6 text-center">
        <h1 className="mb-4 text-2xl font-bold">Participant Not Found</h1>
        <Button onClick={() => navigate("/participants")}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Participants
        </Button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl p-6 mx-auto">
      <div className="flex items-center justify-between mb-4">
        <Button variant="outline" size="sm" onClick={() => navigate("/participants")}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Participants
        </Button>
        {!isEditing && (
          <Button variant="outline" size="sm" onClick={handleEditClick}>
            <Pencil className="w-4 h-4 mr-2" /> Edit
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          {isEditing ? (
             renderField("Full Name", "name", false)
          ) : (
            <CardTitle className="text-2xl">{editedData.name}</CardTitle>
          )}
           {isEditing ? (
             renderField("Current Role", "role", false)
          ) : (
            <p className="text-md text-muted-foreground">{editedData.role}</p>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {renderField("Professional Background", "professional_background", true, 5, "min-h-[60px]")}

          <Collapsible open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
            {!isEditing && (
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="flex items-center justify-start w-full p-0 text-sm hover:bg-transparent text-primary">
                  {isDetailsOpen ? <ChevronUp className="w-4 h-4 mr-2" /> : <ChevronDown className="w-4 h-4 mr-2" />}
                  {isDetailsOpen ? "Hide Details" : "Show More Details"}
                </Button>
              </CollapsibleTrigger>
            )}
            <CollapsibleContent className="pt-4 space-y-4">
              {renderField("Industry Experience", "industry_experience", true, 3)}
              {renderField("Role Overview", "role_overview", true, 4, "min-h-[50px]")}
              {renderField("Technical Stack", "technical_stack", true, 3)}
              {renderField("Soft Skills", "soft_skills", true, 3)}
              {renderField("Core Qualities", "core_qualities", true, 3)}
              {renderField("Style Preferences", "style_preferences", true, 3)}
              {renderField("Additional Information", "additional_info", true, 3)}
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
        {isEditing && (
          <CardFooter className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
              <X className="w-4 h-4 mr-2" /> Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving || !editedData.name || !editedData.role}> {/* Disable save if required fields empty */}
              {isSaving ? <LoadingSpinner size={16} className="mr-2" /> : <Save className="w-4 h-4 mr-2" />}
              Save Changes
            </Button>
          </CardFooter>
        )}
      </Card>
    </div>
  )
}

export default ParticipantViewPage