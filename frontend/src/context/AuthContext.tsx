import { createContext, useContext, ReactNode } from "react"
import { useAuth0, User } from "@auth0/auth0-react"

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | undefined
  loginWithRedirect: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, user, loginWithRedirect, logout } = useAuth0()

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        loginWithRedirect,
        logout,
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