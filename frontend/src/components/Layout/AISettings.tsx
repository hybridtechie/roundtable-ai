import { LoadingSpinner } from "@/components/ui/loading-spinner"
import {
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useState } from "react"
import { toast } from "@/components/ui/sonner"

import { LLMAccountCreate, LLMAccountsResponse, createLLMAccount, deleteLLMAccount, listLLMAccounts, setDefaultProvider } from "@/lib/api"
import { useEffect } from "react"
import { Star, StarOff, Trash2 } from "lucide-react"

export function AISettings() {
  const [accounts, setAccounts] = useState<LLMAccountsResponse>({
    default: "",
    providers: []
  })
  const [isLoading, setIsLoading] = useState(true)

  const [newProvider, setNewProvider] = useState<LLMAccountCreate>({
    provider: "AzureOpenAI",
    model: "",
    api_key: "",
    deployment_name: "",
    endpoint: "",
    api_version: ""
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    setIsLoading(true)
    try {
      const response = await listLLMAccounts()
      if (response.data) {
        setAccounts({
          default: response.data.default || "",
          providers: response.data.providers || []
        })
      }
    } catch (error) {
      console.error("Failed to load LLM accounts:", error)
      toast.error("Failed to load LLM accounts")
    }
    setIsLoading(false)
  }

  const handleAddProvider = async () => {
    try {
      await createLLMAccount(newProvider)
      await loadAccounts()
      setNewProvider({
        provider: "AzureOpenAI",
        model: "",
        api_key: "",
        deployment_name: "",
        endpoint: "",
        api_version: ""
      })
      toast.success("Provider added successfully")
    } catch {
      toast.error("Failed to add provider")
    }
  }

  const handleSetDefault = async (provider: string) => {
    try {
      await setDefaultProvider(provider)
      await loadAccounts()
      toast.success("Default provider updated")
    } catch {
      toast.error("Failed to set default provider")
    }
  }

  const handleDeleteProvider = async (provider: string) => {
    try {
      await deleteLLMAccount(provider)
      await loadAccounts()
      toast.success("Provider deleted successfully")
    } catch {
      toast.error("Failed to delete provider")
    }
  }

  return (
    <DialogContent className="sm:max-w-[550px] p-4">
      <DialogHeader>
        <DialogTitle>AI Provider Settings</DialogTitle>
      </DialogHeader>

      <div className="grid gap-4">
        <div className="space-y-4">
          <h3 className="font-medium">Add New Provider</h3>
          <div className="grid gap-4">
            <div className="w-full">
              <Select
                value={newProvider.provider}
                onValueChange={(value) =>
                  setNewProvider(prev => ({ ...prev, provider: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {["AzureOpenAI", "Grok", "OpenAI", "Deepseek", "OpenRouter", "Gemini"].filter(
                    provider => !accounts.providers.some(p => p.provider === provider)
                  ).map(provider => (
                    <SelectItem key={provider} value={provider}>
                      {provider.replace(/([A-Z])/g, ' $1').trim()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-full">
              <Input
                placeholder="Model name"
                value={newProvider.model}
                onChange={(e) =>
                  setNewProvider(prev => ({ ...prev, model: e.target.value }))
                }
              />
            </div>

            {/* Azure OpenAI requires all fields */}
            {newProvider.provider === "AzureOpenAI" && (
              <>
                <div className="w-full">
                  <Input
                    placeholder="Deployment name"
                    value={newProvider.deployment_name || ""}
                    onChange={(e) =>
                      setNewProvider(prev => ({ ...prev, deployment_name: e.target.value }))
                    }
                    required
                  />
                </div>
                <div className="w-full">
                  <Input
                    placeholder="Endpoint"
                    value={newProvider.endpoint || ""}
                    onChange={(e) =>
                      setNewProvider(prev => ({ ...prev, endpoint: e.target.value }))
                    }
                    required
                  />
                </div>
                <div className="w-full">
                  <Input
                    placeholder="API Version"
                    value={newProvider.api_version || ""}
                    onChange={(e) =>
                      setNewProvider(prev => ({ ...prev, api_version: e.target.value }))
                    }
                    required
                  />
                </div>
              </>
            )}

            <div className="w-full">
              <Input
                placeholder="API Key"
                type="password"
                value={newProvider.api_key}
                onChange={(e) =>
                  setNewProvider(prev => ({ ...prev, api_key: e.target.value }))
                }
              />
            </div>
          </div>
          <Button
            onClick={handleAddProvider}
            disabled={
              !newProvider.model ||
              !newProvider.api_key ||
              (newProvider.provider === "AzureOpenAI" &&
                (!newProvider.deployment_name || !newProvider.endpoint || !newProvider.api_version))
            }
          >
            Add Provider
          </Button>
        </div>

        <div className="mt-2 space-y-2">
          <h3 className="mb-1 font-medium">Existing Providers</h3>
          {isLoading ? (
            <div className="p-2 text-center">
              <LoadingSpinner />
            </div>
          ) : accounts.providers.length === 0 ? (
            <div className="p-2 text-center text-muted-foreground">
              No LLM providers configured. Add a provider to get started.
            </div>
          ) : (
            <div className="space-y-0.5">
              {accounts.providers.map((provider, index) => (
                <Card key={index} className={`${accounts.default === provider.provider ? "border-2 border-primary" : ""} p-0`}>
                  <CardContent className="flex items-center justify-between p-2">
                    <div>
                      <p className="font-medium">{provider.provider}</p>
                      <p className="text-sm text-muted-foreground">{provider.model}</p>
                    </div>
                    <div className="flex gap-2">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleSetDefault(provider.provider)}
                              disabled={accounts.default === provider.provider}
                            >
                              {accounts.default === provider.provider ?
                                <Star className="w-4 h-4 text-yellow-500" /> :
                                <StarOff className="w-4 h-4" />
                              }
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            {accounts.default === provider.provider ? "Default Provider" : "Set as Default"}
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteProvider(provider.provider)}
                              disabled={accounts.providers.length === 1}
                              className="transition-colors hover:text-red-500"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            {accounts.providers.length === 1 ?
                              "Cannot delete the only provider" :
                              "Delete Provider"
                            }
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </DialogContent>
  )
}