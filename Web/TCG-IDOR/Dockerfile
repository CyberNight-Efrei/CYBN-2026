FROM node:22-bookworm-slim AS client-build
WORKDIR /build/client
COPY src/client/package*.json ./
RUN npm ci --no-audit --no-fund
COPY src/client/ ./
RUN npm run build

FROM node:22-bookworm-slim AS server-build
WORKDIR /build/server
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ && rm -rf /var/lib/apt/lists/*
COPY src/server/package*.json ./
RUN npm ci --omit=dev --no-audit --no-fund \
    && npm rebuild sqlite3 --build-from-source --nodedir=/usr/local

FROM node:22-bookworm-slim
ENV NODE_ENV=production PORT=8080 DB_PATH=/data/cybermon.sqlite STATIC_DIR=/app/public
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends fontconfig fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY --from=server-build /build/server/node_modules ./node_modules
COPY --chown=node:node src/server/package*.json ./
COPY --chown=node:node src/server/src ./src
COPY --chown=node:node src/server/data ./data
COPY --chown=node:node --from=client-build /build/client/dist ./public
RUN mkdir /data /app/secret && chown node:node /data /app/secret
USER node
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 CMD node -e "fetch('http://127.0.0.1:8080/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "src/index.js"]
