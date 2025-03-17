import React from "react"
import { NavLink } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { AiFillHome } from "react-icons/ai"
import { TiMessages } from "react-icons/ti";
import { FaMessage } from "react-icons/fa6";
import { FaUser, FaUsers, FaUserPlus } from "react-icons/fa"

const Sidebar: React.FC = () => {
	return (
		<div className="flex flex-col w-64 h-screen gap-2 p-4 bg-gray-100">
			<NavLink to="/" className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
				<Button variant="ghost" className="justify-start w-full">
				<AiFillHome className="mr-2" />
				Home
				</Button>
			</NavLink>
			<div>
				<NavLink
					to="/participants"
					className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
					<Button variant="ghost" className="justify-start w-full">
					<FaUser className="mr-2" />
					Participants
					</Button>
				</NavLink>
				<NavLink
					to="/participants/create"
					className={({ isActive }: { isActive: boolean }) => `w-full pl-4 ${isActive ? "bg-gray-200" : ""}`}>
					<Button variant="ghost" className="justify-start w-full">
					<FaUserPlus className="mr-2" />
					Create Participant
					</Button>
				</NavLink>
			</div>
			<NavLink
				to="/groups"
				className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
				<Button variant="ghost" className="justify-start w-full">
				<FaUsers className="mr-2" />
				Groups
				</Button>
			</NavLink>

			<NavLink to="/meetings" className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
				<Button variant="ghost" className="justify-start w-full">
				<TiMessages className="mr-2" />
				Meetings
				</Button>
			</NavLink>
			<NavLink to="/meetings/new" className={({ isActive }: { isActive: boolean }) => `w-full ${isActive ? "bg-gray-200" : ""}`}>
				<Button variant="ghost" className="justify-start w-full">
				<FaMessage className="mr-2" />
				New Meeting
				</Button>
			</NavLink>
		</div>
	)
}

export default Sidebar
