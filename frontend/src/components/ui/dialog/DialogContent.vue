<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import {
  DialogClose,
  DialogContent,
  DialogOverlay,
  DialogPortal,
  type DialogContentEmits,
  type DialogContentProps,
  useForwardPropsEmits,
} from "reka-ui"
import { X } from "lucide-vue-next"
import { cn } from "@/lib/utils"

const props = defineProps<
  DialogContentProps & {
    class?: HTMLAttributes["class"]
  }
>()
const emits = defineEmits<DialogContentEmits>()
const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <DialogPortal>
    <DialogOverlay
      data-slot="dialog-overlay"
      class="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/50"
    />
    <DialogContent
      v-bind="forwarded"
      data-slot="dialog-content"
      :class="
        cn(
          'bg-card text-card-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 fixed top-1/2 left-1/2 z-50 grid w-full max-w-lg -translate-x-1/2 -translate-y-1/2 gap-4 rounded-xl border p-6 shadow-lg duration-200',
          props.class,
        )
      "
    >
      <slot />
      <DialogClose
        class="ring-offset-background focus:ring-ring data-[state=open]:bg-accent data-[state=open]:text-muted-foreground absolute top-4 right-4 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-none disabled:pointer-events-none"
      >
        <X class="h-4 w-4" />
        <span class="sr-only">Close</span>
      </DialogClose>
    </DialogContent>
  </DialogPortal>
</template>
