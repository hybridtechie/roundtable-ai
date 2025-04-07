import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Copy, ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"
interface ChatMessageProps {
  type?: string
  name?: string
  role?: string
  step?: string
  content?: string
  timestamp?: Date
  className?: string
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
}: ChatMessageProps) {
  const initials = name
    ? name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "AI"
  const [copied, setCopied] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

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
            type === "final" && "text-green-500",
            !isExpanded && "max-h-[7.5rem] overflow-hidden", // ~5 lines of text
          )}>
          {content || ""}
          {content && !isExpanded && content.split("\n").length > 5 && (
            <div className="absolute bottom-0 w-full h-8 bg-gradient-to-t from-secondary/50 to-transparent" />
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted-foreground">{timestamp?.toLocaleTimeString()}</div>
          {content && content.split("\n").length > 5 && (
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
