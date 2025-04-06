import React from "react"
import { NavLink } from "react-router-dom"
import { AiFillHome } from "react-icons/ai"
import { TiMessages } from "react-icons/ti"
import { FaMessage } from "react-icons/fa6"
import { FaUser, FaUsers, FaUserPlus } from "react-icons/fa"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const items = [
  {
    title: "Home",
    url: "/",
    icon: AiFillHome,
  },
  {
    title: "Participants",
    url: "/participants",
    icon: FaUser,
  },
  {
    title: "Create Participant",
    url: "/participants/create",
    icon: FaUserPlus,
  },
  {
    title: "Groups",
    url: "/groups",
    icon: FaUsers,
  },
  {
    title: "Meetings",
    url: "/meetings",
    icon: TiMessages,
  },
  {
    title: "New Meeting",
    url: "/meetings/new",
    icon: FaMessage,
  },
]

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url}>
                      <item.icon className="w-4 h-4" />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}

export default AppSidebar
