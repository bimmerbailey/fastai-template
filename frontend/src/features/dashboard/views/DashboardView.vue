<script setup lang="ts">
import DashboardSidebar from "../components/DashboardSidebar.vue"
import DashboardHeader from "../components/DashboardHeader.vue"
</script>

<template>
  <div class="flex h-svh bg-background">
    <DashboardSidebar />
    <div class="flex flex-1 flex-col overflow-hidden">
      <DashboardHeader />
      <main class="flex-1 overflow-y-auto p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>
