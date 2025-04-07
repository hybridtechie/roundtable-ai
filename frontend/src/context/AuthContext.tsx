import { createContext, useContext, ReactNode, useEffect, useState } from "react"
import { useAuth0, User } from "@auth0/auth0-react"
import { login } from "@/lib/api"

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | undefined
  loginWithRedirect: () => void
  logout: () => void
  isInitialized: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, user, loginWithRedirect, logout, getIdTokenClaims } = useAuth0()
  
  const [isInitialized, setIsInitialized] = useState(false)

  // Initialize user data and call login endpoint
  useEffect(() => {
    const initializeUser = async () => {
      if (isAuthenticated && user && !isInitialized) {
        try {
          // Get and store id token
          const idTokenClaims = await getIdTokenClaims()
          const idToken = idTokenClaims?.__raw
          
          if (idToken) {
            localStorage.setItem("idToken", idToken)
            localStorage.setItem("user", JSON.stringify(user))
            
            // Call login endpoint to initialize user in backend
            await login()
            setIsInitialized(true)
          }
        } catch (error) {
          console.error("Error initializing user:", error)
        }
      }
    }
    initializeUser()
  }, [isAuthenticated, user, getIdTokenClaims, isInitialized])

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        loginWithRedirect,
        logout,
        isInitialized,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}