<script setup lang="ts">
import { onMounted } from "vue"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useItems } from "../composables/useItems"

const props = defineProps<{
  itemId: string
}>()

const { selectedItem, isLoading, error, fetchItem } = useItems()

onMounted(() => fetchItem(props.itemId))
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold text-foreground">Item Detail</h1>
    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <p v-if="isLoading" class="text-sm text-muted-foreground">Loading...</p>

    <Card v-else-if="selectedItem">
      <CardHeader>
        <CardTitle>{{ selectedItem.name }}</CardTitle>
      </CardHeader>
      <CardContent class="space-y-2">
        <p><span class="font-medium">Description:</span> {{ selectedItem.description ?? "—" }}</p>
        <p><span class="font-medium">Quantity:</span> {{ selectedItem.quantity }}</p>
        <p>
          <span class="font-medium">Cost:</span>
          {{ selectedItem.cost != null ? `$${selectedItem.cost}` : "—" }}
        </p>
      </CardContent>
    </Card>
  </div>
</template>
