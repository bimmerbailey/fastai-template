import { useDashboardStore } from "../stores/dashboard.store"
import { storeToRefs } from "pinia"

export function useDashboard() {
  const store = useDashboardStore()
  const { sidebarCollapsed } = storeToRefs(store)

  return {
    sidebarCollapsed,
    toggleSidebar: store.toggleSidebar,
  }
}
