import React from "react"
import { NavLink } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { AiFillHome } from "react-icons/ai"
import { TiMessages } from "react-icons/ti"
import { FaMessage } from "react-icons/fa6"
import { FaUser, FaUsers, FaUserPlus } from "react-icons/fa"
import ChatSessions from "@/components/ChatSessions/ChatSessions"

const Sidebar: React.FC = () => {
	return (
		<div className="flex flex-col w-64 h-screen p-4 space-y-2 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<NavLink
				to="/"
				className={({ isActive }: { isActive: boolean }) =>
					`w-full rounded-md ${isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"}`
				}>
				<Button variant="ghost" className="justify-start w-full font-normal">
					<AiFillHome className="w-4 h-4 mr-2" />
					Home
				</Button>
			</NavLink>
			<div>
				<NavLink
					to="/participants"
					className={({ isActive }: { isActive: boolean }) =>
						`w-full rounded-md ${isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"}`
					}>
					<Button variant="ghost" className="justify-start w-full font-normal">
						<FaUser className="w-4 h-4 mr-2" />
						Participants
					</Button>
				</NavLink>
				<NavLink
					to="/participants/create"
					className={({ isActive }: { isActive: boolean }) =>
						`w-full pl-4 rounded-md ${isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"}`
					}>
					<Button variant="ghost" className="justify-start w-full font-normal">
						<FaUserPlus className="w-4 h-4 mr-2" />
						Create Participant
					</Button>
				</NavLink>
			</div>
			<NavLink
				to="/groups"
				className={({ isActive }: { isActive: boolean }) =>
					`w-full rounded-md ${isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"}`
				}>
				<Button variant="ghost" className="justify-start w-full font-normal">
					<FaUsers className="w-4 h-4 mr-2" />
					Groups
				</Button>
			</NavLink>

			<NavLink
				to="/meetings"
				className={({ isActive }: { isActive: boolean }) =>
					`w-full rounded-md ${isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"}`
				}>
				<Button variant="ghost" className="justify-start w-full font-normal">
					<TiMessages className="w-4 h-4 mr-2" />
					Meetings
				</Button>
			</NavLink>
			<NavLink
				to="/meetings/new"
				className={({ isActive }: { isActive: boolean }) =>
					`w-full rounded-md ${isActive ? "bg-accent text-accent-foreground" : "hover:bg-accent/50 transition-colors"}`
				}>
				<Button variant="ghost" className="justify-start w-full font-normal">
					<FaMessage className="w-4 h-4 mr-2" />
					New Meeting
				</Button>
			</NavLink>
		      <hr className="my-2 border-gray-200" />
		      <div>
		        <ChatSessions />
		      </div>
		    </div>
		  )
		}

export default Sidebar
