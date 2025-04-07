import { useAuth } from "@/context/AuthContext"
import { LoginButton } from "./LoginButton"
import { UserProfile } from "./UserProfile"
import { Skeleton } from "@/components/ui/skeleton"

export function AuthStatus() {
  const { isLoading, isAuthenticated } = useAuth()

  if (isLoading) {
    return <Skeleton className="w-10 h-10 rounded-full" />
  }

  return isAuthenticated ? <UserProfile /> : <LoginButton />
}