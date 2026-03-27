export interface NavItem {
  label: string
  to: string
  icon?: string
  adminOnly?: boolean
}

export interface DashboardState {
  sidebarCollapsed: boolean
  activeSection: string | null
}
