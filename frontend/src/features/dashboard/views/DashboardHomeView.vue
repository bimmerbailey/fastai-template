<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold text-foreground">Overview</h1>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Items</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold text-foreground">—</p>
          <p class="text-sm text-muted-foreground">Total items</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Conversations</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold text-foreground">—</p>
          <p class="text-sm text-muted-foreground">Active conversations</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold text-foreground">—</p>
          <p class="text-sm text-muted-foreground">Registered users</p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
