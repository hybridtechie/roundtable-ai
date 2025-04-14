import React, { useState, useEffect } from "react"
import { Card, CardTitle, CardContent, CardDescription, CardHeader } from "@/components/ui/card"
import { useAuth } from "@/context/AuthContext" // Import useAuth
import { Users, MessageSquare, Layers, User, Sparkles } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Dialog } from "@/components/ui/dialog"
import { AISettings } from "@/components/Layout/AISettings" // Import AISettings

const Home: React.FC = () => {
  const { state, isLoading: isAuthLoading } = useAuth() // Use AuthContext state and loading status
  const { user, backendUser, isInitialized } = state // Access llmAccounts via backendUser
  const [showProviderPrompt, setShowProviderPrompt] = useState(false)
  const [showSettingsDialog, setShowSettingsDialog] = useState(false)

  // Determine loading state based on Auth0 loading and backend initialization
  const isLoading = isAuthLoading || !isInitialized

  // Helper function to safely get counts, ensuring a number is returned
  const getSafeCount = (countValue: unknown, arrayValue?: unknown[]): number => {
    if (typeof countValue === "number" && !isNaN(countValue)) {
      return countValue
    }
    if (Array.isArray(arrayValue)) {
      return arrayValue.length
    }
    return 0
  }

  // Safely access counts from backendUser, ensuring they are numbers
  const participantsCount = getSafeCount(backendUser?.participants_count, backendUser?.participants)
  const groupsCount = getSafeCount(backendUser?.groups_count, backendUser?.groups)
  const meetingsCount = getSafeCount(backendUser?.meetings_count, backendUser?.meetings)
  const chatSessionsCount = getSafeCount(undefined, backendUser?.chat_sessions) // Use the array length
  // Access llmAccounts from backendUser
  const currentLlmAccounts = backendUser?.llmAccounts
  const llmProvidersCount = getSafeCount(currentLlmAccounts?.providers?.length, currentLlmAccounts?.providers)

  const dashboardCards = [
    {
      title: "Participants",
      value: participantsCount,
      description: "Total AI participants created",
      icon: <User className="w-8 h-8 text-blue-500" />,
      color: "bg-blue-50",
    },
    {
      title: "Groups",
      value: groupsCount,
      description: "Participant groups created",
      icon: <Users className="w-8 h-8 text-green-500" />,
      color: "bg-green-50",
    },
    {
      title: "Meetings",
      value: meetingsCount,
      description: "Total meetings organized",
      icon: <Layers className="w-8 h-8 text-purple-500" />,
      color: "bg-purple-50",
    },
    {
      title: "Chat Sessions",
      value: chatSessionsCount,
      description: "Active chat sessions",
      icon: <MessageSquare className="w-8 h-8 text-orange-500" />,
      color: "bg-orange-50",
    },
    {
      title: "LLM Providers",
      value: llmProvidersCount,
      description: "Connected AI providers",
      icon: <Sparkles className="w-8 h-8 text-indigo-500" />,
      color: "bg-indigo-50",
    },
  ]

  // Effect to check for LLM providers after loading
  useEffect(() => {
    if (!isLoading && backendUser && llmProvidersCount === 0) {
      // Only show the prompt if the settings dialog isn't already open
      if (!showSettingsDialog) {
        setShowProviderPrompt(true)
      }
    }
    // Reset prompt if providers are added or user navigates away/reloads context
    if (llmProvidersCount > 0) {
      setShowProviderPrompt(false)
    }
  }, [isLoading, backendUser, llmProvidersCount, showSettingsDialog])

  return (
    <div className="p-6">
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-t-2 border-b-2 border-blue-500 rounded-full animate-spin"></div>
        </div>
      ) : !backendUser ? ( // Check if backendUser exists after loading
        <div className="p-4 text-center text-red-500">Failed to load user details from context.</div>
      ) : (
        <>
          <div className="mb-6">
            {/* Use user info from Auth0 user object */}
            <h1 className="text-3xl font-bold text-foreground">Welcome, {user?.name || user?.nickname || "User"}</h1>
            <p className="mt-1 text-gray-500">{user?.email}</p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-5">
            {dashboardCards.map((card, index) => (
              <Card key={index} className="overflow-hidden">
                <CardHeader className="p-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-medium">{card.title}</CardTitle>
                    {card.icon}
                  </div>
                </CardHeader>
                <CardContent className="p-4">
                  <div className="mb-2 text-3xl font-bold">{card.value}</div>
                  <CardDescription>{card.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
      {/* Provider Configuration Prompt Dialog */}
      {showProviderPrompt && (
        <AlertDialog open={showProviderPrompt} onOpenChange={setShowProviderPrompt}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Configure AI Provider?</AlertDialogTitle>
              <AlertDialogDescription>
                You don't have any AI providers configured yet. Would you like to set one up now to enable AI features?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setShowProviderPrompt(false)}>
                No, I am browsing
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  setShowProviderPrompt(false) // Close this dialog
                  setShowSettingsDialog(true) // Open the settings dialog
                }}>
                Let's do it
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {/* AI Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        {/* AISettings includes its own DialogContent */}
        {showSettingsDialog && <AISettings />}
      </Dialog>
    </div>
  )
}

export default Home
