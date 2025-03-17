import React, { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { listAiTwins } from "@/lib/api"
import { AiTwin } from "@/types/types"

const AiTwins: React.FC = () => {
	const [aitwins, setAiTwins] = useState<AiTwin[]>([])

	useEffect(() => {
		listAiTwins()
			.then((res) => setAiTwins(res.data.aitwins))
			.catch((error: Error) => {
				console.error("Failed to fetch AI twins:", error)
			})
	}, [])

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">AI Twins</h1>
			<div className="grid gap-4">
				{aitwins.map((aitwin) => (
					<Card key={aitwin.id}>
						<CardHeader>
							<CardTitle>{aitwin.name}</CardTitle>
						</CardHeader>
						<CardContent>
							<p>{aitwin.persona_description}</p>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	)
}

export default AiTwins
