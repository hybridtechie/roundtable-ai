import React, { useState, useEffect } from "react"
import { Card, CardTitle, CardContent, CardDescription, CardHeader } from "@/components/ui/card"
import { getUserDetailInfo } from "@/lib/api"
import { UserDetailInfo } from "@/types/types"
import { Users, MessageSquare, Layers, Server, UserCircle } from "lucide-react"

const Home: React.FC = () => {
  const [userDetail, setUserDetail] = useState<UserDetailInfo | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getUserDetailInfo()
      .then((res) => {
        setUserDetail(res.data)
        setError(null)
      })
      .catch((err) => {
        console.error(err)
        setError("Failed to load user details")
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  const dashboardCards = [
    {
      title: "Participants",
      value: userDetail?.participants_count || 0,
      description: "Total AI participants created",
      icon: <Users className="w-8 h-8 text-blue-500" />,
      color: "bg-blue-50",
    },
    {
      title: "Groups",
      value: userDetail?.groups_count || 0,
      description: "Participant groups created",
      icon: <UserCircle className="w-8 h-8 text-green-500" />,
      color: "bg-green-50",
    },
    {
      title: "Meetings",
      value: userDetail?.meetings_count || 0,
      description: "Total meetings organized",
      icon: <Layers className="w-8 h-8 text-purple-500" />,
      color: "bg-purple-50",
    },
    {
      title: "Chat Sessions",
      value: userDetail?.chat_sessions_count || 0,
      description: "Active chat sessions",
      icon: <MessageSquare className="w-8 h-8 text-orange-500" />,
      color: "bg-orange-50",
    },
    {
      title: "LLM Providers",
      value: userDetail?.llm_providers_count || 0,
      description: "Connected AI providers",
      icon: <Server className="w-8 h-8 text-indigo-500" />,
      color: "bg-indigo-50",
    },
  ]

  return (
    <div className="p-6">
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-t-2 border-b-2 border-blue-500 rounded-full animate-spin"></div>
        </div>
      ) : error ? (
        <div className="p-4 text-center text-red-500">{error}</div>
      ) : (
        <>
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Welcome, {userDetail?.display_name || "User"}</h1>
            <p className="mt-1 text-gray-500">{userDetail?.email}</p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-5">
            {dashboardCards.map((card, index) => (
              <Card key={index} className="overflow-hidden">
                <CardHeader className={`${card.color} p-4`}>
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
    </div>
  )
}

export default Home
