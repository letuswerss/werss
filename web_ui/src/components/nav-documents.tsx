"use client"

import * as React from "react"
import { Link, useLocation } from "react-router-dom"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { type LucideIcon } from "lucide-react"

interface DocumentItem {
  name: string
  url: string
  icon: LucideIcon
}

interface NavDocumentsProps {
  items: DocumentItem[]
  title?: string
}

export function NavDocuments({ items, title = "文档" }: NavDocumentsProps) {
  const location = useLocation()

  return (
    <SidebarGroup>
      <SidebarGroupLabel>{title}</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.url ||
            (item.url !== "#" && location.pathname.startsWith(item.url))

          return (
            <SidebarMenuItem key={item.name}>
              <SidebarMenuButton asChild tooltip={item.name} isActive={isActive}>
                <Link to={item.url}>
                  <Icon />
                  <span>{item.name}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          )
        })}
      </SidebarMenu>
    </SidebarGroup>
  )
}
