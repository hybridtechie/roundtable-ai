import React, { useState, useEffect } from "react"
import { listMeetings } from "@/lib/api"
import { Meeting } from "@/types/types"
import { DataTable } from "@/components/ui/data-table"
import { columns } from "./columns"

const Meetings: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([])

  useEffect(() => {
    listMeetings()
      .then((res) => setMeetings(res.data.meetings))
      .catch((error: Error) => {
        console.error("Failed to fetch Meetings:", error)
      })
  }, [])

  return (
    <div className="p-6">
      <h1 className="mb-4 text-3xl font-bold">Meetings</h1>
      <div className="container py-10 mx-auto">
        <DataTable columns={columns} data={meetings} />
      </div>
    </div>
  )
}

export default Meetings
