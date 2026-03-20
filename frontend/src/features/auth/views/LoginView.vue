<script setup lang="ts">
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import LoginForm from '../components/LoginForm.vue'
</script>

<template>
  <div class="flex min-h-svh items-center justify-center bg-background p-4">
    <Card class="w-full max-w-sm">
      <CardHeader class="text-center">
        <CardTitle class="text-2xl">Sign in</CardTitle>
        <CardDescription>Enter your credentials to access your account</CardDescription>
      </CardHeader>
      <CardContent>
        <LoginForm />
      </CardContent>
    </Card>
  </div>
</template>
