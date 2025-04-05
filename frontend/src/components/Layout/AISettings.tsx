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
import { useState } from "react"

interface LLMProvider {
  provider: string
  deployment_name?: string
  model: string
  endpoint?: string
  api_version?: string
  api_key: string
}

interface LLMAccounts {
  default: string
  providers: LLMProvider[]
}

export function AISettings() {
  const [accounts, setAccounts] = useState<LLMAccounts>({
    default: "AzureOpenAI",
    providers: [
      {
        provider: "AzureOpenAI",
        deployment_name: "gpt-4o",
        model: "gpt-4o",
        endpoint: "https://nithin-test.openai.azure.com",
        api_version: "2024-10-21",
        api_key: "3952377f72bd49b88f86cc984178b2d4",
      },
    ],
  })

  const [newProvider, setNewProvider] = useState<LLMProvider>({
    provider: "AzureOpenAI",
    model: "",
    api_key: "",
  })

  const handleAddProvider = () => {
    setAccounts(prev => ({
      ...prev,
      providers: [...prev.providers, newProvider],
    }))
    setNewProvider({
      provider: "AzureOpenAI",
      model: "",
      api_key: "",
    })
  }

  const handleSetDefault = (provider: string) => {
    setAccounts(prev => ({
      ...prev,
      default: provider,
    }))
  }

  return (
    <DialogContent className="sm:max-w-[550px]">
      <DialogHeader>
        <DialogTitle>AI Provider Settings</DialogTitle>
      </DialogHeader>

      <div className="grid gap-4 py-4">
        <div className="space-y-4">
          <h3 className="font-medium">Add New Provider</h3>
          <div className="grid grid-cols-2 gap-2">
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
                <SelectItem value="AzureOpenAI">Azure OpenAI</SelectItem>
                <SelectItem value="Grok">Grok</SelectItem>
              </SelectContent>
            </Select>

            <Input
              placeholder="Model name"
              value={newProvider.model}
              onChange={(e) =>
                setNewProvider(prev => ({ ...prev, model: e.target.value }))
              }
            />

            {newProvider.provider === "AzureOpenAI" && (
              <>
                <Input
                  placeholder="Deployment name"
                  value={newProvider.deployment_name}
                  onChange={(e) =>
                    setNewProvider(prev => ({ ...prev, deployment_name: e.target.value }))
                  }
                />
                <Input
                  placeholder="Endpoint"
                  value={newProvider.endpoint}
                  onChange={(e) =>
                    setNewProvider(prev => ({ ...prev, endpoint: e.target.value }))
                  }
                />
                <Input
                  placeholder="API Version"
                  value={newProvider.api_version}
                  onChange={(e) =>
                    setNewProvider(prev => ({ ...prev, api_version: e.target.value }))
                  }
                />
              </>
            )}

            <Input
              placeholder="API Key"
              type="password"
              value={newProvider.api_key}
              onChange={(e) =>
                setNewProvider(prev => ({ ...prev, api_key: e.target.value }))
              }
            />
          </div>
          <Button onClick={handleAddProvider}>Add Provider</Button>
        </div>

        <div className="space-y-4">
          <h3 className="font-medium">Existing Providers</h3>
          <div className="space-y-2">
            {accounts.providers.map((provider, index) => (
              <Card key={index}>
                <CardContent className="flex items-center justify-between pt-6">
                  <div>
                    <p className="font-medium">{provider.provider}</p>
                    <p className="text-sm text-muted-foreground">Model: {provider.model}</p>
                  </div>
                  <Button
                    variant={accounts.default === provider.provider ? "default" : "outline"}
                    onClick={() => handleSetDefault(provider.provider)}
                  >
                    {accounts.default === provider.provider ? "Default" : "Set as Default"}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </DialogContent>
  )
}