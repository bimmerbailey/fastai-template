<script setup lang="ts">
import { ref } from "vue"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useLogin } from "../composables/useLogin"

const email = ref("")
const password = ref("")

const { isLoading, error, login } = useLogin()

async function onSubmit(): Promise<void> {
  await login({ username: email.value, password: password.value })
}
</script>

<template>
  <form class="grid gap-4" @submit.prevent="onSubmit">
    <div
      v-if="error"
      class="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
    >
      {{ error }}
    </div>

    <div class="grid gap-2">
      <Label for="email">Email</Label>
      <Input
        id="email"
        v-model="email"
        type="email"
        placeholder="you@example.com"
        required
        autocomplete="email"
      />
    </div>

    <div class="grid gap-2">
      <Label for="password">Password</Label>
      <Input
        id="password"
        v-model="password"
        type="password"
        required
        autocomplete="current-password"
      />
    </div>

    <Button type="submit" class="w-full" :disabled="isLoading">
      {{ isLoading ? "Signing in..." : "Sign in" }}
    </Button>
  </form>
</template>
