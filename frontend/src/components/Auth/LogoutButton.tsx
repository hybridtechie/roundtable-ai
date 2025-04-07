import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { LogOut } from "lucide-react"

export function LogoutButton() {
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
  }

  return (
    <Button 
      variant="ghost" 
      onClick={handleLogout}
      className="flex items-center gap-2"
    >
      <LogOut className="w-4 h-4" />
      Sign Out
    </Button>
  )
}