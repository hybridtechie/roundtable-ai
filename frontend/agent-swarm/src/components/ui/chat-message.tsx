import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

interface ChatMessageProps {
  type: 'aitwin' | 'final'
  name?: string
  step?: string
  content: string
  timestamp: Date
  className?: string
}

export function ChatMessage({ type, name, step, content, timestamp, className }: ChatMessageProps) {
  const initials = name ? name.split(' ').map(n => n[0]).join('').toUpperCase() : 'AI'
  
  return (
    <div className={cn("flex items-start gap-4 p-4 rounded-lg bg-secondary/50", className)}>
      <Avatar>
        <AvatarFallback className="bg-primary/10">{initials}</AvatarFallback>
      </Avatar>
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold">
            {type === 'aitwin' ? name : 'Final Response'}
          </span>
          {step && (
            <span className="text-sm text-muted-foreground">
              ({step})
            </span>
          )}
        </div>
        <div className="text-sm whitespace-pre-wrap">{content}</div>
        <div className="text-xs text-muted-foreground">
          {timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}