FROM node:18-alpine

WORKDIR /app

COPY payment-api/package*.json ./
RUN npm ci --only=production

COPY payment-api/ ./

EXPOSE 3001

CMD ["node", "server.js"]
