FROM node:22-alpine AS builder

WORKDIR /frontend

ARG API_URL
ARG WEB_URL

ENV API_URL=$API_URL
ENV WEB_URL=$WEB_URL

COPY /frontend/package*.json ./
COPY /frontend/pnpm-lock.yaml ./

RUN apk update && apk add --no-cache libc6-compat
RUN npm install --global --no-update-notifier --no-fund pnpm@9.5.0

RUN pnpm fetch

COPY /frontend .

RUN pnpm build

FROM node:22-alpine AS runner

WORKDIR /frontend

COPY --from=builder /frontend/package.json ./
COPY --from=builder /frontend/.next ./.next
COPY --from=builder /frontend/public ./public

ENV CHOKIDAR_USEPOLLING=true

EXPOSE 3002

CMD ["pnpm", "run", "start"]