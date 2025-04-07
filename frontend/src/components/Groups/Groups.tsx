import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { ChevronsUpDown, Edit, Trash2 } from "lucide-react"
import { listParticipants, listGroups, createGroup, updateGroup, deleteGroup } from "@/lib/api"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog"
import { Participant, Group } from "@/types/types"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { toast } from "@/components/ui/sonner"

const Groups: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([])
  const [participants, setParticipants] = useState<Participant[]>([])
  const [selectedParticipantIds, setSelectedParticipantIds] = useState<string[]>([])
  const [groupName, setGroupName] = useState("")
  const [groupDescription, setGroupDescription] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [editingGroupId, setEditingGroupId] = useState<string | null>(null)
  const [groupToDelete, setGroupToDelete] = useState<Group | null>(null)

  useEffect(() => {
    listGroups()
      .then((res) => setGroups(res.data.groups))
      .catch(console.error)
    listParticipants()
      .then((res) => setParticipants(res.data.participants))
      .catch(console.error)
  }, [])

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
    setSelectedParticipantIds(group.participants.map(p => p.id))
    setIsDialogOpen(true)
  }

  const handleSubmitGroup = async () => {
    setIsLoading(true)
    try {
      if (isEditMode && editingGroupId) {
        await updateGroup(editingGroupId, {
          name: groupName,
          participant_ids: selectedParticipantIds
        })
        toast.success("Group updated successfully!")
      } else {
        await createGroup({
          name: groupName,
          description: groupDescription,
          participant_ids: selectedParticipantIds,
        })
        toast.success("Group created successfully!")
      }
      const res = await listGroups()
      setGroups(res.data.groups)
      resetForm()
    } catch (error) {
      console.error(`Error ${isEditMode ? "updating" : "creating"} group:`, error)
      toast.error(`Failed to ${isEditMode ? "update" : "create"} group. Please try again.`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteGroup = async (group: Group) => {
    try {
      await deleteGroup(group.id)
      const res = await listGroups()
      setGroups(res.data.groups)
      setGroupToDelete(null)
      toast.success("Group deleted successfully!")
    } catch (error) {
      console.error("Error deleting group:", error)
      toast.error("Failed to delete group. Please try again.")
    }
  }

  // Filter participants based on search term
  const filteredParticipants = participants.filter((participant) =>
    participant.name.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="p-6">
      <h1 className="mb-4 text-3xl font-bold">Groups</h1>

      <Dialog open={isDialogOpen} onOpenChange={(open) => {
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
              {filteredParticipants.map((participant) => (
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
              ) : (
                isEditMode ? "Update" : "Create"
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
              This action cannot be undone. This will permanently delete the group
              "{groupToDelete?.name}" and remove it from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setGroupToDelete(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => groupToDelete && handleDeleteGroup(groupToDelete)}>
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
                  <div className="space-y-2">
                    <div>
                      <p className="mb-2 font-medium">Participants:</p>
                      <ul className="pl-6 space-y-1 list-disc">
                        {group.participants.map((participant) => (
                          <li key={participant.id}>
                            <span className="font-medium">{participant.name}</span>
                            <span className="text-gray-600"> - {participant.role}</span>
                          </li>
                        ))}
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
