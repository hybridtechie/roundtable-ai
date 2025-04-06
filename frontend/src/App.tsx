import { Routes, Route } from "react-router-dom"
import Sidebar from "./components/Layout/Sidebar"
import Home from "./components/Home/Home"
import Groups from "./components/Groups/Groups"
import Participants from "./components/Participants/Participants"
import CreateParticipant from "./components/Participants/CreateParticipant"
import Meetings from "./components/Meetings/Meetings"
import NewMeeting from "./components/Meetings/NewMeeting"
import Chat from "./components/Chat/Chat"
import NewChat from "./components/Chat/NewChat"
import { ThemeProvider } from "@/components/theme-provider"
import { NavBar } from "./components/Layout/NavBar"
import { Toaster } from "@/components/ui/sonner"

function App() {
	return (
		<>
			<ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
				<div className="flex flex-col h-screen">
					<NavBar />
					<div className="flex flex-1 overflow-hidden">
						<Sidebar />
						<div className="flex-1 overflow-auto">
							<Routes>
								<Route path="/" element={<Home />} />
								<Route path="/participants" element={<Participants />} />
								<Route path="/participants/create" element={<CreateParticipant />} />
								<Route path="/groups" element={<Groups />} />
								<Route path="/meetings" element={<Meetings />} />
								<Route path="/meetings/new" element={<NewMeeting />} />
								<Route path="/chat/new" element={<NewChat />} />
								<Route path="/chat/:sessionId" element={<Chat />} />
							</Routes>
						</div>
					</div>
				</div>
			</ThemeProvider>
			<Toaster />
		</>
	)
}

export default App
