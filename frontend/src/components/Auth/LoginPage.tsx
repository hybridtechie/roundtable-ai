import { LoginButton } from "./LoginButton"
import { useAuth } from "@/context/AuthContext"
import { Navigate } from "react-router-dom"

export function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth() // Remove isInitialized, redirection depends only on isAuthenticated

  // If loading, show a simple loading state
  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  // If authenticated, redirect to the home page immediately.
  // The loading/initialization state while fetching backend data should be handled
  // by the main layout or a protected route component after redirection.
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  // If not authenticated and not loading, show the login page
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background">
      <div className="p-8 border rounded-lg shadow-lg bg-card">
        <h1 className="mb-6 text-2xl font-semibold text-center text-card-foreground">
          Welcome to Roundtable AI
        </h1>
        <LoginButton />
      </div>
    </div>
  )
}