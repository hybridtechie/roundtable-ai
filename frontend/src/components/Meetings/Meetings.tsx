import React, { useState, useEffect } from "react"
import { listMeetings } from "@/lib/api"
import { Meeting } from "@/types/types"
import { DataTable } from "@/components/ui/data-table"
import { columns } from "./columns"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

const Meetings: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setIsLoading(true)
    setError(null)
    listMeetings()
      .then((res) => {
        setMeetings(res.data.meetings)
        setIsLoading(false)
      })
      .catch((error: Error) => {
        console.error("Failed to fetch Meetings:", error)
        setError("Failed to fetch meetings. Please try again later.")
        setIsLoading(false)
      })
  }, [])

	  return (
	    <div className="p-6">
	      <h1 className="mb-4 text-3xl font-bold">Meetings</h1>
	      <div className="container py-10 mx-auto">
	        {isLoading ? (
	          <div className="flex items-center justify-center h-32">
	            <LoadingSpinner size={32} />
	          </div>
	        ) : error ? (
	          <div className="text-center text-red-500">{error}</div>
	        ) : (
	          <DataTable columns={columns} data={meetings} />
	        )}
	      </div>
	    </div>
	  )
}

export default Meetings
