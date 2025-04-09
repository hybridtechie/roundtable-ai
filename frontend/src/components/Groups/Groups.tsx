import React, { useState } from "react" // Removed useEffect
import { useAuth } from "@/context/AuthContext" // Import useAuth
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { ChevronsUpDown, Edit, Trash2 } from "lucide-react"
import { createGroup, updateGroup, deleteGroup } from "@/lib/api" // Removed listParticipants
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Participant, Group } from "@/types/types"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"

const Groups: React.FC = () => {
  // const [groups, setGroups] = useState<Group[]>([]) // Remove local state for groups
  // const [participants, setParticipants] = useState<Participant[]>([]) // Removed local state
  const [selectedParticipantIds, setSelectedParticipantIds] = useState<string[]>([])
  const [groupName, setGroupName] = useState("")
  const [groupDescription, setGroupDescription] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [isLoading, setIsLoading] = useState(false) // Keep for form submission loading
  const { state, dispatch, isLoading: isAuthLoading } = useAuth() // Get state and dispatch
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [editingGroupId, setEditingGroupId] = useState<string | null>(null)
  const [groupToDelete, setGroupToDelete] = useState<Group | null>(null)

  // Derive groups from context state
  const groups: Group[] = (state.backendUser?.groups as Group[]) || []

  // Participants are now derived from AuthContext state below

  const resetForm = () => {
    setSelectedParticipantIds([])
    setGroupName("")
    setGroupDescription("")
    setSearchTerm("")
    setIsEditMode(false)
    setEditingGroupId(null)
    setIsDialogOpen(false)
  }

  const handleEditGroup = (group: Group) => {
    setIsEditMode(true)
    setEditingGroupId(group.id)
    setGroupName(group.name)
    setGroupDescription(group.description || "")

    // Use the same participant resolution logic as in display
    let participantIds: string[] = []
    if (Array.isArray(group.participant_ids)) {
      participantIds = group.participant_ids
    } else if (Array.isArray(group.participants)) {
      participantIds = group.participants.map((p) => p?.id).filter((id): id is string => !!id)
    }

    setSelectedParticipantIds(participantIds)
    setIsDialogOpen(true)
  }

  const handleSubmitGroup = async () => {
    setIsLoading(true)
    try {
      if (isEditMode && editingGroupId) {
        // API should return the updated group object
        // API likely expects only name and participant_ids for update
        const response = await updateGroup(editingGroupId, {
          name: groupName,
          participant_ids: selectedParticipantIds,
        })
        const updatedGroup: Group | undefined = response.data
        if (updatedGroup && updatedGroup.id) {
          dispatch({ type: "UPDATE_GROUP", payload: updatedGroup })
          toast.success("Group updated successfully!")
          resetForm()
        } else {
          console.error("Update group response did not contain group data:", response.data)
          toast.error("Failed to update group (invalid server response).")
        }
      } else {
        // API should return the created group object
        // Remove user_id, backend should get it from auth
        const response = await createGroup({
          name: groupName,
          description: groupDescription,
          participant_ids: selectedParticipantIds,
        })
        const createdGroup: Group | undefined = response.data
        if (createdGroup && createdGroup.id) {
          dispatch({ type: "ADD_GROUP", payload: createdGroup })
          toast.success("Group created successfully!")
          resetForm()
        } else {
          console.error("Create group response did not contain group data:", response.data)
          toast.error("Failed to create group (invalid server response).")
        }
      }
    } catch (error) {
      console.error(`Error ${isEditMode ? "updating" : "creating"} group:`, error)
      toast.error(`Failed to ${isEditMode ? "update" : "create"} group. Please try again.`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteGroup = async () => {
    // Removed unused 'group' parameter
    if (!groupToDelete) return // Check if groupToDelete is set
    setIsLoading(true) // Use isLoading for delete operation as well
    try {
      // API should return { deleted_id: "..." }
      const response = await deleteGroup(groupToDelete.id)
      const deletedId = response.data?.deleted_id

      if (deletedId) {
        dispatch({ type: "DELETE_GROUP", payload: deletedId })
        toast.success(`Group "${groupToDelete.name}" deleted successfully!`)
        setGroupToDelete(null) // Close dialog
      } else {
        console.error("Delete group response did not contain deleted_id:", response.data)
        toast.error(`Failed to delete group "${groupToDelete.name}" (invalid server response).`)
      }
    } catch (error) {
      console.error("Error deleting group:", error)
      toast.error(`Failed to delete group "${groupToDelete.name}". Please try again.`)
      setGroupToDelete(null) // Close dialog even on error
    } finally {
      setIsLoading(false)
    }
  }

  // Derive all participants from context state and create a lookup map
  const allParticipants: Participant[] = state.backendUser?.participants || []
  const participantsMap = new Map(allParticipants.map((p) => [p.id, p]))

  // Filter participants for the creation/edit form based on search term
  const filteredParticipantsForForm = allParticipants.filter((participant) =>
    participant.name.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  // Handle loading state from AuthContext
  if (isAuthLoading || !state.isInitialized) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size={48} />
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="mb-4 text-3xl font-bold">Groups</h1>

      <Dialog
        open={isDialogOpen}
        onOpenChange={(open) => {
          if (!open) resetForm()
          setIsDialogOpen(open)
        }}>
        <DialogTrigger asChild>
          <Button onClick={() => setIsDialogOpen(true)}>Create New Group</Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{isEditMode ? "Edit Group" : "Create Group"}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <div className="mb-4">
              <label htmlFor="groupName" className="block mb-2 text-sm font-medium">
                Group Name
              </label>
              <input
                type="text"
                id="groupName"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                className="w-full p-2 border rounded-md"
                placeholder="Enter group name"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="groupDescription" className="block mb-2 text-sm font-medium">
                Description
              </label>
              <textarea
                id="groupDescription"
                value={groupDescription}
                onChange={(e) => setGroupDescription(e.target.value)}
                className="w-full p-2 border rounded-md"
                placeholder="Enter group description"
                rows={3}
              />
            </div>
            <div className="mb-4">
              <label htmlFor="participantSearch" className="block mb-2 text-sm font-medium">
                Search Participants
              </label>
              <input
                type="text"
                id="participantSearch"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full p-2 border rounded-md"
                placeholder="Search participants..."
              />
            </div>
            <div className="grid gap-2 overflow-y-auto max-h-60">
              {filteredParticipantsForForm.map((participant) => (
                <div key={participant.id} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedParticipantIds.includes(participant.id)}
                    onChange={(e) =>
                      setSelectedParticipantIds(
                        e.target.checked
                          ? [...selectedParticipantIds, participant.id]
                          : selectedParticipantIds.filter((id) => id !== participant.id),
                      )
                    }
                  />
                  <p>{participant.name}</p>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleSubmitGroup} disabled={selectedParticipantIds.length === 0 || !groupName.trim() || isLoading}>
              {isLoading ? (
                <>
                  <LoadingSpinner className="mr-2" size={16} />
                  {isEditMode ? "Updating..." : "Creating..."}
                </>
              ) : isEditMode ? (
                "Update"
              ) : (
                "Create"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!groupToDelete} onOpenChange={(open) => !open && setGroupToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the group "{groupToDelete?.name}" and remove it from our
              servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setGroupToDelete(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (groupToDelete) {
                  // Add null check
                  handleDeleteGroup()
                }
              }}
              disabled={isLoading}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {isLoading ? <LoadingSpinner size={16} className="mr-2" /> : null}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="grid gap-4 mt-4">
        {groups.map((group) => (
          <Collapsible key={group.id} className="w-full">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>{group.name || group.id}</CardTitle>
                  {group.description && <p className="mt-1 text-sm text-gray-500">{group.description}</p>}
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="icon" onClick={() => handleEditGroup(group)}>
                    <Edit className="w-4 h-4" />
                    <span className="sr-only">Edit</span>
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setGroupToDelete(group)}>
                    <Trash2 className="w-4 h-4" />
                    <span className="sr-only">Delete</span>
                  </Button>
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm" className="p-0 w-9">
                      <ChevronsUpDown className="w-4 h-4" />
                      <span className="sr-only">Toggle</span>
                    </Button>
                  </CollapsibleTrigger>
                </div>
              </CardHeader>
              <CollapsibleContent>
                <CardContent>
                  {/* Removed duplicate CardContent tag */}
                  <div className="space-y-2">
                    <div>
                      <p className="mb-2 font-medium">Participants:</p>
                      <ul className="pl-6 space-y-1 list-disc">
                        {(() => {
                          // Determine participant IDs for the current group
                          let participantIds: string[] = []
                          // Use updated Group type which includes optional participant_ids
                          if (Array.isArray(group.participant_ids)) {
                            participantIds = group.participant_ids
                          } else if (Array.isArray(group.participants)) {
                            // Fallback: try to get IDs from the participants array if participant_ids doesn't exist
                            participantIds = group.participants.map((p) => p?.id).filter((id): id is string => !!id)
                          }

                          // Look up full participant details from the map
                          const populatedParticipants = participantIds
                            .map((id) => participantsMap.get(id))
                            .filter((p): p is Participant => !!p) // Filter out undefined results

                          if (populatedParticipants.length === 0) {
                            return <li>No participants assigned or details unavailable.</li>
                          }

                          return populatedParticipants.map((participant) => (
                            <li key={participant.id}>
                              <span className="font-medium">{participant.name}</span>
                              <span className="text-gray-600"> - {participant.role}</span>
                            </li>
                          ))
                        })()}
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>
        ))}
      </div>
    </div>
  )
}

export default Groups
