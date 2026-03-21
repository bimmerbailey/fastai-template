<script setup lang="ts">
import { Sun, Moon } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { useThemeStore, THEMES, type ThemeName } from '@/stores/theme.store'

const themeStore = useThemeStore()

function selectTheme(id: ThemeName): void {
  themeStore.setTheme(id)
}
</script>

<template>
  <div class="flex items-center gap-1.5">
    <div class="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
      <button
        v-for="theme in THEMES"
        :key="theme.id"
        :title="`${theme.label} — ${theme.description}`"
        class="group relative flex h-7 w-7 items-center justify-center rounded-md transition-all hover:scale-110"
        :class="[
          themeStore.themeName === theme.id
            ? 'ring-2 ring-ring ring-offset-1 ring-offset-background'
            : 'hover:bg-muted',
        ]"
        @click="selectTheme(theme.id)"
      >
        <span
          class="block h-4 w-4 rounded-full border border-foreground/10"
          :style="{
            background: `linear-gradient(135deg, ${theme.bgPreview} 50%, ${theme.accentColor} 50%)`,
          }"
        />
      </button>
    </div>

    <Button
      variant="ghost"
      size="icon-sm"
      :title="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      @click="themeStore.toggleDarkMode()"
    >
      <Sun v-if="themeStore.isDark" class="h-4 w-4" />
      <Moon v-else class="h-4 w-4" />
    </Button>
  </div>
</template>
