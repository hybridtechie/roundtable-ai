import { Routes, Route } from "react-router-dom"
import Sidebar from "./components/Layout/Sidebar"
import Home from "./components/Home/Home"
import Groups from "./components/Groups/Groups"
import Participants from "./components/Participants/Participants"
import CreateParticipant from "./components/Participants/CreateParticipant"
import Chat from "./components/Meetings/Meetings"
import NewMeeting from "./components/Meetings/NewMeeting"

function App() {
	return (
		<div className="flex">
			<Sidebar />
			<div className="flex-1">
				<Routes>
					<Route path="/" element={<Home />} />
					<Route path="/participants" element={<Participants />} />
					<Route path="/participants/create" element={<CreateParticipant />} />
					<Route path="/groups" element={<Groups />} />
					<Route path="/meetings" element={<Chat />} />
					<Route path="/meetings/new" element={<NewMeeting />} />
				</Routes>
			</div>
		</div>
	)
}

export default App
