<script setup lang="ts">
import { reactive } from "vue"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { ItemCreate } from "../types/item.types"

const props = defineProps<{
  initialValues?: Partial<ItemCreate>
  isLoading?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: ItemCreate]
  cancel: []
}>()

const form = reactive<ItemCreate>({
  name: props.initialValues?.name ?? "",
  cost: props.initialValues?.cost,
  description: props.initialValues?.description,
  quantity: props.initialValues?.quantity ?? 0,
})

function handleSubmit(): void {
  emit("submit", { ...form })
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="handleSubmit">
    <div class="space-y-2">
      <Label for="name">Name</Label>
      <Input id="name" v-model="form.name" placeholder="Item name" required />
    </div>

    <div class="space-y-2">
      <Label for="description">Description</Label>
      <Input id="description" v-model="form.description" placeholder="Description" />
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-2">
        <Label for="quantity">Quantity</Label>
        <Input id="quantity" v-model.number="form.quantity" type="number" min="0" />
      </div>
      <div class="space-y-2">
        <Label for="cost">Cost</Label>
        <Input id="cost" v-model.number="form.cost" type="number" step="0.01" min="0" />
      </div>
    </div>

    <div class="flex justify-end gap-2">
      <Button type="button" variant="outline" @click="$emit('cancel')">Cancel</Button>
      <Button type="submit" :disabled="isLoading">
        {{ isLoading ? "Saving..." : "Save" }}
      </Button>
    </div>
  </form>
</template>
