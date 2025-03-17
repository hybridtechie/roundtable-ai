"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Meeting } from "@/types/types"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

export const columns: ColumnDef<Meeting>[] = [
  {
    accessorKey: "id",
    header: "Meeting ID",
  },
  {
    accessorKey: "topic",
    header: "Topic",
    cell: ({ row }) => {
      const topic = row.getValue("topic") as string
      return topic || "No topic set"
    }
  },
  {
    accessorKey: "participants",
    header: "Participants",
    cell: ({ row }) => {
      const participants = row.getValue("participants") as Meeting["participants"]
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
]