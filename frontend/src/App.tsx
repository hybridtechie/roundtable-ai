import { Routes, Route, Outlet } from "react-router-dom"
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
import { ChatSessionsProvider } from "./context/ChatSessionsContext"
import { ProtectedRoute } from "./components/Auth/ProtectedRoute"
import { LoginPage } from "./components/Auth/LoginPage" // Import LoginPage

// Layout component including NavBar and Sidebar
const MainLayout = () => (
  <div className="flex flex-col h-screen">
    <NavBar />
    <div className="flex flex-1 overflow-hidden">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <Outlet /> {/* Nested routes will render here */}
      </div>
    </div>
  </div>
)

function App() {
  return (
    <>
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <ChatSessionsProvider>
          <Routes>
            {/* Public Login Route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes with Main Layout */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              {/* Index route for the main layout */}
              <Route index element={<Home />} />
              <Route path="participants" element={<Participants />} />
              <Route path="participants/create" element={<CreateParticipant />} />
              <Route path="groups" element={<Groups />} />
              <Route path="meetings" element={<Meetings />} />
              <Route path="meetings/new" element={<NewMeeting />} />
              <Route path="chat/new" element={<NewChat />} />
              <Route path="chat/:meetingId/session/:sessionId?" element={<Chat />} />
              <Route path="chat/:meetingId/stream" element={<Chat />} />
              {/* Add other protected routes here as needed */}
            </Route>
          </Routes>
        </ChatSessionsProvider>
      </ThemeProvider>
      <Toaster />
    </>
  )
}

export default App
