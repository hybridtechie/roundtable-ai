import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar" // Added AvatarImage
import { Copy, ChevronDown, ChevronUp } from "lucide-react"
import { useState, useEffect } from "react" // Added useEffect
interface ChatMessageProps {
  type?: string
  name?: string
  role?: string
  step?: string
  content?: string
  timestamp?: Date
  className?: string
  forceExpand?: boolean // New prop to control expansion externally
}

const defaultProps: Partial<ChatMessageProps> = {
  type: "participant",
  content: "",
  timestamp: new Date(),
}

export function ChatMessage({
  type = defaultProps.type,
  name,
  role,
  step,
  content = defaultProps.content,
  timestamp = defaultProps.timestamp,
  className,
  forceExpand, // Destructure the new prop
}: ChatMessageProps) {
  const initials = name
    ? name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "AI"
  const [copied, setCopied] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false) // Internal state for individual toggle
  const showFullContent = forceExpand !== undefined ? forceExpand : isExpanded // Prioritize forceExpand prop
  const [userAvatar, setUserAvatar] = useState<string | null>(null)

  useEffect(() => {
    if (name === "You") {
      try {
        const storedUser = localStorage.getItem("user")
        if (storedUser) {
          const user = JSON.parse(storedUser)
          if (user && user.picture) {
            setUserAvatar(user.picture)
          } else {
            setUserAvatar(null) // Reset if picture not found
          }
        } else {
          setUserAvatar(null) // Reset if user not found
        }
      } catch (error) {
        console.error("Error reading user from localStorage:", error)
        setUserAvatar(null) // Reset on error
      }
    } else {
      setUserAvatar(null) // Reset if name is not "You"
    }
  }, [name]) // Re-run effect if name changes

  const handleCopy = async () => {
    if (content) {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className={cn("flex items-start gap-4 p-4 rounded-lg bg-secondary/50 relative group", className)}>
      <Avatar>
        {name === "You" && userAvatar ? <AvatarImage src={userAvatar} alt={name || "User"} /> : null}
        <AvatarFallback className="bg-primary/5">{initials}</AvatarFallback>
      </Avatar>
      <div className="flex-1 space-y-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{type === "participant" || type === "user" ? name : "Final Response"}</span>
            {step && <span className="text-sm text-muted-foreground">({step})</span>}
          </div>
          {role && type === "participant" && <span className="text-sm text-muted-foreground">{role}</span>}
        </div>
        <div
          className={cn(
            "text-sm whitespace-pre-wrap relative",
            type === "final" || (type === "summary" && "text-green-500"),
            !showFullContent && "max-h-[7.5rem] overflow-hidden", // Use combined state
          )}>
          {content || ""}
          {content &&
            !showFullContent &&
            content.split("\n").length > 5 && ( // Use combined state
              <div className="absolute bottom-0 w-full h-8 bg-gradient-to-t from-secondary/50 to-transparent" />
            )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">{timestamp?.toLocaleTimeString()}</div>
          {/* Only show individual toggle if forceExpand is not set */}
          {forceExpand === undefined && content && content.split("\n").length > 5 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary">
              {isExpanded ? (
                <>
                  Show Less <ChevronUp className="w-3 h-3" />
                </>
              ) : (
                <>
                  Show More <ChevronDown className="w-3 h-3" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
      <button
        onClick={handleCopy}
        className="absolute p-2 transition-opacity rounded-md opacity-0 top-2 right-2 group-hover:opacity-100 hover:bg-secondary"
        title="Copy message">
        <Copy className={cn("h-4 w-4", copied ? "text-green-500" : "text-muted-foreground")} />
      </button>
    </div>
  )
}
