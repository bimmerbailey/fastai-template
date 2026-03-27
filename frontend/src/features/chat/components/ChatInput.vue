<script setup lang="ts">
import { ref } from "vue"
import { Send } from "lucide-vue-next"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [message: string]
}>()

const message = ref("")

function handleSend(): void {
  const text = message.value.trim()
  if (!text) return
  emit("send", text)
  message.value = ""
}
</script>

<template>
  <form class="flex items-center gap-2 border-t border-border p-4" @submit.prevent="handleSend">
    <Input
      v-model="message"
      placeholder="Type a message..."
      :disabled="disabled"
      class="flex-1"
      @keydown.enter.prevent="handleSend"
    />
    <Button type="submit" size="icon-sm" :disabled="disabled || !message.trim()">
      <Send class="h-4 w-4" />
    </Button>
  </form>
</template>
