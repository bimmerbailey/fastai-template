import { ofetch } from "ofetch"
import type { FetchOptions } from "ofetch"

const AUTH_TOKEN_KEY = "auth_token"

const sharedInterceptors: Pick<FetchOptions, "onRequest" | "onResponseError"> = {
  onRequest({ options }) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    if (token) {
      options.headers.set("Authorization", `Bearer ${token}`)
    }
  },
  onResponseError({ response, request }) {
    const url = typeof request === "string" ? request : request.url
    // TODO: Not sure if I like this
    const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/register")

    if (response.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem(AUTH_TOKEN_KEY)
      // TODO: Use vue-router?
      window.location.href = "/#/login"
    }
  },
}

export const api = ofetch.create({
  baseURL: "/api/v1",
  ...sharedInterceptors,
})

export const adminApi = ofetch.create({
  baseURL: "/admin/v1",
  ...sharedInterceptors,
})
