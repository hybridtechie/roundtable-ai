import { Routes, Route } from "react-router-dom"
import Sidebar from "./components/Sidebar"
import Home from "./components/Home"
import Meetings from "./components/Meetings"
import AiTwins from "./components/AiTwins"
import CreateAiTwin from "./components/CreateAiTwin"
import Chat from "./components/Chat"

function App() {
	return (
		<div className="flex">
			<Sidebar />
			<div className="flex-1">
				<Routes>
					<Route path="/" element={<Home />} />
					<Route path="/meetings" element={<Meetings />} />
					<Route path="/aitwins" element={<AiTwins />} />
					<Route path="/aitwins/create" element={<CreateAiTwin />} />
					<Route path="/chat" element={<Chat />} />
				</Routes>
			</div>
		</div>
	)
}

export default App
