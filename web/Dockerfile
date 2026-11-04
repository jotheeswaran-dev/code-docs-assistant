FROM node:24-alpine AS deps
WORKDIR /srv
COPY package.json package-lock.json ./
RUN npm ci --no-fund --no-audit

FROM node:24-alpine AS build
WORKDIR /srv
COPY --from=deps /srv/node_modules ./node_modules
COPY . .
RUN npm run build

# The standalone output holds only the files that the server needs.
FROM node:24-alpine AS run
WORKDIR /srv
ENV NODE_ENV=production
COPY --from=build /srv/public ./public
COPY --from=build /srv/.next/standalone ./
COPY --from=build /srv/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
