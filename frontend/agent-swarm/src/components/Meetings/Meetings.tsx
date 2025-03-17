import React, { useState, useEffect } from "react"
import { listMeetings } from "@/lib/api"
import { Meeting} from "@/types/types"

const Meetings: React.FC = () => {
	const [meetings, setMeetings] = useState<Meeting[]>([])

	useEffect(() => {
		listMeetings()
			.then((res) => setMeetings(res.data.meetings))
			.catch((error: Error) => {
				console.error("Failed to fetch Participants:", error)
			})
	}, [])

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">Participants</h1>
			<div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{meetings.map((meeting) => (
					
				))}
			</div>
		</div>
	)
}

export default Meetings
