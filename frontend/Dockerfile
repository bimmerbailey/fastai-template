# ---- Stage 0: Development ----
FROM oven/bun:1.2-alpine AS dev

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

EXPOSE 5173

CMD ["bun", "run", "dev", "--host"]

# ---- Stage 1: Install dependencies ----
FROM oven/bun:1.2-alpine AS deps

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# ---- Stage 2: Build ----
FROM oven/bun:1.2-alpine AS build

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Pass build-time env vars as needed:
# ARG VITE_API_URL
# ENV VITE_API_URL=$VITE_API_URL

RUN bun run build-only

# ---- Stage 3: Production ----
FROM nginx:stable-alpine AS production

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

RUN mkdir -p /var/cache/nginx /var/run/nginx \
    && chown -R nginx:nginx /var/cache/nginx /var/run/nginx /usr/share/nginx/html

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
