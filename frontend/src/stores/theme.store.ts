import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

export type ThemeName =
  | 'precision-dark'
  | 'developer-verdant'
  | 'warm-neutral'
  | 'vibrant-saas'
  | 'tactile-craft'

export interface ThemeOption {
  id: ThemeName
  label: string
  description: string
  accentColor: string
  bgPreview: string
}

export const THEMES: ThemeOption[] = [
  {
    id: 'precision-dark',
    label: 'Precision',
    description: 'Linear/Raycast',
    accentColor: '#5B5BD6',
    bgPreview: '#F0F3F6',
  },
  {
    id: 'developer-verdant',
    label: 'Verdant',
    description: 'Supabase/Terminal',
    accentColor: '#3ECF8E',
    bgPreview: '#EFF3F0',
  },
  {
    id: 'warm-neutral',
    label: 'Warm',
    description: 'Notion/Cal.com',
    accentColor: '#2F7AEA',
    bgPreview: '#F2F0EB',
  },
  {
    id: 'vibrant-saas',
    label: 'Vibrant',
    description: 'Stripe',
    accentColor: '#635BFF',
    bgPreview: '#FFFFFF',
  },
  {
    id: 'tactile-craft',
    label: 'Tactile',
    description: 'Craft/Editorial',
    accentColor: '#C04030',
    bgPreview: '#FAF8F4',
  },
]

const STORAGE_KEY_THEME = 'app-theme'
const STORAGE_KEY_DARK = 'app-dark-mode'

function getStoredTheme(): ThemeName {
  const stored = localStorage.getItem(STORAGE_KEY_THEME)
  if (stored && THEMES.some((t) => t.id === stored)) {
    return stored as ThemeName
  }
  return 'precision-dark'
}

function getStoredDarkMode(): boolean {
  const stored = localStorage.getItem(STORAGE_KEY_DARK)
  if (stored !== null) {
    return stored === 'true'
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export const useThemeStore = defineStore('theme', () => {
  const themeName = ref<ThemeName>(getStoredTheme())
  const isDark = ref(getStoredDarkMode())

  const currentTheme = computed(() => THEMES.find((t) => t.id === themeName.value)!)

  function setTheme(name: ThemeName): void {
    themeName.value = name
  }

  function toggleDarkMode(): void {
    isDark.value = !isDark.value
  }

  function applyTheme(): void {
    const root = document.documentElement
    root.setAttribute('data-theme', themeName.value)

    if (isDark.value) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  watch(
    [themeName, isDark],
    () => {
      localStorage.setItem(STORAGE_KEY_THEME, themeName.value)
      localStorage.setItem(STORAGE_KEY_DARK, String(isDark.value))
      applyTheme()
    },
    { immediate: true },
  )

  return {
    themeName,
    isDark,
    currentTheme,
    setTheme,
    toggleDarkMode,
  }
})
