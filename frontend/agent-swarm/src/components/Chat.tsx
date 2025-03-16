import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { startChat } from "@/lib/api"

const Chat: React.FC<{ chatroomId: string }> = ({ chatroomId }) => {
	const [chatMessage, setChatMessage] = useState("")
	const [chatResponse, setChatResponse] = useState<any>(null)

	const handleStartChat = async () => {
		try {
			const res = await startChat({ chatroom_id: chatroomId, message: chatMessage })
			setChatResponse(res.data)
			setChatMessage("")
		} catch (error) {
			console.error("Error starting chat:", error)
		}
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle>Chat</CardTitle>
			</CardHeader>
			<CardContent className="flex flex-col gap-4">
				<Textarea
					placeholder="Enter your message"
					value={chatMessage}
					onChange={(e) => setChatMessage(e.target.value)}
					disabled={!chatroomId}
				/>
				<Button onClick={handleStartChat} disabled={!chatroomId || !chatMessage}>
					Send Message
				</Button>
				{chatResponse && (
					<div>
						<h3 className="font-semibold">Final Response:</h3>
						<p>{chatResponse.final_response}</p>
						<h3 className="font-semibold mt-4">Discussion Log:</h3>
						{chatResponse.discussion_log.map((log: any, index: number) => (
							<p key={index}>
								<strong>
									{log.name} ({log.step}):
								</strong>{" "}
								{log.response}
							</p>
						))}
					</div>
				)}
			</CardContent>
		</Card>
	)
}

export default Chat
