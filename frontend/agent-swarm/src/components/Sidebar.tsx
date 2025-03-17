import React from "react"
import { NavLink } from "react-router-dom"
import { Button } from "@/components/ui/button"

const Sidebar: React.FC = () => {
	return (
		<div className="flex flex-col w-64 h-screen gap-2 p-4 bg-gray-100">
			<h2 className="mb-4 text-2xl font-bold">AiTwin Swarm</h2>
			<NavLink to="/" className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
				<Button variant="ghost" className="justify-start w-full">
					Home
				</Button>
			</NavLink>
			<NavLink
				to="/meetings"
				className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
				<Button variant="ghost" className="justify-start w-full">
					Meetings
				</Button>
			</NavLink>
			<div>
				<NavLink
					to="/aitwins"
					className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
					<Button variant="ghost" className="justify-start w-full">
						AiTwins
					</Button>
				</NavLink>
				<NavLink
					to="/aitwins/create"
					className={({ isActive }: { isActive: boolean }) => `w-full pl-4 ${isActive ? "bg-gray-200" : ""}`}>
					<Button variant="ghost" className="justify-start w-full">
						Create AiTwin
					</Button>
				</NavLink>
			</div>
			<NavLink to="/chat" className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
				<Button variant="ghost" className="justify-start w-full">
					Chat
				</Button>
			</NavLink>
		</div>
	)
}

export default Sidebar
