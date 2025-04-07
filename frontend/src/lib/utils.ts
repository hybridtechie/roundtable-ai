import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Safely encodes markdown content for API transmission
 * This ensures that markdown syntax is preserved but properly encoded
 * to prevent security issues like XSS attacks
 */
export function encodeMarkdownContent(content: string): string {
  if (!content) return ""
  
  // First encode the content to handle special characters
  return encodeURIComponent(content)
}

/**
 * Decodes markdown content received from the API
 */
export function decodeMarkdownContent(content: string): string {
  if (!content) return ""
  
  try {
    return decodeURIComponent(content)
  } catch (error) {
    console.error("Error decoding markdown content:", error)
    return content // Return original content if decoding fails
  }
}
