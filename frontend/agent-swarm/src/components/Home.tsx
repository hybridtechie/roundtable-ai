import React, { useState, useEffect } from "react"
import { Card, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { listAiTwins } from "@/lib/api"
import { AiTwin } from "@/types/types"
const Home: React.FC = () => {
	const [aitwins, setAiTwins] = useState<AiTwin[]>([])

	useEffect(() => {
		listAiTwins()
			.then((res) => setAiTwins(res.data.aitwins))
			.catch(console.error)
	}, [])

	return (
		<div className="p-6">
			<h1 className="mb-4 text-3xl font-bold">AI Twins</h1>
			<div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
				{aitwins.map((aitwin) => (
					<Card key={aitwin.id}>
						<div className="flex p-6">
							<Avatar className="h-14 w-14">
								<AvatarFallback>{aitwin.name.charAt(0) + aitwin.name.charAt(1)}</AvatarFallback>
							</Avatar>
							<div className="ml-4">
								<CardTitle className="text-lg">{aitwin.name}</CardTitle>
								<CardDescription>{aitwin.role}</CardDescription>
							</div>
						</div>
						<CardContent>
							{/* Show the first 100 characters of description */}
							<p className="text-sm text-muted-foreground">{aitwin.persona_description.slice(0, 100)}...</p>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	)
}

export default Home
