import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { LogIn } from "lucide-react"

export function LoginButton() {
  const { loginWithRedirect } = useAuth()

  return (
    <Button 
      variant="outline" 
      onClick={() => loginWithRedirect()}
      className="flex items-center gap-2"
    >
      <LogIn className="w-4 h-4" />
      Login with Google
    </Button>
  )
}