"use client"

import * as React from "react"
import { Link, useLocation } from "react-router-dom"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface SecondaryItem {
  title: string
  url: string
  icon: LucideIcon
}

interface NavSecondaryProps {
  items: SecondaryItem[]
  className?: string
}

export function NavSecondary({ items, className }: NavSecondaryProps) {
  const location = useLocation()

  return (
    <SidebarMenu className={cn("mt-auto", className)}>
      {items.map((item) => {
        const Icon = item.icon
        const isActive = location.pathname === item.url ||
          (item.url !== "#" && location.pathname.startsWith(item.url))

        return (
          <SidebarMenuItem key={item.title}>
            <SidebarMenuButton asChild tooltip={item.title} isActive={isActive}>
              <Link to={item.url}>
                <Icon />
                <span>{item.title}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        )
      })}
    </SidebarMenu>
  )
}
