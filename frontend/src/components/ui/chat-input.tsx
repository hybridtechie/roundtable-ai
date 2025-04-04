import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

interface ChatInputProps {
	value: string
	onChange: (value: string) => void
	onSend: () => void
	disabled?: boolean
	isLoading?: boolean
}

export function ChatInput({ value, onChange, onSend, disabled, isLoading }: ChatInputProps) {
	const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === "Enter" && !e.shiftKey && !disabled && !isLoading && value.trim()) {
			e.preventDefault()
			onSend()
		}
	}

	return (
		<div className="flex gap-2 p-4 border-t bg-background/95">
			<Textarea
				placeholder="Enter your message"
				value={value}
				onChange={(e) => onChange(e.target.value)}
				onKeyDown={handleKeyPress}
				disabled={disabled || isLoading}
				className="flex-1 min-h-[60px]"
				rows={2}
			/>
			<Button onClick={onSend} disabled={!value.trim() || disabled || isLoading} className="self-end">
				{isLoading ? "Sending..." : "Send"}
			</Button>
		</div>
	)
}
