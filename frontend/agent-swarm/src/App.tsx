import { Routes, Route } from "react-router-dom"
import Sidebar from "./components/Sidebar"
import Home from "./components/Home"
import Groups from "./components/Groups"
import Participants from "./components/Participants"
import CreateParticipant from "./components/CreateParticipant"
import Chat from "./components/Meetings"

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
				</Routes>
			</div>
		</div>
	)
}

export default App
