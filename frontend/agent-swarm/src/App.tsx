import { Routes, Route } from "react-router-dom"
import Sidebar from "./components/Sidebar"
import Home from "./components/Home"
import Meetings from "./components/Meetings"
import Participants from "./components/Participants"
import CreateParticipant from "./components/CreateParticipant"
import Chat from "./components/Chat"

function App() {
	return (
		<div className="flex">
			<Sidebar />
			<div className="flex-1">
				<Routes>
					<Route path="/" element={<Home />} />
					<Route path="/meetings" element={<Meetings />} />
					<Route path="/participants" element={<Participants />} />
					<Route path="/participants/create" element={<CreateParticipant />} />
					<Route path="/chat" element={<Chat />} />
				</Routes>
			</div>
		</div>
	)
}

export default App
