import { ofetch } from 'ofetch'

const AUTH_TOKEN_KEY = 'auth_token'

export const api = ofetch.create({
  baseURL: '/api/v1',
  onRequest({ options }) {
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    if (token) {
      options.headers.set('Authorization', `Bearer ${token}`)
    }
  },
  onResponseError({ response }) {
    if (response.status === 401) {
      localStorage.removeItem(AUTH_TOKEN_KEY)
      window.location.href = '/#/login'
    }
  },
})
