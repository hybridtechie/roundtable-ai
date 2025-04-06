import { ModeToggle } from "./mode-toggle"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogTrigger } from "@/components/ui/dialog"
import { AISettings } from "./AISettings"

export function NavBar() {
  return (
    <nav className="border-b bg-background">
      <div className="flex items-center h-16 px-4">
        <div className="flex-1">
          <h2 className="mb-4 text-2xl font-bold">Roundtable AI</h2>
        </div>
        <div className="flex items-center space-x-4">
          <Avatar>
            <AvatarImage src="https://github.com/shadcn.png" />
            <AvatarFallback>CN</AvatarFallback>
          </Avatar>
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon">
                <Sparkles className="w-5 h-5" />
              </Button>
            </DialogTrigger>
            <AISettings />
          </Dialog>
          <ModeToggle />
        </div>
      </div>
    </nav>
  )
}
