import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible"
import { ChevronsUpDown, CheckCircle, XCircle } from "lucide-react"
import { listParticipants, listGroups, createGroup } from "@/lib/api"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Participant, Group } from "@/types/types"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

const Groups: React.FC = () => {
	const [groups, setGroups] = useState<Group[]>([])
	const [participants, setParticipants] = useState<Participant[]>([])
	const [selectedParticipantIds, setSelectedParticipantIds] = useState<string[]>([])
	const [groupName, setGroupName] = useState("")
	const [groupDescription, setGroupDescription] = useState("")
	const [searchTerm, setSearchTerm] = useState("")
	const [isLoading, setIsLoading] = useState(false)
	const [isDialogOpen, setIsDialogOpen] = useState(false)
	const [toast, setToast] = useState<{ show: boolean; message: string; type: 'success' | 'error' }>({
		show: false,
		message: "",
		type: 'success'
	})

	useEffect(() => {
		listGroups()
			.then((res) => setGroups(res.data.groups))
			.catch(console.error)
		listParticipants()
			.then((res) => setParticipants(res.data.participants))
			.catch(console.error)
	}, [])

	const handleCreateGroup = async () => {
		setIsLoading(true)
		try {
			await createGroup({
				name: groupName,
				description: groupDescription,
				participant_ids: selectedParticipantIds
			})
			const res = await listGroups()
			setGroups(res.data.groups)
			setSelectedParticipantIds([])
			setGroupName("")
			setGroupDescription("")
			setSearchTerm("")
			setIsDialogOpen(false)
			setToast({
				show: true,
				message: "Group created successfully!",
				type: 'success'
			})
			// Auto-hide toast after 3 seconds
			setTimeout(() => {
				setToast(prev => ({ ...prev, show: false }))
			}, 3000)
		} catch (error) {
			console.error("Error creating group:", error)
			setToast({
				show: true,
				message: "Failed to create group. Please try again.",
				type: 'error'
			})
			// Auto-hide toast after 3 seconds
			setTimeout(() => {
				setToast(prev => ({ ...prev, show: false }))
			}, 3000)
		} finally {
			setIsLoading(false)
		}
	}

	// Filter participants based on search term
	const filteredParticipants = participants.filter(participant =>
		participant.name.toLowerCase().includes(searchTerm.toLowerCase())
	)

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">Groups</h1>
			
			{/* Toast Notification */}
			{toast.show && (
				<div className={`fixed top-4 right-4 p-4 rounded-md shadow-md flex items-center gap-2 z-50 ${
					toast.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
				}`}>
					{toast.type === 'success' ? (
						<CheckCircle className="w-5 h-5" />
					) : (
						<XCircle className="w-5 h-5" />
					)}
					<p>{toast.message}</p>
				</div>
			)}
			
			<Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
				<DialogTrigger asChild>
					<Button onClick={() => setIsDialogOpen(true)}>Create New Group</Button>
				</DialogTrigger>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Create Group</DialogTitle>
					</DialogHeader>
					<div className="flex flex-col gap-4">
						<div className="mb-4">
							<label htmlFor="groupName" className="block mb-2 text-sm font-medium">Group Name</label>
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
							<label htmlFor="groupDescription" className="block mb-2 text-sm font-medium">Description</label>
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
							<label htmlFor="participantSearch" className="block mb-2 text-sm font-medium">Search Participants</label>
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
						<Button
							onClick={handleCreateGroup}
							disabled={selectedParticipantIds.length === 0 || !groupName.trim() || isLoading}
						>
							{isLoading ? (
								<>
									<LoadingSpinner className="mr-2" size={16} />
									Creating...
								</>
							) : (
								"Create"
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
			<div className="grid gap-4 mt-4">
				{groups.map((group) => (
					<Collapsible key={group.id} className="w-full">
					  <Card>
					    <CardHeader className="flex flex-row items-center justify-between">
					      <div>
					        <CardTitle>{group.name || group.id}</CardTitle>
					        {group.description && (
					          <p className="mt-1 text-sm text-gray-500">{group.description}</p>
					        )}
					      </div>
					      <CollapsibleTrigger asChild>
					        <Button variant="ghost" size="sm" className="p-0 w-9">
					          <ChevronsUpDown className="w-4 h-4" />
					          <span className="sr-only">Toggle</span>
					        </Button>
					      </CollapsibleTrigger>
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
