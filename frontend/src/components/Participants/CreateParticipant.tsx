import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { createParticipant } from "@/lib/api"
import { encodeMarkdownContent } from "@/lib/utils"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"
import { useAuth } from "@/context/AuthContext" // Import useAuth
import { Participant } from "@/types/types" // Import Participant type
import { useNavigate } from "react-router-dom" // Import useNavigate

const CreateParticipant: React.FC = () => {
  const { dispatch } = useAuth() // Get dispatch from context
  const navigate = useNavigate() // Hook for navigation

  const initialState = {
    name: "",
    role: "",
    professional_background: "",
    industry_experience: "",
    role_overview: "",
    technical_stack: "",
    soft_skills: "",
    core_qualities: "",
    style_preferences: "",
    additional_info: "",
  }

  const [newParticipant, setNewParticipant] = useState(initialState)
  const [isLoading, setIsLoading] = useState(false)

  const handleCreateParticipant = async () => {
    setIsLoading(true)
    try {
      // Encode all text fields to safely handle markdown content
      const encodedParticipantData = {
        name: encodeMarkdownContent(newParticipant.name),
        role: encodeMarkdownContent(newParticipant.role),
        professional_background: encodeMarkdownContent(newParticipant.professional_background),
        industry_experience: encodeMarkdownContent(newParticipant.industry_experience),
        role_overview: encodeMarkdownContent(newParticipant.role_overview),
        technical_stack: encodeMarkdownContent(newParticipant.technical_stack),
        soft_skills: encodeMarkdownContent(newParticipant.soft_skills),
        core_qualities: encodeMarkdownContent(newParticipant.core_qualities),
        style_preferences: encodeMarkdownContent(newParticipant.style_preferences),
        additional_info: encodeMarkdownContent(newParticipant.additional_info),
      }

      console.log("Creating participant with encoded markdown content")
      // API now returns the created participant object directly in response.data
      const response = await createParticipant(encodedParticipantData)

      // The created participant object is directly in response.data
      const createdParticipant: Participant | undefined = response.data

      if (createdParticipant && createdParticipant.id) { // Check if data and ID exist
        // Dispatch action to add participant to global state
        dispatch({ type: "ADD_PARTICIPANT", payload: createdParticipant })
        setNewParticipant(initialState) // Reset form only on success
        toast.success("Participant created successfully!")
        navigate("/participants") // Navigate back to the list view
      } else {
        // Handle case where participant data is not returned as expected
        console.error("Create participant response did not contain expected participant data:", response.data)
        toast.error("Failed to create participant (invalid server response).")
      }

    } catch (error) {
      console.error("Error creating participant:", error)
      toast.error("Failed to create participant. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-6">
      <h1 className="mb-4 text-3xl font-bold">Create Participant</h1>
      <div className="p-3 mb-4 rounded-md bg-muted">
        <p className="text-sm text-muted-foreground">
          <strong>Note:</strong> All fields support markdown formatting. You can use **bold**, *italic*, lists, and other markdown
          syntax to format your content.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>New Participant</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {/* Form fields remain the same */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="name" className="block mb-2 text-sm font-medium">
                Full Name
              </label>
              <Input
                id="name"
                placeholder="Full name"
                value={newParticipant.name}
                onChange={(e) => setNewParticipant({ ...newParticipant, name: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="role" className="block mb-2 text-sm font-medium">
                Current Role
              </label>
              <Input
                id="role"
                placeholder="Current role (e.g., Senior Solutions Architect)"
                value={newParticipant.role}
                onChange={(e) => setNewParticipant({ ...newParticipant, role: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label htmlFor="background" className="block mb-2 text-sm font-medium">
              Professional Background
            </label>
            <Textarea
              id="background"
              placeholder="Professional background (e.g., 10+ years of experience...)"
              value={newParticipant.professional_background}
              onChange={(e) => setNewParticipant({ ...newParticipant, professional_background: e.target.value })}
              rows={5}
            />
          </div>

          <div>
            <label htmlFor="industry" className="block mb-2 text-sm font-medium">
              Industry Experience
            </label>
            <Textarea
              id="industry"
              placeholder="Industry & domain experience (e.g., Government, Energy...)"
              value={newParticipant.industry_experience}
              onChange={(e) => setNewParticipant({ ...newParticipant, industry_experience: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label htmlFor="overview" className="block mb-2 text-sm font-medium">
              Role Overview
            </label>
            <Textarea
              id="overview"
              placeholder="Role overview (e.g., Leads high-level architecture...)"
              value={newParticipant.role_overview}
              onChange={(e) => setNewParticipant({ ...newParticipant, role_overview: e.target.value })}
              rows={4}
            />
          </div>

          <div>
            <label htmlFor="tech" className="block mb-2 text-sm font-medium">
              Technical Stack
            </label>
            <Textarea
              id="tech"
              placeholder="Technical stack & tools (e.g., .NET, Azure...)"
              value={newParticipant.technical_stack}
              onChange={(e) => setNewParticipant({ ...newParticipant, technical_stack: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label htmlFor="soft" className="block mb-2 text-sm font-medium">
              Soft Skills
            </label>
            <Textarea
              id="soft"
              placeholder="Soft skills (e.g., Highly collaborative...)"
              value={newParticipant.soft_skills}
              onChange={(e) => setNewParticipant({ ...newParticipant, soft_skills: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label htmlFor="qualities" className="block mb-2 text-sm font-medium">
              Core Qualities
            </label>
            <Textarea
              id="qualities"
              placeholder="Core qualities (e.g., Technically grounded...)"
              value={newParticipant.core_qualities}
              onChange={(e) => setNewParticipant({ ...newParticipant, core_qualities: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label htmlFor="style" className="block mb-2 text-sm font-medium">
              Communication Style
            </label>
            <Textarea
              id="style"
              placeholder="Communication style & preferences (e.g., Clear and structured...)"
              value={newParticipant.style_preferences}
              onChange={(e) => setNewParticipant({ ...newParticipant, style_preferences: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label htmlFor="additional" className="block mb-2 text-sm font-medium">
              Additional Information
            </label>
            <Textarea
              id="additional"
              placeholder="Additional information (Optional)"
              value={newParticipant.additional_info}
              onChange={(e) => setNewParticipant({ ...newParticipant, additional_info: e.target.value })}
              rows={3}
            />
          </div>

          <Button onClick={handleCreateParticipant} disabled={isLoading}>
            {isLoading ? (
              <>
                <LoadingSpinner className="mr-2" size={16} />
                Creating...
              </>
            ) : (
              "Create Participant"
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

export default CreateParticipant
