<script setup lang="ts">
import type { ItemRead } from "../types/item.types"

defineProps<{
  items: ItemRead[]
}>()

defineEmits<{
  select: [id: string]
  delete: [id: string]
}>()
</script>

<template>
  <div class="rounded-md border border-border">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-border bg-muted/50">
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Description</th>
          <th class="px-4 py-3 text-right font-medium text-muted-foreground">Quantity</th>
          <th class="px-4 py-3 text-right font-medium text-muted-foreground">Cost</th>
          <th class="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in items"
          :key="item.id"
          class="border-b border-border last:border-0 hover:bg-muted/30 cursor-pointer"
          @click="$emit('select', item.id)"
        >
          <td class="px-4 py-3 font-medium text-foreground">{{ item.name }}</td>
          <td class="px-4 py-3 text-muted-foreground">{{ item.description ?? "—" }}</td>
          <td class="px-4 py-3 text-right text-foreground">{{ item.quantity }}</td>
          <td class="px-4 py-3 text-right text-foreground">
            {{ item.cost != null ? `$${item.cost}` : "—" }}
          </td>
          <td class="px-4 py-3 text-right">
            <!-- TODO: action buttons -->
          </td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">No items found</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
