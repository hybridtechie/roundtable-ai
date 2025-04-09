"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Meeting } from "@/types/types"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Eye, Trash2 } from "lucide-react"
import { LoadingSpinner } from "@/components/ui/loading-spinner" // Import LoadingSpinner
import { FC } from "react"

interface MeetingDetailsDialogProps {
  meeting: Meeting
  open: boolean
  onOpenChange: (open: boolean) => void
}

const MeetingDetailsDialog: FC<MeetingDetailsDialogProps> = ({ meeting, open, onOpenChange }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{meeting.name}</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <div>
          <h4 className="font-medium">Topic</h4>
          <p className="text-sm text-gray-500">{meeting.topic}</p>
        </div>
        <div>
          <h4 className="font-medium">Strategy</h4>
          <p className="text-sm text-gray-500">{meeting.strategy}</p>
        </div>
        <div>
          <h4 className="font-medium">Participants</h4>
          <div className="space-y-2">
            {meeting.participants.map((p) => (
              <div key={p.id} className="flex items-center gap-2">
                <Avatar className="w-8 h-8">
                  <AvatarFallback>{p.name.charAt(0)}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-sm font-medium">{p.name}</p>
                  <p className="text-xs text-gray-500">{p.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>
)

interface ActionsProps {
  meeting: Meeting
  onDelete: (id: string) => void
  onView: (meeting: Meeting) => void
  isDeleting: boolean // Add isDeleting prop
}

const Actions: FC<ActionsProps> = ({ meeting, onDelete, onView, isDeleting }) => (
  <div className="flex gap-2">
    <Button variant="ghost" size="icon" onClick={() => onView(meeting)} className="hover:bg-slate-100">
      <Eye className="w-4 h-4" />
    </Button>
    <Button
      variant="ghost"
      size="icon"
      onClick={() => onDelete(meeting.id)}
      className="hover:bg-red-100 hover:text-red-600"
      disabled={isDeleting} // Disable button when deleting
    >
      {isDeleting ? <LoadingSpinner size={16} /> : <Trash2 className="w-4 h-4" />}
    </Button>
  </div>
)

type ColumnProps = {
  onDelete: (id: string) => void
  onView: (meeting: Meeting) => void
  isDeleting: boolean // Add isDeleting prop here too
}

export const columns = ({ onDelete, onView, isDeleting }: ColumnProps): ColumnDef<Meeting>[] => [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => {
      const name = row.getValue("name") as string
      return name || "Unnamed Meeting"
    },
  },
  {
    accessorKey: "topic",
    header: "Topic",
    cell: ({ row }) => {
      const topic = row.getValue("topic") as string
      return topic || "No topic set"
    },
  },
  {
    accessorKey: "strategy",
    header: "Strategy",
  },
  {
    accessorKey: "participants",
    header: "Participants",
    cell: ({ row }) => {
      // Ensure participants is treated as potentially undefined
      const participants = row.getValue("participants") as Meeting["participants"] | undefined

      // Check if participants is an array and not empty before mapping
      if (!Array.isArray(participants) || participants.length === 0) {
        return <div className="text-xs text-gray-500">No participants</div> // Fallback UI
      }

      // If it's a valid array, map over it
      return (
        <div className="flex -space-x-2">
          {participants.map((participant) => (
            <Avatar key={participant.id} className="w-8 h-8 border-2 border-white">
              <AvatarFallback>{participant.name.charAt(0)}</AvatarFallback>
            </Avatar>
          ))}
        </div>
      )
    },
  },
  {
    id: "actions",
    cell: ({ row }) => <Actions meeting={row.original} onDelete={onDelete} onView={onView} isDeleting={isDeleting} />, // Pass isDeleting to Actions
  },
]

export { MeetingDetailsDialog }
