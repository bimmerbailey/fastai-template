<script setup lang="ts">
import { onMounted } from "vue"
import { useRouter } from "vue-router"
import { useItems } from "../composables/useItems"
import ItemsTable from "../components/ItemsTable.vue"

const router = useRouter()
const { items, isLoading, error, fetchItems } = useItems()

onMounted(() => fetchItems())

function handleSelect(id: string): void {
  router.push({ name: "item-detail", params: { itemId: id } })
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold text-foreground">Items</h1>
    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <p v-if="isLoading" class="text-sm text-muted-foreground">Loading...</p>
    <ItemsTable v-else :items="items" @select="handleSelect" />
  </div>
</template>
