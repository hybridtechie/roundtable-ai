import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { createParticipant } from "@/lib/api"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"

const CreateParticipant: React.FC = () => {
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
      console.log("Creating participant:", newParticipant)
      await createParticipant(newParticipant)
      setNewParticipant(initialState)
      toast.success("Participant created successfully!")
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
      <Card>
        <CardHeader>
          <CardTitle>New Participant</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
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
              placeholder="Professional background (e.g., 10+ years of experience across architecture, software engineering, and solution design...)"
              value={newParticipant.professional_background}
              onChange={(e) => setNewParticipant({ ...newParticipant, professional_background: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="industry" className="block mb-2 text-sm font-medium">
              Industry Experience
            </label>
            <Textarea
              id="industry"
              placeholder="Industry & domain experience (e.g., Government, Energy, Banking, Systems integration...)"
              value={newParticipant.industry_experience}
              onChange={(e) => setNewParticipant({ ...newParticipant, industry_experience: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="overview" className="block mb-2 text-sm font-medium">
              Role Overview
            </label>
            <Textarea
              id="overview"
              placeholder="Role overview (e.g., Leads high-level architecture and design across large delivery teams...)"
              value={newParticipant.role_overview}
              onChange={(e) => setNewParticipant({ ...newParticipant, role_overview: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="tech" className="block mb-2 text-sm font-medium">
              Technical Stack
            </label>
            <Textarea
              id="tech"
              placeholder="Technical stack & tools (e.g., .NET, Azure, ServiceNow, Neo4j, Python...)"
              value={newParticipant.technical_stack}
              onChange={(e) => setNewParticipant({ ...newParticipant, technical_stack: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="soft" className="block mb-2 text-sm font-medium">
              Soft Skills
            </label>
            <Textarea
              id="soft"
              placeholder="Soft skills (e.g., Highly collaborative, people-first mindset, comfortable leading discussions...)"
              value={newParticipant.soft_skills}
              onChange={(e) => setNewParticipant({ ...newParticipant, soft_skills: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="qualities" className="block mb-2 text-sm font-medium">
              Core Qualities
            </label>
            <Textarea
              id="qualities"
              placeholder="Core qualities (e.g., Technically grounded, empathetic leader, detail-oriented...)"
              value={newParticipant.core_qualities}
              onChange={(e) => setNewParticipant({ ...newParticipant, core_qualities: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="style" className="block mb-2 text-sm font-medium">
              Communication Style
            </label>
            <Textarea
              id="style"
              placeholder="Communication style & preferences (e.g., Clear and structured communication, visual thinker...)"
              value={newParticipant.style_preferences}
              onChange={(e) => setNewParticipant({ ...newParticipant, style_preferences: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="additional" className="block mb-2 text-sm font-medium">
              Additional Information
            </label>
            <Textarea
              id="additional"
              placeholder="Additional information (Optional: Any other relevant details about the participant)"
              value={newParticipant.additional_info}
              onChange={(e) => setNewParticipant({ ...newParticipant, additional_info: e.target.value })}
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
